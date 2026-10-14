"""Versioned source of truth for deployable LIBERO perturbation tasks."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

# OpenPI examples/libero/main.py limits, excluding its 10 reset wait steps.
PI0_MAX_STEPS_BY_SUITE: Mapping[str, int] = {
    "libero_spatial": 220,
    "libero_object": 280,
    "libero_goal": 300,
    "libero_10": 520,
}
LIBERO_EVAL_DEFAULT_MAX_STEPS = 600


def _canonical_text_bytes(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def normalize_case_id(value: str) -> str:
    normalized = value.strip().upper()
    return "BASE" if normalized == "BASE" else normalized


@dataclass(frozen=True)
class TaskManifest:
    path: Path
    version: str
    sha256: str
    entries: Tuple[Dict[str, Any], ...]
    _by_key: Mapping[Tuple[str, int, str], Dict[str, Any]]

    @classmethod
    def load(cls, value: str) -> "TaskManifest":
        path = Path(value).expanduser().resolve()
        raw = path.read_bytes()
        canonical_raw = _canonical_text_bytes(raw)
        payload = json.loads(canonical_raw.decode("utf-8"))
        version = str(payload.get("manifest_version", "")).strip()
        declared_count = int(payload.get("task_count", -1))
        tasks = payload.get("tasks")
        if not version or not isinstance(tasks, list) or declared_count != len(tasks):
            raise ValueError("Task manifest version or task_count is invalid")

        entries: List[Dict[str, Any]] = []
        by_key: Dict[Tuple[str, int, str], Dict[str, Any]] = {}
        for raw_entry in tasks:
            if not isinstance(raw_entry, dict):
                raise ValueError("Every task manifest entry must be an object")
            entry = dict(raw_entry)
            suite = str(entry["suite"])
            task_id = int(entry["base_task_id"])
            case_id = normalize_case_id(str(entry["case_id"]))
            entry["case_id"] = case_id
            key = (suite, task_id, case_id)
            if key in by_key:
                raise ValueError(f"Duplicate task manifest key: {key}")
            entry["max_steps"] = _validate_max_steps(
                entry.get("max_steps"), f"Task manifest entry {key}"
            )
            cls._validate_bddl(path.parent, entry)
            entries.append(entry)
            by_key[key] = entry

        return cls(
            path=path,
            version=version,
            sha256=hashlib.sha256(canonical_raw).hexdigest(),
            entries=tuple(entries),
            _by_key=by_key,
        )

    @staticmethod
    def _validate_bddl(root: Path, entry: Dict[str, Any]) -> None:
        relative = Path(str(entry["bddl_path"]))
        path = (root / relative).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError(f"Manifest BDDL path escapes its root: {relative}") from exc
        if not path.is_file():
            raise FileNotFoundError(f"Manifest BDDL does not exist: {path}")
        actual = hashlib.sha256(_canonical_text_bytes(path.read_bytes())).hexdigest()
        if actual != str(entry["bddl_sha256"]):
            raise ValueError(f"Manifest BDDL hash mismatch: {path}")

    def require(self, suite: str, task_id: int, case_id: str) -> Dict[str, Any]:
        key = (suite, int(task_id), normalize_case_id(case_id))
        entry = self._by_key.get(key)
        if entry is None:
            raise ValueError(f"Task is not published by manifest {self.version}: {key}")
        return dict(entry)

    def resolve_bddl(self, suite: str, task_id: int, case_id: str) -> Path:
        entry = self.require(suite, task_id, case_id)
        return (self.path.parent / str(entry["bddl_path"])).resolve()

    def catalog(self) -> Dict[str, Any]:
        cases = sorted(
            {str(entry["case_id"]) for entry in self.entries},
            key=lambda value: (value != "BASE", value),
        )
        return {
            "task_manifest_version": self.version,
            "task_manifest_sha256": self.sha256,
            "task_count": len(self.entries),
            "suites": sorted({str(entry["suite"]) for entry in self.entries}),
            "variants": ["base" if case == "BASE" else case for case in cases],
            "tasks": [
                {
                    "suite": entry["suite"],
                    "task_id": entry["base_task_id"],
                    "case_id": entry["case_id"],
                    "case_kind": entry["case_kind"],
                    "max_steps": entry["max_steps"],
                    "bddl_sha256": entry["bddl_sha256"],
                }
                for entry in self.entries
            ],
        }


def default_max_steps_for_suite(suite: str) -> int:
    return PI0_MAX_STEPS_BY_SUITE.get(suite, LIBERO_EVAL_DEFAULT_MAX_STEPS)


def resolve_catalog_max_steps(
    catalog: Mapping[str, Any], suite: str, task_id: int, case_id: str = "base"
) -> int:
    tasks = catalog.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("Task catalog does not contain a published tasks list")
    normalized_case = normalize_case_id(case_id)
    for raw_task in tasks:
        if not isinstance(raw_task, Mapping):
            continue
        published_task_id = raw_task.get("task_id", raw_task.get("base_task_id"))
        try:
            normalized_task_id = int(published_task_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("Task catalog entry has an invalid task_id") from exc
        if (
            str(raw_task.get("suite", "")) == suite
            and normalized_task_id == int(task_id)
            and normalize_case_id(str(raw_task.get("case_id", "base"))) == normalized_case
        ):
            return _validate_max_steps(
                raw_task.get("max_steps"),
                f"Task catalog entry {(suite, int(task_id), normalized_case)}",
            )
    raise ValueError(
        f"Task catalog does not publish {(suite, int(task_id), normalized_case)}"
    )


def _validate_max_steps(value: Any, context: str) -> int:
    try:
        max_steps = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} has an invalid max_steps value") from exc
    if not 1 <= max_steps <= 5000:
        raise ValueError(f"{context} max_steps must be between 1 and 5000")
    return max_steps


def load_optional_task_manifest(value: Optional[str]) -> Optional[TaskManifest]:
    return TaskManifest.load(value) if value else None
