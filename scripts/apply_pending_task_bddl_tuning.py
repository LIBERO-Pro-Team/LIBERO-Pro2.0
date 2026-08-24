"""Tune only review-ledger tasks supported by existing BDDL runtime fields."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from apply_pending_task_bddl_defaults import (
    MANIFEST,
    REVIEW,
    ROOT,
    defaults,
    manifest_paths,
    normalize_case_params,
    sync_hashes,
)


TARGET_CASES = {
    "S15",
    "S16",
    "S17",
    "S18",
    "S20",
    "D07",
    "D12",
    "D13",
    "D14",
    "D16",
    "D19",
    "D21",
}

SKIPPED_REASONS: dict[tuple[str, int, str], str] = {
    ("libero_10", 4, "D12"): "success label requires evaluator/report changes",
    ("libero_10", 4, "D13"): "success label requires evaluator/report changes",
    ("libero_10", 4, "D21"): "success label requires evaluator/report changes",
    ("libero_spatial", 9, "D12"): "success label requires evaluator/report changes",
    ("libero_spatial", 7, "D13"): "success label requires evaluator/report changes",
    ("libero_spatial", 8, "D16"): "success label requires evaluator/report changes",
    ("libero_spatial", 2, "D13"): (
        "reported penetration needs policy-rollout safety work before increasing delay"
    ),
    ("libero_10", 0, "D19"): "missing grasp/trigger needs shared trigger changes",
    ("libero_10", 1, "D19"): "success label requires evaluator/report changes",
    ("libero_10", 8, "D19"): "missing grasp/trigger needs shared trigger changes",
    ("libero_goal", 0, "D19"): "feedback requires shared trajectory/event logging",
    ("libero_goal", 3, "D19"): "feedback requires shared trajectory/event logging",
    ("libero_goal", 8, "D19"): "place-phase timing needs shared trigger changes",
    ("libero_spatial", 3, "D19"): "missing grasp/trigger needs shared trigger changes",
    ("libero_spatial", 6, "D19"): "missing grasp/trigger needs shared trigger changes",
}

COMMON_TUNING: dict[str, dict[str, tuple[str, ...]]] = {
    "S15": {
        "camera_offset_xyz": ("0.100", "-0.100", "0.070"),
        "camera_rotation_rpy": ("0.0", "0.0", "0.0"),
    },
    "S16": {
        "fov_scale": ("1.35",),
        "image_shift_xy": ("0.10", "-0.10"),
        "crop_ratio": ("0.04",),
        "distortion_strength": ("0.04",),
    },
    "S17": {
        "joint_offset_rad": (
            "0.090",
            "-0.090",
            "0.090",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
        ),
    },
    "S18": {
        "eef_offset_xyz": ("0.012", "-0.008", "0.006"),
        "joint_zero_offset_rad": ("0.012", "-0.010", "0.010"),
        "grasp_center_offset_xyz": ("0.004", "-0.003", "0.002"),
    },
    "S20": {"delay_steps": ("7",)},
    "D07": {
        "camera_offset_xyz": ("0.100", "-0.100", "0.070"),
        "camera_rotation_rpy": ("0.015", "-0.010", "0.025"),
        "event_duration_steps": ("24",),
    },
    "D12": {"delay_steps": ("8",), "event_duration_steps": ("36",)},
    "D13": {
        "arm_delay_steps": ("6",),
        "gripper_delay_steps": ("2",),
        "event_duration_steps": ("36",),
    },
    "D14": {
        "drop_count": ("2",),
        "repeat_count": ("2",),
        "event_duration_steps": ("4",),
    },
    "D16": {
        "takeover_action": ("0.18", "-0.08"),
        "takeover_duration_steps": ("12",),
    },
    "D19": {
        "misplace_offset_xy": ("0.055", "0.035"),
        "misplace_height_m": ("0.012",),
        "event_duration_steps": ("24",),
    },
    "D21": {
        "value": ("Continue_with_the_same_goal:_{instruction}",),
        "event_duration_steps": ("24",),
    },
}

D19_SAFETY_REDUCTIONS = {
    ("libero_10", 6),
    ("libero_goal", 4),
    ("libero_goal", 5),
    ("libero_object", 4),
    ("libero_object", 7),
    ("libero_spatial", 1),
    ("libero_spatial", 8),
    ("libero_spatial", 9),
}


def group_end(text: str, start: int) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError(f"Unclosed BDDL group at offset {start}")


def case_block(text: str, case_id: str) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing perturbation case {case_id}")
    return text[match.start() : group_end(text, match.start())]


def apply_params(
    text: str, case_id: str, values: dict[str, tuple[str, ...]]
) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing perturbation case {case_id}")
    end = group_end(text, match.start())
    block = text[match.start() : end]
    params_match = re.search(r"\(\s*:params\b", block)
    if not params_match:
        raise ValueError(f"Case {case_id} has no :params group")
    params_start = params_match.start()
    params_end = group_end(block, params_start)
    params = block[params_start:params_end]
    for key, atoms in values.items():
        field = f"(:{key} {' '.join(atoms)})"
        field_match = re.search(rf"\(\s*:{re.escape(key)}\b[^)]*\)", params)
        if field_match:
            params = params[: field_match.start()] + field + params[field_match.end() :]
        else:
            insertion = params.rfind(")")
            params = params[:insertion].rstrip() + f"\n          {field}\n        " + params[insertion:]
    block = block[:params_start] + params + block[params_end:]
    updated = text[: match.start()] + block + text[end:]
    return normalize_case_params(updated, case_id)


def review_rows() -> list[dict[str, str]]:
    with REVIEW.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle, delimiter="\t")
            if str(row["扰动"]).upper() in TARGET_CASES
        ]


def task_tuning(suite: str, task_id: int, case_id: str) -> dict[str, tuple[str, ...]]:
    values = dict(COMMON_TUNING[case_id])
    if (suite, task_id, case_id) == ("libero_10", 5, "S17"):
        values["joint_offset_rad"] = (
            "-0.090",
            "0.090",
            "-0.090",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
        )
    elif (suite, task_id, case_id) == ("libero_object", 1, "D16"):
        values["takeover_action"] = ("-0.18", "0.08")
    elif case_id == "D07" and (suite, task_id) in {
        ("libero_spatial", 3),
        ("libero_spatial", 6),
    }:
        values["trigger_distance_m"] = ("0.22",)
    elif (suite, task_id, case_id) == ("libero_object", 0, "D19"):
        values["misplace_offset_xy"] = ("0.120", "0.0")
        values["misplace_height_m"] = ("0.0",)
    elif (suite, task_id, case_id) == ("libero_10", 5, "D19"):
        values["misplace_offset_xy"] = ("0.120", "0.050")
        values["misplace_height_m"] = ("0.0",)
    elif (suite, task_id, case_id) == ("libero_10", 7, "D19"):
        values["misplace_offset_xy"] = ("0.120", "0.0")
        values["misplace_height_m"] = ("0.0",)
    elif (suite, task_id, case_id) == ("libero_object", 5, "D19"):
        values["misplace_offset_xy"] = ("0.120", "0.0")
        values["misplace_height_m"] = ("0.0",)
    elif (suite, task_id, case_id) == ("libero_object", 6, "D19"):
        values["misplace_offset_xy"] = ("0.100", "0.040")
        values["misplace_height_m"] = ("0.0",)
    elif (suite, task_id, case_id) == ("libero_goal", 4, "D19"):
        values["misplace_offset_xy"] = ("0.120", "0.0")
        values["misplace_height_m"] = ("0.0",)
    elif (suite, task_id, case_id) == ("libero_goal", 5, "D19"):
        values["misplace_offset_xy"] = ("0.100", "0.0")
        values["misplace_height_m"] = ("0.0",)
    elif (suite, task_id, case_id) == ("libero_object", 4, "D19"):
        values["misplace_offset_xy"] = ("0.080", "0.0")
        values["misplace_height_m"] = ("0.0",)
    elif (suite, task_id, case_id) == ("libero_10", 9, "D19"):
        values["misplace_offset_xy"] = ("0.120", "0.000")
        values["misplace_height_m"] = ("-0.050",)
    elif (suite, task_id, case_id) == ("libero_object", 7, "D19"):
        values["misplace_offset_xy"] = ("0.120", "0.000")
        values["misplace_height_m"] = ("-0.040",)
    elif case_id == "D19" and (suite, task_id) in D19_SAFETY_REDUCTIONS:
        values["misplace_offset_xy"] = ("0.035", "0.020")
        values["misplace_height_m"] = ("0.005",)
    elif (suite, task_id, case_id) == ("libero_goal", 2, "D19"):
        values["misplace_offset_xy"] = ("0.070", "0.040")
        values["misplace_height_m"] = ("0.008",)
    return values


def build_tuning_plan(
    rows: list[dict[str, str]],
) -> tuple[
    dict[tuple[str, int, str], dict[str, tuple[str, ...]]],
    dict[tuple[str, int, str], str],
]:
    plan: dict[tuple[str, int, str], dict[str, tuple[str, ...]]] = {}
    skipped: dict[tuple[str, int, str], str] = {}
    for row in rows:
        key = (str(row["suite"]), int(row["task_id"]), str(row["扰动"]).upper())
        if key in SKIPPED_REASONS:
            skipped[key] = SKIPPED_REASONS[key]
            continue
        plan[key] = task_tuning(*key)
    return plan, skipped


def param_atoms(text: str, case_id: str, field: str) -> tuple[str, ...]:
    block = case_block(text, case_id)
    match = re.search(rf"\(\s*:{re.escape(field)}\b([^)]*)\)", block)
    if not match:
        return ()
    return tuple(match.group(1).split())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    plan, skipped = build_tuning_plan(review_rows())
    paths = manifest_paths()
    changed_paths: list[Path] = []
    changes: list[dict[str, object]] = []
    ledger_changes: list[dict[str, object]] = []
    for key, values in sorted(plan.items()):
        path = paths.get(key)
        if path is None:
            raise ValueError(f"Review key is absent from task manifest: {key}")
        original = path.read_text(encoding="utf-8")
        baseline = defaults(key[2], original)
        ledger_changes.append(
            {
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "bddl": str(path.relative_to(ROOT)).replace("\\", "/"),
                "fields": {
                    field: {
                        "old": list(baseline.get(field, ())),
                        "new": list(atoms),
                    }
                    for field, atoms in values.items()
                    if baseline.get(field, ()) != atoms
                },
            }
        )
        updated = apply_params(original, key[2], values)
        if updated == original:
            continue
        changed_paths.append(path)
        changes.append(
            {
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "bddl": str(path.relative_to(ROOT)).replace("\\", "/"),
                "fields": {
                    field: {
                        "old": list(param_atoms(original, key[2], field)),
                        "new": list(atoms),
                    }
                    for field, atoms in values.items()
                    if param_atoms(original, key[2], field) != atoms
                },
            }
        )
        if not args.check_only:
            path.write_text(updated, encoding="utf-8")

    if changed_paths and not args.check_only:
        sync_hashes(changed_paths)

    payload = {
        "feedback_keys": len(review_rows()),
        "planned_bddl_only_keys": len(plan),
        "skipped_shared_code_keys": [
            {
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "reason": reason,
            }
            for key, reason in sorted(skipped.items())
        ],
        "changed": len(changed_paths),
        "changes": ledger_changes,
        "applied_changes": changes,
    }
    if args.report is not None and not args.check_only:
        report = args.report.resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
