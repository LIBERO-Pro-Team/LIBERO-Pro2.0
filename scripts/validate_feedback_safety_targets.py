"""Run current low-cost safety probes for feedback rows with scene defects."""

from __future__ import annotations

import json
import os
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_review_weak_perturbations as weak_validator


TARGETS = (
    ("libero_10", 0, "D17"),
    ("libero_10", 0, "S06"),
    ("libero_10", 1, "S06"),
    ("libero_10", 4, "S06"),
    ("libero_10", 4, "S09"),
    ("libero_goal", 0, "D04"),
    ("libero_goal", 0, "D18"),
    ("libero_goal", 0, "S05"),
    ("libero_goal", 0, "S12"),
    ("libero_goal", 1, "D05"),
    ("libero_goal", 2, "D05"),
    ("libero_goal", 2, "S05"),
    ("libero_goal", 2, "S06"),
    ("libero_goal", 3, "D05"),
    ("libero_goal", 3, "S05"),
    ("libero_goal", 4, "D05"),
    ("libero_goal", 4, "S05"),
    ("libero_goal", 5, "S03"),
    ("libero_goal", 7, "D03"),
    ("libero_goal", 7, "S05"),
    ("libero_goal", 8, "D05"),
    ("libero_goal", 9, "S05"),
    ("libero_goal", 9, "S06"),
)

OUTPUT = ROOT / "outputs" / "feedback_safety_targets_20260824"


def _tasks() -> dict[tuple[str, int, str], dict[str, object]]:
    payload = json.loads((ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8"))
    return {
        (str(item["suite"]), int(item["base_task_id"]), str(item["case_id"]).upper()): item
        for item in payload["tasks"]
    }


def _path_check(case_id: str, events: list[dict[str, object]]) -> dict[str, object]:
    if case_id in {"D05", "S05"}:
        return {
            "applicable": False,
            "detour_event_present": None,
            "reason": "This smoke probe checks placement collisions and stability; alternate-path proof requires a trajectory probe.",
        }
    return {"applicable": False, "detour_event_present": None}


def main() -> None:
    os.environ.pop("MUJOCO_GL", None)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tasks = _tasks()
    results = []
    weak_validator.OUT = OUTPUT
    for key in TARGETS:
        print(f"[safety] {key}", flush=True)
        result = weak_validator._record(key, tasks[key])
        result["path_safety"] = _path_check(
            key[2],
            [event for event in result.get("events", []) if isinstance(event, dict)],
        )
        result["checks"] = {
            "collision_clear": not bool(result.get("collision_pairs")),
            "deep_penetration_after_settle": (
                not bool(result.get("stability_penetration"))
                if key[2] in {"D03", "D05"}
                else None
            ),
            "stable_after_settle": (
                float(result.get("stability_displacement_m", 0.0)) <= 0.05
                if key[2] in {"D03", "D05"}
                else None
            ),
            "path_not_closed_when_applicable": result["path_safety"]["detour_event_present"]
            if result["path_safety"]["applicable"]
            else None,
            "runtime_event_present": bool(result.get("events")),
        }
        source_status = result.get("status")
        failed_checks = [
            name for name, passed in result["checks"].items() if passed is False
        ]
        result["source_status"] = source_status
        result["failed_checks"] = failed_checks
        result["status"] = (
            "PASS" if source_status == "PASS" and not failed_checks else "REVIEW"
        )
        results.append(result)
        print(json.dumps({"key": key, "status": result.get("status"), "checks": result["checks"]}, ensure_ascii=False), flush=True)
    (OUTPUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1 if any(item.get("status") != "PASS" for item in results) else 0)


if __name__ == "__main__":
    main()
