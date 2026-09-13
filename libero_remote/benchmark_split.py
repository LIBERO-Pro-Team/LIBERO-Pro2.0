"""Versioned suite-aware train/test split for LIBERO-Pro benchmarks."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Set, Tuple

TaskKey = Tuple[str, int]
SPLIT_SCHEMA_VERSION = "libero-pro-benchmark-split-v1"


@dataclass(frozen=True)
class BenchmarkSplit:
    """Validated split whose unit of assignment is (suite, base task ID)."""

    version: str
    sha256: str
    path: Path
    assignments: Dict[str, Dict[str, Tuple[int, ...]]]

    @classmethod
    def load(cls, value: Path) -> "BenchmarkSplit":
        path = Path(value).expanduser().resolve()
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        if payload.get("schema_version") != SPLIT_SCHEMA_VERSION:
            raise ValueError("Unsupported benchmark split schema")
        version = str(payload.get("split_version", "")).strip()
        if not version:
            raise ValueError("Benchmark split_version must not be empty")
        splits = payload.get("splits")
        if not isinstance(splits, dict) or set(splits) != {"train", "test"}:
            raise ValueError("Benchmark split must define exactly train and test")
        assignments = {
            name: _normalize_assignment(assignment, name)
            for name, assignment in splits.items()
        }
        train = _task_keys(assignments["train"])
        test = _task_keys(assignments["test"])
        overlap = sorted(train.intersection(test))
        if overlap:
            raise ValueError(f"Train/test task overlap: {overlap}")
        return cls(
            version=version,
            sha256=hashlib.sha256(raw).hexdigest(),
            path=path,
            assignments=assignments,
        )

    def filter_catalog(self, catalog: Mapping[str, Any], name: str) -> Dict[str, Any]:
        """Keep every perturbation case under each selected suite/task pair."""

        if name not in self.assignments:
            raise ValueError(f"Unknown benchmark split {name!r}")
        selected = _task_keys(self.assignments[name])
        raw_tasks = catalog.get("tasks")
        if not isinstance(raw_tasks, list):
            raise ValueError("Task catalog does not contain a published tasks list")
        available = {
            (str(item["suite"]), int(item["task_id"])) for item in raw_tasks
        }
        missing = sorted(selected.difference(available))
        if missing:
            raise ValueError(
                f"Benchmark split references tasks absent from the catalog: {missing}"
            )
        filtered = dict(catalog)
        filtered["tasks"] = [
            dict(item)
            for item in raw_tasks
            if (str(item["suite"]), int(item["task_id"])) in selected
        ]
        filtered["task_count"] = len(filtered["tasks"])
        filtered["benchmark_split"] = {
            "name": name,
            "version": self.version,
            "sha256": self.sha256,
            "id_semantics": ["suite", "base_task_id"],
            "assignment_scope": "all_cases_for_suite_and_base_task",
            "suite_tasks": {
                suite: list(task_ids)
                for suite, task_ids in self.assignments[name].items()
            },
        }
        return filtered


def _normalize_assignment(value: Any, label: str) -> Dict[str, Tuple[int, ...]]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} must be a non-empty suite mapping")
    result: Dict[str, Tuple[int, ...]] = {}
    for raw_suite, raw_ids in value.items():
        suite = str(raw_suite).strip()
        if not suite or not isinstance(raw_ids, list) or not raw_ids:
            raise ValueError(f"{label} contains an invalid suite task list")
        task_ids = tuple(int(task_id) for task_id in raw_ids)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError(f"{label}.{suite} contains duplicate task IDs")
        result[suite] = task_ids
    return result


def _task_keys(assignment: Mapping[str, Tuple[int, ...]]) -> Set[TaskKey]:
    return {
        (suite, task_id)
        for suite, task_ids in assignment.items()
        for task_id in task_ids
    }
