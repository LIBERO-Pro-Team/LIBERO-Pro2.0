import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest
from fastapi.testclient import TestClient

from libero_remote import RemoteRunClient
from libero_remote.benchmark import (
    BenchmarkPlan,
    build_benchmark_plan,
    export_benchmark_results,
    run_grouped_benchmark,
    summarize_benchmark_episodes,
)
from libero_remote.benchmark_split import BenchmarkSplit
from libero_remote.runner import AgentContext
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings


def _catalog() -> Dict[str, Any]:
    tasks = []
    for suite, task_id in (("libero_goal", 9), ("libero_spatial", 4)):
        for case_id, case_kind in (
            ("BASE", "base"),
            ("S01", "static"),
            ("S02", "static"),
            ("D01", "dynamic"),
        ):
            tasks.append(
                {
                    "suite": suite,
                    "task_id": task_id,
                    "case_id": case_id,
                    "case_kind": case_kind,
                }
            )
    return {
        "protocol_version": "1.0",
        "task_manifest_version": "test-v1",
        "task_manifest_sha256": "manifest-hash",
        "tasks": tasks,
    }


def test_static_group_expands_catalog_tasks_and_paired_seeds() -> None:
    plan = build_benchmark_plan(
        _catalog(),
        group="static",
        suites=["libero_goal"],
        seeds=[42, 43],
        init_state_ids=[0, 1],
        control_mode="relative",
        max_steps=300,
    )

    assert plan.schema_version == "libero-pro-grouped-eval-plan-v1"
    assert plan.task_manifest_version == "test-v1"
    assert plan.selected_task_count == 2
    assert plan.rollout_count == 4
    assert [
        (episode["variant"], episode["seed"], episode["init_state_id"])
        for episode in plan.episodes
    ] == [
        ("S01", 42, 0),
        ("S01", 43, 1),
        ("S02", 42, 0),
        ("S02", 43, 1),
    ]


def test_matrix_mode_builds_seed_init_state_cartesian_product() -> None:
    plan = build_benchmark_plan(
        _catalog(),
        group="base",
        suites=["libero_spatial"],
        seeds=[7, 8],
        init_state_ids=[0, 1],
        matrix=True,
        control_mode="absolute",
    )

    assert [
        (episode["seed"], episode["init_state_id"])
        for episode in plan.episodes
    ] == [(7, 0), (7, 1), (8, 0), (8, 1)]
    assert all(episode["control_mode"] == "absolute" for episode in plan.episodes)


def test_case_filter_uses_published_catalog_instead_of_cartesian_product() -> None:
    catalog = _catalog()
    catalog["tasks"] = [
        task
        for task in catalog["tasks"]
        if not (task["suite"] == "libero_spatial" and task["case_id"] == "D01")
    ]

    plan = build_benchmark_plan(
        catalog,
        group="dynamic",
        cases=["D01"],
        seeds=[42],
        init_state_ids=[0],
    )

    assert [(item["suite"], item["variant"]) for item in plan.episodes] == [
        ("libero_goal", "D01")
    ]


def test_suite_task_split_keeps_all_cases_and_is_recorded(tmp_path: Path) -> None:
    split_path = tmp_path / "split.json"
    split_path.write_text(
        json.dumps(
            {
                "schema_version": "libero-pro-benchmark-split-v1",
                "split_version": "test-split-v1",
                "splits": {
                    "train": {"libero_goal": [9]},
                    "test": {"libero_spatial": [4]},
                },
            }
        ),
        encoding="utf-8",
    )
    filtered = BenchmarkSplit.load(split_path).filter_catalog(_catalog(), "test")
    plan = build_benchmark_plan(
        filtered,
        group="all",
        seeds=[42],
        init_state_ids=[0],
    )

    assert {(item["suite"], item["task_id"]) for item in plan.episodes} == {
        ("libero_spatial", 4)
    }
    assert {item["variant"] for item in plan.episodes} == {"base", "S01", "S02", "D01"}
    assert plan.selection["benchmark_split"]["name"] == "test"
    assert plan.selection["benchmark_split"]["suite_tasks"] == {
        "libero_spatial": [4]
    }


def test_published_split_is_complete_disjoint_and_suite_aware() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "assets" / "task_manifest.json").read_text())
    catalog = {
        "tasks": [
            {
                "suite": item["suite"],
                "task_id": item["base_task_id"],
                "case_id": item["case_id"],
                "case_kind": item["case_kind"],
            }
            for item in manifest["tasks"]
        ]
    }
    split = BenchmarkSplit.load(root / "assets" / "benchmark_split_v1.json")
    train_catalog = split.filter_catalog(catalog, "train")
    test_catalog = split.filter_catalog(catalog, "test")
    available = {(item["suite"], item["task_id"]) for item in catalog["tasks"]}
    train = {(item["suite"], item["task_id"]) for item in train_catalog["tasks"]}
    test = {(item["suite"], item["task_id"]) for item in test_catalog["tasks"]}

    assert len(train) == 32
    assert len(test) == 8
    assert train.isdisjoint(test)
    assert train.union(test) == available


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"group": "unknown"}, "group must be"),
        ({"group": "dynamic", "cases": ["S01"]}, "No published tasks"),
        (
            {"group": "base", "seeds": [1, 2], "init_state_ids": [0, 1, 2]},
            "one value, equal lengths, or --matrix",
        ),
        ({"group": "base", "seeds": [1, 1]}, "seeds must not contain duplicates"),
    ],
)
def test_invalid_plan_requests_fail_before_submission(
    kwargs: Dict[str, Any], message: str
) -> None:
    arguments = {
        "catalog": _catalog(),
        "seeds": [42],
        "init_state_ids": [0],
        **kwargs,
    }
    with pytest.raises(ValueError, match=message):
        build_benchmark_plan(**arguments)


