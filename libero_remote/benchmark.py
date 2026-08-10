"""Grouped, multi-seed benchmark planning on top of the existing run scheduler."""

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from libero_remote.client.run_client import RemoteRunClient
from libero_remote.runner.scheduled import AgentAdapter, run_scheduled_run

PLAN_SCHEMA_VERSION = "libero-pro-grouped-eval-plan-v1"
VALID_GROUPS = ("all", "base", "static", "dynamic")


@dataclass(frozen=True)
class BenchmarkPlan:
    """Immutable, auditable expansion of task selection and rollout parameters."""

    schema_version: str
    plan_id: str
    task_manifest_version: Optional[str]
    task_manifest_sha256: Optional[str]
    selection: Dict[str, Any]
    selected_task_count: int
    rollout_count: int
    episodes: Tuple[Dict[str, Any], ...]

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["episodes"] = [dict(item) for item in self.episodes]
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BenchmarkPlan":
        schema_version = str(payload.get("schema_version", ""))
        if schema_version != PLAN_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported benchmark plan schema {schema_version!r}; "
                f"expected {PLAN_SCHEMA_VERSION!r}"
            )
        episodes = tuple(dict(item) for item in payload.get("episodes", []))
        return cls(
            schema_version=schema_version,
            plan_id=str(payload["plan_id"]),
            task_manifest_version=_optional_string(payload.get("task_manifest_version")),
            task_manifest_sha256=_optional_string(payload.get("task_manifest_sha256")),
            selection=dict(payload.get("selection", {})),
            selected_task_count=int(payload.get("selected_task_count", 0)),
            rollout_count=int(payload.get("rollout_count", len(episodes))),
            episodes=episodes,
        )


def build_benchmark_plan(
    catalog: Mapping[str, Any],
    *,
    group: str = "all",
    suites: Optional[Sequence[str]] = None,
    cases: Optional[Sequence[str]] = None,
    seeds: Sequence[int] = (142,),
    init_state_ids: Sequence[int] = (0,),
    matrix: bool = False,
    control_mode: str = "relative",
    camera_names: Sequence[str] = ("agentview", "robot0_eye_in_hand"),
    camera_height: int = 256,
    camera_width: int = 256,
    max_steps: int = 500,
    observation_schema_version: str = "libero_standard_v1",
) -> BenchmarkPlan:
    """Expand a published task catalog into deterministic episode specifications."""

    normalized_group = group.strip().lower()
    if normalized_group not in VALID_GROUPS:
        raise ValueError(f"group must be one of {VALID_GROUPS}, got {group!r}")
    if control_mode not in {"relative", "absolute"}:
        raise ValueError("control_mode must be 'relative' or 'absolute'")
    if camera_height < 1 or camera_width < 1 or max_steps < 1:
        raise ValueError("camera dimensions and max_steps must be positive")

    normalized_suites = _normalize_unique_strings(suites, "suites")
    normalized_cases = _normalize_cases(cases)
    normalized_seeds = _normalize_unique_ints(seeds, "seeds", minimum=0)
    normalized_init_states = _normalize_unique_ints(
        init_state_ids, "init_state_ids", minimum=0
    )
    seed_state_pairs = _expand_seed_init_states(
        normalized_seeds, normalized_init_states, matrix
    )

    raw_tasks = catalog.get("tasks")
    if not isinstance(raw_tasks, list):
        raise ValueError("Task catalog does not contain a published tasks list")
    selected: List[Dict[str, Any]] = []
    for raw_task in raw_tasks:
        if not isinstance(raw_task, Mapping):
            raise ValueError("Every task catalog entry must be an object")
        task = _normalize_catalog_task(raw_task)
        if normalized_group != "all" and task["case_kind"] != normalized_group:
            continue
        if normalized_suites and task["suite"] not in normalized_suites:
            continue
        if normalized_cases and task["case_id"] not in normalized_cases:
            continue
        selected.append(task)
    if not selected:
        raise ValueError("No published tasks match the requested group, suite, and case filters")

    selected.sort(key=_task_sort_key)
    cameras = _normalize_unique_strings(camera_names, "camera_names")
    if not cameras:
        raise ValueError("camera_names must contain at least one camera")
    episodes: List[Dict[str, Any]] = []
    for task in selected:
        for seed, init_state_id in seed_state_pairs:
            episodes.append(
                {
                    "protocol_version": str(catalog.get("protocol_version", "1.0")),
                    "suite": task["suite"],
                    "task_id": task["task_id"],
                    "init_state_id": init_state_id,
                    "seed": seed,
                    "variant": "base" if task["case_id"] == "BASE" else task["case_id"],
                    "control_mode": control_mode,
                    "camera_names": list(cameras),
                    "camera_height": camera_height,
                    "camera_width": camera_width,
                    "max_steps": max_steps,
                    "observation_schema_version": observation_schema_version,
                }
            )

    selection = {
        "group": normalized_group,
        "suites": list(normalized_suites),
        "cases": list(normalized_cases),
        "seeds": list(normalized_seeds),
        "init_state_ids": list(normalized_init_states),
        "matrix": matrix,
        "control_mode": control_mode,
        "camera_names": list(cameras),
        "camera_height": camera_height,
        "camera_width": camera_width,
        "max_steps": max_steps,
        "observation_schema_version": observation_schema_version,
    }
    identity = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "task_manifest_version": catalog.get("task_manifest_version"),
        "task_manifest_sha256": catalog.get("task_manifest_sha256"),
        "selection": selection,
        "episodes": episodes,
    }
    plan_id = hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()
    return BenchmarkPlan(
        schema_version=PLAN_SCHEMA_VERSION,
        plan_id=plan_id,
        task_manifest_version=_optional_string(catalog.get("task_manifest_version")),
        task_manifest_sha256=_optional_string(catalog.get("task_manifest_sha256")),
        selection=selection,
        selected_task_count=len(selected),
        rollout_count=len(episodes),
        episodes=tuple(episodes),
    )


