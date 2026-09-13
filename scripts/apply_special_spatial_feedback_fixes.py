"""Apply only the scene fixes identified by the special Spatial review CSV.

The older feedback fixer intentionally has a different ledger.  This script
keeps the 2026-08-28 special review scope separate so rerunning it cannot
rewrite unrelated suites, Base tasks, task 6, or unreviewed perturbations.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPECIAL_CSV = Path(r"C:\Users\racin\Desktop\human_review_results _special(1).csv")
MANIFEST = ROOT / "assets" / "task_manifest.json"
REPORT = ROOT / "outputs" / "special_spatial_feedback_fixes_20260829" / "applied.json"

FIXER_PATH = ROOT / "scripts" / "apply_feedback_task_fixes.py"
FIXER_SPEC = importlib.util.spec_from_file_location("_task_level_fixer", FIXER_PATH)
if FIXER_SPEC is None or FIXER_SPEC.loader is None:
    raise RuntimeError(f"Cannot load BDDL helper: {FIXER_PATH}")
FIXER = importlib.util.module_from_spec(FIXER_SPEC)
FIXER_SPEC.loader.exec_module(FIXER)


def _params(**values: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    return values


def _support(*names: str) -> tuple[str, ...]:
    return tuple(names)


# Only keys with a scene or perturbation defect are listed here.  Label-only
# and recording-only rows are recorded below and deliberately untouched.
FIXES: dict[tuple[str, int, str], dict[str, Any]] = {
    ("libero_spatial", 4, "D01"): {
        "params": _params(
            offset_xy=("0.055", "-0.035"),
            support_surface=("wooden_cabinet_1",),
        ),
    },
    ("libero_spatial", 7, "D05"): {
        "params": _params(
            lateral_offset_m=("0.0",),
            visual_only_asset=("false",),
            physical_collision=("true",),
        ),
    },
    ("libero_spatial", 9, "D05"): {
        "params": _params(
            lateral_offset_m=("0.0",),
            visual_only_asset=("false",),
            physical_collision=("true",),
        ),
    },
    ("libero_spatial", 0, "D06"): {
        "fields": {"disturbance_targets": ("cookies_1", "glazed_rim_porcelain_ramekin_1")},
    },
    ("libero_spatial", 2, "D06"): {
        "fields": {"disturbance_targets": ("cookies_1", "glazed_rim_porcelain_ramekin_1")},
    },
    ("libero_spatial", 4, "D06"): {
        "fields": {"disturbance_targets": ("cookies_1", "glazed_rim_porcelain_ramekin_1")},
    },
    ("libero_spatial", 9, "D06"): {
        "fields": {"disturbance_targets": ("cookies_1", "glazed_rim_porcelain_ramekin_1")},
    },
    ("libero_spatial", 0, "D08"): {
        "params": _params(event_duration_steps=("16",)),
    },
    ("libero_spatial", 0, "D12"): {
        "params": _params(delay_steps=("10",), event_duration_steps=("36",)),
    },
    ("libero_spatial", 0, "D13"): {
        "params": _params(
            arm_delay_steps=("8",),
            gripper_delay_steps=("8",),
            event_duration_steps=("36",),
        ),
    },
    ("libero_spatial", 1, "D13"): {
        "params": _params(
            arm_delay_steps=("8",),
            gripper_delay_steps=("8",),
            event_duration_steps=("36",),
        ),
    },
    ("libero_spatial", 0, "D14"): {
        "params": _params(
            drop_count=("2",), repeat_count=("8",), event_duration_steps=("8",)
        ),
    },
    ("libero_spatial", 0, "D15"): {
        "params": _params(chunk_size=("12",), stale_chunk_steps=("8",)),
    },
    ("libero_spatial", 4, "D18"): {
        "params": _params(
            offset_xy=("0.04", "-0.12"),
            minimum_clearance_m=("0.08",),
            support_surface=("wooden_cabinet_1",),
            grounded_pose=("true",),
        ),
    },
    ("libero_spatial", 0, "D20"): {
        "params": _params(trigger_action_norm=("0.025",), trigger_eef_motion_m=("0.012",)),
    },
    ("libero_spatial", 1, "D20"): {
        "params": _params(trigger_action_norm=("0.025",), trigger_eef_motion_m=("0.012",)),
    },
    ("libero_spatial", 2, "D20"): {
        "params": _params(trigger_action_norm=("0.025",), trigger_eef_motion_m=("0.012",)),
    },
    ("libero_spatial", 5, "D20"): {
        "params": _params(trigger_action_norm=("0.025",), trigger_eef_motion_m=("0.012",)),
    },
    ("libero_spatial", 8, "D20"): {
        "params": _params(trigger_action_norm=("0.025",), trigger_eef_motion_m=("0.012",)),
    },
    ("libero_spatial", 9, "D20"): {
        "params": _params(trigger_action_norm=("0.025",), trigger_eef_motion_m=("0.012",)),
    },
    ("libero_spatial", 0, "S01"): {
        "params": _params(
            offset_xy=("0.0", "-0.075"),
            grounded_pose=("true",),
            support_surface=("main_table",),
        ),
    },
    ("libero_spatial", 9, "S01"): {
        "params": _params(
            offset_xy=("0.04", "-0.03"),
            grounded_pose=("true",),
            support_surface=("wooden_cabinet_1",),
        ),
    },
    ("libero_spatial", 0, "S03"): {
        "params": _params(height_delta_m=("0.055",)),
    },
    ("libero_spatial", 8, "S03"): {
        "params": _params(
            height_delta_m=("0.090",),
            asset_id=("generated/support_riser_wide_top",),
            asset_geometry_factors=("1.0", "1.0", "3.0"),
        ),
    },
    ("libero_spatial", 1, "S04"): {
        "params": _params(
            strict_swap_xy=("true",),
            support_surface=_support("main_table"),
        ),
    },
    ("libero_spatial", 2, "S04"): {
        "params": _params(
            strict_swap_xy=("true",),
            support_surface=_support("main_table"),
        ),
    },
    ("libero_spatial", 3, "S04"): {
        "params": _params(
            strict_swap_xy=("true",),
            support_surface=_support("cookies_1", "wooden_cabinet_1"),
            swap_single_support_group=("true",),
            support_object=_support("cookies_1"),
            support_ground_surface=_support("wooden_cabinet_1"),
            second_ground_surface=_support("main_table"),
            group_minimum_clearance_m=("0.018",),
        ),
    },
    ("libero_spatial", 4, "S04"): {
        "params": _params(
            strict_swap_xy=("true",),
            support_surface=_support("wooden_cabinet_1"),
            ground_support_from_declared_surface=("true",),
        ),
    },
    ("libero_spatial", 5, "S04"): {
        "params": _params(
            strict_swap_xy=("true",),
            support_surface=_support("glazed_rim_porcelain_ramekin_1", "cookies_1"),
            preserve_swapped_support_heights=("true",),
            swap_support_groups=("true",),
            support_objects=_support("glazed_rim_porcelain_ramekin_1", "cookies_1"),
            support_ground_surface=_support("main_table"),
            group_minimum_clearance_m=("0.018",),
            group_settle_steps=("300",),
        ),
    },
    ("libero_spatial", 7, "S04"): {
        "params": _params(
            strict_swap_xy=("true",),
            support_surface=_support("flat_stove_1", "wooden_cabinet_1"),
        ),
    },
    ("libero_spatial", 9, "S04"): {
        "params": _params(
            strict_swap_xy=("true",),
            support_surface=_support("wooden_cabinet_1", "flat_stove_1"),
            ground_support_from_declared_surface=("true",),
        ),
    },
    ("libero_spatial", 0, "S05"): {
        "params": _params(
            barrier_lateral_offset_m=("0.0",),
            barrier_scale=("0.65",),
            barrier_path_fraction=("0.40",),
            barrier_geometry_factors=("1.0", "0.20", "1.0"),
            visual_only_asset=("false",),
        ),
    },
    ("libero_spatial", 8, "S05"): {
        "params": _params(
            barrier_scale=("0.65",),
            barrier_path_fraction=("0.50",),
            barrier_lateral_offset_m=("-0.12",),
            barrier_geometry_factors=("1.0", "1.0", "2.4"),
            ground_barrier_to_support=("true",),
            support_surface=("main_table",),
            visual_only_asset=("false",),
        ),
    },
    ("libero_spatial", 0, "S06"): {
        "params": _params(
            asset_scale=("0.6696",), sampler_compatible=("true",), grounded_replacement=("true",), support_surface=("main_table",),
            grounded_height_offset_m=("0.040",),
        ),
    },
    ("libero_spatial", 2, "S06"): {
        "params": _params(
            asset_scale=("0.45",), sampler_compatible=("true",), grounded_replacement=("true",), support_surface=("main_table",)
        ),
    },
    ("libero_spatial", 4, "S06"): {
        "params": _params(
            asset_scale=("0.45",), sampler_compatible=("true",), grounded_replacement=("true",), support_surface=("wooden_cabinet_1",)
        ),
    },
    ("libero_spatial", 5, "S06"): {
        "params": _params(
            asset_scale=("0.45",), sampler_compatible=("true",), grounded_replacement=("true",), grounded_height_offset_m=("0.005",), support_surface=("glazed_rim_porcelain_ramekin_1",)
        ),
    },
    ("libero_spatial", 8, "S06"): {
        "params": _params(
            asset_scale=("0.6696",), sampler_compatible=("true",), grounded_replacement=("true",), support_surface=("main_table",),
            grounded_height_offset_m=("0.080",),
        ),
    },
    ("libero_spatial", 0, "S10"): {
        "params": _params(
            asset_count=("3",),
            clutter_minimum_gap_m=("0.10",),
            clutter_offsets_xy=("0.00", "0.12", "-0.15", "-0.12", "0.00", "-0.12"),
            support_surface=("main_table",),
            visual_only_asset=("false",),
            movable_asset=("true",),
            physical_collision=("true",),
            clear_of_task_entities=("true",),
            asset_contact_margin_m=("0.006",),
        ),
    },
    ("libero_spatial", 7, "S10"): {
        "params": _params(
            clutter_minimum_gap_m=("0.065",),
            clutter_offsets_xy=("0.12", "0.10", "-0.12", "0.10"),
            support_surface=("wooden_cabinet_1",),
            visual_only_asset=("true",),
        ),
    },
    ("libero_spatial", 9, "S10"): {
        "params": _params(
            clutter_minimum_gap_m=("0.065",),
            clutter_offsets_xy=("0.06", "0.04", "-0.06", "0.04"),
            support_surface=("flat_stove_1",),
            visual_only_asset=("true",),
        ),
    },
    ("libero_spatial", 0, "S11"): {
        "params": _params(
            visual_only_asset=("true",),
        ),
    },
    ("libero_spatial", 1, "S11"): {
        "params": _params(
            asset_scale=("0.737",),
            clutter_offsets_xy=("0.10", "-0.18"),
            clutter_minimum_gap_m=("0.13",),
        ),
    },
    ("libero_spatial", 3, "S11"): {
        "params": _params(asset_scale=("0.36",)),
    },
    ("libero_spatial", 4, "S11"): {
        "params": _params(
            asset_id=("github/object_sim_bowl",),
            asset_scale=("0.6696",),
            clutter_offsets_xy=("0.10", "0.13"),
            clutter_minimum_gap_m=("0.13",),
            support_surface=("main_table",),
            visual_only_asset=("false",),
        ),
    },
    ("libero_spatial", 5, "S11"): {
        "params": _params(asset_scale=("0.36",)),
    },
    ("libero_spatial", 7, "S11"): {
        "params": _params(
            asset_scale=("0.70",),
            clutter_offsets_xy=("0.0", "0.19"),
            clutter_minimum_gap_m=("0.13",),
            support_surface=("main_table",),
            visual_only_asset=("false",),
        ),
    },
    ("libero_spatial", 8, "S11"): {
        "params": _params(asset_scale=("0.36",)),
    },
    ("libero_spatial", 9, "S11"): {
        "params": _params(
            asset_scale=("0.36",),
            clutter_offsets_xy=("0.055", "0.035"),
            support_surface=("wooden_cabinet_1",),
            visual_only_asset=("true",),
        ),
    },
    ("libero_spatial", 1, "S12"): {
        "params": _params(physical_collision=("true",)),
    },
    ("libero_spatial", 0, "S15"): {
        "params": _params(
            camera_offset_xyz=("0.100", "-0.100", "0.070"),
            camera_rotation_rpy=("0.0", "0.0", "0.0"),
        ),
    },
    ("libero_spatial", 1, "S17"): {
        "params": _params(
            joint_offset_rad=(
                "0.060",
                "-0.045",
                "0.035",
                "0.0",
                "0.0",
                "0.0",
                "0.0",
            ),
        ),
    },
    ("libero_spatial", 0, "S18"): {
        "params": _params(
            eef_offset_xyz=("0.050", "-0.040", "0.030"),
            joint_zero_offset_rad=("0.050", "-0.040", "0.030"),
            grasp_center_offset_xyz=("0.0", "0.0", "0.0"),
        ),
    },
    ("libero_spatial", 0, "S20"): {
        "params": _params(delay_steps=("7",)),
    },
}


EXCLUDED_FEEDBACK = {
    ("libero_spatial", 1, "D04"): "label_error",
    ("libero_spatial", 1, "D12"): "video_recording_or_frame_sampling_issue",
    ("libero_spatial", 1, "D19"): "label_error_and_short_recording",
    ("libero_spatial", 2, "D19"): "label_error_and_short_recording",
    ("libero_spatial", 1, "S10"): "label_error",
    ("libero_spatial", 4, "D19"): "removed_case_not_in_published_task_matrix",
}


def special_feedback_keys() -> set[tuple[str, int, str]]:
    with SPECIAL_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        keys = set()
        for row in csv.DictReader(handle):
            note = str(row.get("note", "")).strip()
            if not note:
                continue
            task_value = str(row["task_id"])
            task_id = int(task_value.rsplit("/", 1)[-1])
            keys.add((str(row["suite"]), task_id, str(row["case_id"]).upper()))
    return keys


def sync_hashes(paths: list[Path]) -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    payload = json.loads(manifest)
    by_key = {
        (str(item["suite"]), int(item["base_task_id"]), str(item["case_id"]).upper()): item
        for item in payload["tasks"]
    }
    for path in paths:
        relative = path.relative_to(ROOT / "assets").as_posix()
        key = next(
            key for key, item in by_key.items()
            if str(item["bddl_path"]) == relative
        )
        digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        by_key[key]["bddl_sha256"] = digest
    MANIFEST.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> None:
    reviewed = special_feedback_keys()
    if set(FIXES) - reviewed:
        raise RuntimeError(f"Fix mapping contains keys absent from special CSV: {sorted(set(FIXES) - reviewed)}")
    if set(EXCLUDED_FEEDBACK) - reviewed:
        raise RuntimeError(f"Excluded mapping contains keys absent from special CSV: {sorted(set(EXCLUDED_FEEDBACK) - reviewed)}")
    if reviewed != set(FIXES) | set(EXCLUDED_FEEDBACK):
        missing = reviewed - set(FIXES) - set(EXCLUDED_FEEDBACK)
        raise RuntimeError(f"Special CSV feedback is not classified: {sorted(missing)}")
    if any(task_id == 6 for _, task_id, _ in FIXES):
        raise RuntimeError("Task 6 must remain untouched")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = {
        (str(item["suite"]), int(item["base_task_id"]), str(item["case_id"]).upper()): ROOT / "assets" / str(item["bddl_path"])
        for item in manifest["tasks"]
    }
    changed: list[Path] = []
    changes: list[dict[str, Any]] = []
    for key in sorted(FIXES):
        if key not in paths:
            raise RuntimeError(f"Manifest entry missing for {key}")
        path = paths[key]
        original = path.read_text(encoding="utf-8")
        spec = FIXES[key]
        params = dict(spec.get("params", {}))
        fields = dict(spec.get("fields", {}))
        updated = FIXER.update_case(original, key[2], params=params, fields=fields)
        if updated == original:
            continue
        path.write_text(updated, encoding="utf-8", newline="\n")
        changed.append(path)
        changes.append(
            {
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "bddl": str(path.relative_to(ROOT)).replace("\\", "/"),
                "params": params,
                "fields": fields,
            }
        )
    if changed:
        sync_hashes(changed)
    payload = {
        "source": str(SPECIAL_CSV),
        "reviewed_feedback_keys": len(reviewed),
        "scene_fix_keys": len(FIXES),
        "excluded_non_parameter_keys": [
            {
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "reason": reason,
            }
            for key, reason in sorted(EXCLUDED_FEEDBACK.items())
        ],
        "changed_files": len(changed),
        "changes": changes,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
