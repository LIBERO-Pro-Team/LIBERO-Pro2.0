"""Audit task-level review feedback against published BDDL/runtime support."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"

try:
    from libero.libero.envs.perturbation_config import parse_bddl_perturbation_config
except ModuleNotFoundError:
    # Keep this read-only audit usable on a clean checkout without importing
    # LIBERO's optional simulator dependencies (for example PyYAML).
    import importlib.util

    _PARSER_PATH = ROOT / "simulator-source" / "libero" / "libero" / "envs" / "perturbation_config.py"
    _PARSER_SPEC = importlib.util.spec_from_file_location("_libero_perturbation_config", _PARSER_PATH)
    if _PARSER_SPEC is None or _PARSER_SPEC.loader is None:
        raise RuntimeError(f"Cannot load BDDL parser from {_PARSER_PATH}")
    _PARSER_MODULE = importlib.util.module_from_spec(_PARSER_SPEC)
    _PARSER_SPEC.loader.exec_module(_PARSER_MODULE)
    parse_bddl_perturbation_config = _PARSER_MODULE.parse_bddl_perturbation_config

# Fields consumed by the ec1aa8a runtime retained in the current baseline.
# Case-scoped entries override the generic dynamic timing/trigger fields.
GENERIC_FIELDS = {
    "event_duration_steps",
    "grasp_distance_m",
    "interaction_mode",
    "recovery_retreat_m",
    "trigger_distance_m",
    "trigger_lift_m",
    "trigger_move_m",
    "trigger_state_change_m",
    "trigger",
}
CASE_FIELDS: dict[str, set[str]] = {
    "S15": {"camera_offset_xyz", "camera_rotation_rpy"},
    "S16": {"fov_scale", "image_shift_xy", "crop_ratio", "distortion_strength"},
    "S17": {"joint_offset_rad"},
    "S18": {"eef_offset_xyz", "joint_zero_offset_rad", "grasp_center_offset_xyz"},
    "S20": {"delay_steps"},
    "D07": {"camera_offset_xyz", "camera_rotation_rpy"},
    "D12": {"delay_steps"},
    "D13": {"arm_delay_steps", "gripper_delay_steps"},
    "D14": {"drop_count", "repeat_count"},
    "D16": {"takeover_action", "takeover_duration_steps"},
    "D19": {"misplace_offset_xy", "misplace_height_m"},
    "D21": {"value"},
    "D01": {"offset_xy"},
    "D02": {"offset_xy"},
    "D06": {"offset_xy"},
    "D18": {"offset_xy"},
    "D15": {"chunk_size", "stale_chunk_steps"},
    "D18": {"offset_xy"},
    "D20": {
        "joint_delta_rad",
        "min_eef_displacement_m",
        "min_workspace_clearance_m",
        "penetration_tolerance_m",
        "trigger_action_norm",
        "trigger_eef_motion_m",
    },
    "S06": {"asset_id", "asset_scale"},
    "S11": {"asset_id", "asset_scale"},
    "S21": {"value"},
    "S22": {"material_id"},
}

VERIFICATION_PREFIXES = (
    "constraints.",
    "runtime ",
    "static_event_log",
    "asset_injected",
    "timestamp_log",
    "action_log",
    "input_log",
    "calibration_log",
    "success_label",
    "evaluator_reason",
)


def _manifest_entries() -> dict[tuple[str, int, str], dict[str, Any]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        (str(item["suite"]), int(item["base_task_id"]), str(item["case_id"])): item
        for item in payload["tasks"]
    }


def _active_case(config: dict[str, Any], case_id: str) -> dict[str, Any]:
    entries = config.get("perturbations", [])
    if not isinstance(entries, list):
        return {}
    for item in entries:
        if isinstance(item, list) and item and str(item[0]).upper() == case_id.upper():
            fields: dict[str, Any] = {}
            for field in item[1:]:
                if not isinstance(field, dict):
                    continue
                fields.update(field)
            return fields
    return {}


def _required_fields(raw: str) -> list[str]:
    fields = []
    for value in raw.replace("；", ";").split(";"):
        value = value.strip()
        if not value:
            continue
        if value.startswith("params."):
            fields.append(value[len("params.") :])
        elif value.startswith("constraints.") or value.startswith("runtime "):
            fields.append(value)
        else:
            fields.append(value)
    return fields


def audit(source: Path) -> list[dict[str, Any]]:
    manifest = _manifest_entries()
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    audited = []
    for row in rows:
        suite = str(row["suite"])
        task_id = int(row["task_id"])
        case_id = str(row["扰动"]).upper()
        entry = manifest[(suite, task_id, case_id)]
        bddl = ROOT / "assets" / str(entry["bddl_path"])
        config = parse_bddl_perturbation_config(bddl)
        active = _active_case(config, case_id)
        params = active.get("params", {}) if isinstance(active, dict) else {}
        params = params if isinstance(params, dict) else {}
        required = _required_fields(str(row.get("需要修改字段", "")))
        consumed = GENERIC_FIELDS | CASE_FIELDS.get(case_id, set())
        supported = sorted(field for field in required if field in consumed)
        verification_only = sorted(
            field
            for field in required
            if field.startswith(VERIFICATION_PREFIXES)
        )
        unsupported = sorted(
            field
            for field in required
            if field not in consumed
            and field not in verification_only
            and field not in {"targets", "references", "parts", "constraints"}
        )
        audited.append(
            {
                "suite": suite,
                "task_id": task_id,
                "case_id": case_id,
                "problem_type": row.get("原问题类型", ""),
                "problem": row.get("人审具体问题", ""),
                "bddl": str(bddl.relative_to(ROOT)).replace("\\", "/"),
                "targets": active.get("targets", []) if isinstance(active, dict) else [],
                "references": active.get("references", []) if isinstance(active, dict) else [],
                "params": params,
                "required_fields": required,
                "runtime_supported_fields": supported,
                "runtime_unsupported_fields": unsupported,
                "verification_only_fields": verification_only,
                "requires_runtime_support": bool(unsupported),
                "bddl_only_possible": not unsupported,
            }
        )
    return audited


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = audit(args.source)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    summary = {
        "rows": len(rows),
        "bddl_only_possible": sum(row["bddl_only_possible"] for row in rows),
        "requires_runtime_support": sum(row["requires_runtime_support"] for row in rows),
        "unsupported_fields": Counter(
            field
            for row in rows
            for field in row["runtime_unsupported_fields"]
        ).most_common(),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