def run_grouped_benchmark(
    client: RemoteRunClient,
    plan: BenchmarkPlan,
    adapter: AgentAdapter,
    *,
    runner_id: str,
    output_dir: Path,
    run_id: Optional[str] = None,
    poll_interval_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    """Submit or resume a plan, execute its remaining leases, and export results."""

    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "plan.json", plan.to_dict())
    if run_id is None:
        if not plan.episodes:
            raise ValueError("A new grouped benchmark plan must contain at least one episode")
        submitted = client.submit_run(plan.episodes)
        run_id = str(submitted["run_id"])
        _write_json(output / "submission.json", submitted)
    else:
        _validate_existing_run(client, run_id, plan)
    run = run_scheduled_run(
        client,
        run_id=run_id,
        runner_id=runner_id,
        adapter=adapter,
        poll_interval_seconds=poll_interval_seconds,
    )
    exported = export_benchmark_results(client, run_id, output)
    exported["run"] = run
    return exported


def save_benchmark_plan(plan: BenchmarkPlan, output_dir: Path) -> Path:
    """Persist a plan before submission so large runs remain auditable."""

    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    path = output / "plan.json"
    _write_json(path, plan.to_dict())
    return path


def submit_benchmark_plan(
    client: RemoteRunClient, plan: BenchmarkPlan, output_dir: Path
) -> Dict[str, Any]:
    """Submit a previously generated plan and persist its scheduler identity."""

    if not plan.episodes:
        raise ValueError("A submitted grouped benchmark plan must contain episodes")
    output = Path(output_dir).expanduser().resolve()
    save_benchmark_plan(plan, output)
    submitted = client.submit_run(plan.episodes)
    _write_json(output / "submission.json", submitted)
    return submitted