def test_summary_groups_completed_results_and_keeps_failures_separate() -> None:
    payload = {
        "run_id": "run-test",
        "episodes": [
            {
                "status": "completed",
                "spec": {
                    "suite": "libero_goal",
                    "task_id": 9,
                    "variant": "S01",
                    "seed": 42,
                    "init_state_id": 0,
                },
                "result": {"success": True, "step_count": 100},
            },
            {
                "status": "completed",
                "spec": {
                    "suite": "libero_goal",
                    "task_id": 9,
                    "variant": "S01",
                    "seed": 43,
                    "init_state_id": 1,
                },
                "result": {"success": False, "step_count": 300},
            },
            {
                "status": "failed",
                "spec": {
                    "suite": "libero_spatial",
                    "task_id": 4,
                    "variant": "D01",
                    "seed": 42,
                    "init_state_id": 0,
                },
                "result": {"success": False, "failure_class": "WORKER_FAILURE"},
            },
        ],
    }

    summary = summarize_benchmark_episodes(payload)

    assert summary["overall"] == {
        "total": 3,
        "completed": 2,
        "failed": 1,
        "cancelled": 0,
        "successful": 1,
        "success_rate": 0.5,
        "mean_step_count": 200.0,
    }
    assert summary["by_suite"]["libero_goal"]["success_rate"] == 0.5
    assert summary["by_variant"]["S01"]["successful"] == 1
    assert summary["by_group"]["static"]["completed"] == 2
    assert summary["by_group"]["dynamic"]["failed"] == 1
    assert summary["by_seed"]["42"]["total"] == 2


class _SuccessfulAdapter:
    def __init__(self) -> None:
        self.reset_count = 0
        self.closed = False

    def reset(self, context: AgentContext) -> None:
        self.reset_count += 1
        assert context.episode_spec["variant"] in {"base", "S01"}

    def act(self, observation: Dict[str, Any]) -> np.ndarray:
        del observation
        return np.array([1.0, 0.0], dtype=np.float32)

    def close(self) -> None:
        self.closed = True


def test_grouped_benchmark_submits_runs_executes_and_exports_results(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
        )
    )
    catalog = _catalog()
    catalog["tasks"] = [
        task
        for task in catalog["tasks"]
        if task["suite"] == "libero_goal" and task["case_id"] in {"BASE", "S01"}
    ]
    plan = build_benchmark_plan(
        catalog,
        group="all",
        seeds=[42],
        init_state_ids=[0],
        camera_height=16,
        camera_width=16,
        max_steps=10,
    )
    adapter = _SuccessfulAdapter()

    with TestClient(app) as http_client:
        client = RemoteRunClient("http://testserver", http_client=http_client)
        result = run_grouped_benchmark(
            client,
            plan,
            adapter,
            runner_id="grouped-test-runner",
            output_dir=tmp_path / "output",
        )
        client.close()

    assert result["run"]["status"] == "completed"
    assert result["summary"]["overall"]["successful"] == 2
    assert adapter.reset_count == 2
    assert adapter.closed is True
    assert json.loads((tmp_path / "output" / "plan.json").read_text())["plan_id"]
    assert json.loads((tmp_path / "output" / "summary.json").read_text())[
        "overall"
    ]["success_rate"] == 1.0
    assert (tmp_path / "output" / "episodes.csv").is_file()


def test_resume_uses_existing_run_without_resubmitting(tmp_path: Path) -> None:
    class ResumeClient:
        def __init__(self) -> None:
            self.submissions = 0

        def submit_run(self, episodes: Any) -> Dict[str, Any]:
            del episodes
            self.submissions += 1
            return {"run_id": "new-run"}

        def get_run(self, run_id: str) -> Dict[str, Any]:
            return {"run_id": run_id, "status": "completed"}

        def get_episodes(self, run_id: str) -> Dict[str, Any]:
            return {"run_id": run_id, "episodes": []}

    plan = BenchmarkPlan.from_dict(
        {
            "schema_version": "libero-pro-grouped-eval-plan-v1",
            "plan_id": "plan-test",
            "task_manifest_version": "test-v1",
            "task_manifest_sha256": "hash",
            "selection": {"group": "base"},
            "selected_task_count": 0,
            "rollout_count": 0,
            "episodes": [],
        }
    )
    client = ResumeClient()

    result = run_grouped_benchmark(
        client,  # type: ignore[arg-type]
        plan,
        _SuccessfulAdapter(),
        runner_id="runner",
        output_dir=tmp_path,
        run_id="existing-run",
    )

    assert client.submissions == 0
    assert result["run"]["run_id"] == "existing-run"


def test_export_can_be_repeated_for_a_persisted_run(tmp_path: Path) -> None:
    class ExportClient:
        def get_run(self, run_id: str) -> Dict[str, Any]:
            return {"run_id": run_id, "status": "completed"}

        def get_episodes(self, run_id: str) -> Dict[str, Any]:
            return {"run_id": run_id, "episodes": []}

    exported = export_benchmark_results(
        ExportClient(),  # type: ignore[arg-type]
        "run-existing",
        tmp_path,
    )

    assert exported["summary"]["overall"]["total"] == 0
    assert (tmp_path / "episodes.jsonl").read_text(encoding="utf-8") == ""