def export_benchmark_results(
    client: RemoteRunClient, run_id: str, output_dir: Path
) -> Dict[str, Any]:
    """Export persisted scheduler state without rerunning completed episodes."""

    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    run = client.get_run(run_id)
    episode_payload = client.get_episodes(run_id)
    episodes = list(episode_payload.get("episodes", []))
    summary = summarize_benchmark_episodes(episode_payload)
    _write_json(output / "run.json", run)
    _write_json(output / "summary.json", summary)
    _write_jsonl(output / "episodes.jsonl", episodes)
    _write_episode_csv(output / "episodes.csv", episodes)
    failures = [item for item in episodes if item.get("status") == "failed"]
    _write_jsonl(output / "failures.jsonl", failures)
    return {"run": run, "episodes": episode_payload, "summary": summary}


def summarize_benchmark_episodes(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Aggregate scheduler-authoritative results by suite, variant, group, and seed."""

    episodes = payload.get("episodes", [])
    if not isinstance(episodes, list):
        raise ValueError("Episode result payload must contain an episodes list")
    return {
        "schema_version": "libero-pro-grouped-eval-summary-v1",
        "run_id": payload.get("run_id"),
        "overall": _aggregate(episodes),
        "by_suite": _group_aggregate(episodes, lambda item: str(item["spec"]["suite"])),
        "by_variant": _group_aggregate(
            episodes, lambda item: _normalize_case_id(item["spec"].get("variant", "base"))
        ),
        "by_group": _group_aggregate(
            episodes,
            lambda item: _case_kind(_normalize_case_id(item["spec"].get("variant", "base"))),
        ),
        "by_seed": _group_aggregate(episodes, lambda item: str(item["spec"]["seed"])),
    }


def _aggregate(episodes: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    completed = [item for item in episodes if item.get("status") == "completed"]
    successful = sum(
        bool(item.get("result") and item["result"].get("success")) for item in completed
    )
    step_counts = [
        int(item["result"]["step_count"])
        for item in completed
        if item.get("result") and item["result"].get("step_count") is not None
    ]
    return {
        "total": len(episodes),
        "completed": len(completed),
        "failed": sum(item.get("status") == "failed" for item in episodes),
        "cancelled": sum(item.get("status") == "cancelled" for item in episodes),
        "successful": successful,
        "success_rate": successful / len(completed) if completed else None,
        "mean_step_count": mean(step_counts) if step_counts else None,
    }


def _group_aggregate(
    episodes: Sequence[Mapping[str, Any]], key_fn: Any
) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for item in episodes:
        key = key_fn(item)
        grouped.setdefault(key, []).append(item)
    return {key: _aggregate(grouped[key]) for key in sorted(grouped)}


def _validate_existing_run(
    client: RemoteRunClient, run_id: str, plan: BenchmarkPlan
) -> None:
    existing = client.get_episodes(run_id).get("episodes", [])
    if len(existing) != len(plan.episodes):
        raise ValueError(
            f"Existing run {run_id!r} has {len(existing)} episodes, "
            f"but plan {plan.plan_id!r} has {len(plan.episodes)}"
        )
    for index, (job, expected) in enumerate(zip(existing, plan.episodes)):
        actual = job.get("spec", {})
        mismatches = {
            key: (expected_value, actual.get(key))
            for key, expected_value in expected.items()
            if actual.get(key) != expected_value
        }
        if mismatches:
            raise ValueError(
                f"Existing run {run_id!r} episode {index} does not match plan: {mismatches}"
            )


def _normalize_catalog_task(task: Mapping[str, Any]) -> Dict[str, Any]:
    case_id = _normalize_case_id(task.get("case_id", task.get("variant", "base")))
    case_kind = str(task.get("case_kind", _case_kind(case_id))).strip().lower()
    expected_kind = _case_kind(case_id)
    if case_kind != expected_kind:
        raise ValueError(
            f"Task catalog case {case_id!r} declares kind {case_kind!r}, "
            f"expected {expected_kind!r}"
        )
    suite = str(task.get("suite", "")).strip()
    if not suite:
        raise ValueError("Task catalog entry has an empty suite")
    return {
        "suite": suite,
        "task_id": int(task["task_id"]),
        "case_id": case_id,
        "case_kind": case_kind,
    }


def _normalize_case_id(value: Any) -> str:
    normalized = str(value).strip().upper()
    if normalized == "BASE":
        return "BASE"
    if len(normalized) == 3 and normalized[0] in {"S", "D"}:
        try:
            number = int(normalized[1:])
        except ValueError as exc:
            raise ValueError(f"Invalid case id {value!r}") from exc
        if 1 <= number <= 21:
            return f"{normalized[0]}{number:02d}"
    raise ValueError(f"Invalid case id {value!r}; expected base, S01-S21, or D01-D21")


def _case_kind(case_id: str) -> str:
    if case_id == "BASE":
        return "base"
    return "static" if case_id.startswith("S") else "dynamic"


def _normalize_cases(values: Optional[Sequence[str]]) -> Tuple[str, ...]:
    if not values:
        return ()
    normalized = tuple(_normalize_case_id(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("cases must not contain duplicates")
    return normalized


def _normalize_unique_strings(
    values: Optional[Sequence[str]], label: str
) -> Tuple[str, ...]:
    if values is None:
        return ()
    normalized = tuple(str(value).strip() for value in values)
    if any(not value for value in normalized):
        raise ValueError(f"{label} must not contain empty values")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} must not contain duplicates")
    return normalized


def _normalize_unique_ints(
    values: Sequence[int], label: str, minimum: int
) -> Tuple[int, ...]:
    normalized = tuple(int(value) for value in values)
    if not normalized:
        raise ValueError(f"{label} must contain at least one value")
    if any(value < minimum for value in normalized):
        raise ValueError(f"{label} values must be at least {minimum}")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} must not contain duplicates")
    return normalized


def _expand_seed_init_states(
    seeds: Tuple[int, ...], init_state_ids: Tuple[int, ...], matrix: bool
) -> Tuple[Tuple[int, int], ...]:
    if matrix:
        return tuple(product(seeds, init_state_ids))
    if len(seeds) == len(init_state_ids):
        return tuple(zip(seeds, init_state_ids))
    if len(init_state_ids) == 1:
        return tuple((seed, init_state_ids[0]) for seed in seeds)
    if len(seeds) == 1:
        return tuple((seeds[0], init_state_id) for init_state_id in init_state_ids)
    raise ValueError(
        "seeds and init_state_ids require one value, equal lengths, or --matrix"
    )


def _task_sort_key(task: Mapping[str, Any]) -> Tuple[str, int, int, str]:
    case_id = str(task["case_id"])
    group_order = 0 if case_id == "BASE" else 1 if case_id.startswith("S") else 2
    return str(task["suite"]), int(task["task_id"]), group_order, case_id


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _write_json(path: Path, value: Any) -> None:
    _atomic_write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, values: Iterable[Mapping[str, Any]]) -> None:
    lines = [json.dumps(value, sort_keys=True) for value in values]
    _atomic_write(path, "".join(f"{line}\n" for line in lines))


def _write_episode_csv(path: Path, episodes: Sequence[Mapping[str, Any]]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    fields = (
        "job_index",
        "job_id",
        "status",
        "suite",
        "task_id",
        "variant",
        "seed",
        "init_state_id",
        "attempt",
        "success",
        "step_count",
        "terminated",
        "truncated",
        "failure_class",
    )
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in episodes:
            spec = item.get("spec") or {}
            result = item.get("result") or {}
            writer.writerow(
                {
                    "job_index": item.get("job_index"),
                    "job_id": item.get("job_id"),
                    "status": item.get("status"),
                    "suite": spec.get("suite"),
                    "task_id": spec.get("task_id"),
                    "variant": spec.get("variant", "base"),
                    "seed": spec.get("seed"),
                    "init_state_id": spec.get("init_state_id"),
                    "attempt": item.get("attempt"),
                    "success": result.get("success"),
                    "step_count": result.get("step_count"),
                    "terminated": result.get("terminated"),
                    "truncated": result.get("truncated"),
                    "failure_class": result.get("failure_class"),
                }
            )
    temporary.replace(path)


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
