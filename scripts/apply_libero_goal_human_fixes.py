"""Apply only the task-case fixes approved in libero-goal.csv."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.apply_review_weak_overrides import SUITE_TASKS, group_end, update_case
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from apply_review_weak_overrides import SUITE_TASKS, group_end, update_case


ROOT = Path(__file__).resolve().parents[1]
BDDL_ROOT = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1" / "libero_goal"
MANIFEST = ROOT / "assets" / "task_manifest.json"


FIXES: dict[tuple[int, str], dict[str, Any]] = {
    (0, "D01"): {"params": {"approach_trigger_distance_m": ("0.18",), "joint_offset": ("-0.04",)}},
    (9, "D01"): {"params": {"approach_trigger_distance_m": ("0.18",), "offset_xy": ("0.10", "0.04")}},
    (0, "D03"): {"params": {"asset_id": ("prl/fuze_bottle",), "asset_scale": ("0.55",), "allow_compact_asset": ("true",), "event_duration_steps": ("30",), "obstacle_part": ("handle",), "articulation_obstacle_offset_xy": ("0.0", "-0.10")}},
    (2, "D03"): {"params": {"asset_scale": ("1.75",), "event_duration_steps": ("30",)}},
    (7, "D03"): {"params": {"asset_scale": ("0.70",), "allow_compact_asset": ("true",), "event_duration_steps": ("30",), "obstacle_part": ("button",), "articulation_obstacle_offset_xy": ("0.0", "-0.08")}},
    (8, "D03"): {"params": {"asset_scale": ("0.75",), "allow_compact_asset": ("true",)}},
    (0, "D04"): {"params": {"event_duration_steps": ("36",), "occlusion_part": ("handle",)}},
    (2, "D04"): {"params": {"event_duration_steps": ("36",)}},
    (3, "D04"): {"params": {"event_duration_steps": ("36",)}},
    (7, "D04"): {"params": {"event_duration_steps": ("36",), "occlusion_part": ("button",)}},
    (0, "D05"): {"params": {"asset_scale": ("0.70",), "obstacle_part": ("handle",), "articulation_obstacle_offset_xy": ("0.0", "-0.12")}},
    (1, "D05"): {"params": {"asset_scale": ("0.75",), "lateral_offset_m": ("0.08",)}},
    (2, "D05"): {"params": {"asset_scale": ("0.65",), "lateral_offset_m": ("0.08",)}},
    (3, "D05"): {"params": {"asset_scale": ("0.65",), "lateral_offset_m": ("0.08",)}},
    (4, "D05"): {"params": {"asset_scale": ("0.75",), "lateral_offset_m": ("0.08",)}},
    (5, "D05"): {"params": {"asset_scale": ("0.70",), "lateral_offset_m": ("0.08",)}},
    (8, "D05"): {"params": {"asset_scale": ("0.65",), "lateral_offset_m": ("0.08",)}},
    (0, "D08"): {"params": {"event_duration_steps": ("36",)}},
    (2, "D08"): {"params": {"event_duration_steps": ("36",)}},
    (0, "D09"): {"params": {"event_duration_steps": ("36",)}},
    (1, "D09"): {"params": {"event_duration_steps": ("36",)}},
    (2, "D09"): {"params": {"event_duration_steps": ("36",)}},
    (2, "D17"): {"params": {"grasp_trigger_distance_m": ("0.16",), "event_duration_steps": ("40",)}},
    (7, "D17"): {"params": {"grasp_trigger_distance_m": ("0.16",), "event_duration_steps": ("40",)}},
    (0, "D18"): {"params": {"offset_xy": ("-0.10", "0.08")}},
    (1, "D19"): {"params": {"misplacement_distance_m": ("0.14",), "require_release": ("true",)}},
    (2, "D19"): {"params": {"misplacement_distance_m": ("0.16",), "require_release": ("true",)}},
    (4, "D19"): {"params": {"misplacement_distance_m": ("0.14",), "require_release": ("true",)}},
    (5, "D19"): {"params": {"misplacement_distance_m": ("0.14",), "require_release": ("true",)}},
    (8, "D19"): {"params": {"misplacement_distance_m": ("0.14",), "require_release": ("true",)}},
    (5, "S03"): {"fields": {"targets": ("plate_1", "main_table")}, "params": {"height_delta_m": ("0.05",)}},
    (0, "S04"): {"fields": {"targets": ("wine_bottle_1", "cream_cheese_1")}, "params": {"interaction_mode": ("placement",), "layout_offset_xy": ("0.12", "0.08")}},
    (7, "S04"): {"fields": {"targets": ("flat_stove_1", "cream_cheese_1")}, "params": {"interaction_mode": ("placement",), "allow_fixture_swap": ("true",)}},
    (0, "S05"): {"params": {"asset_scale": ("0.45",), "lateral_offset_m": ("0.15",)}},
    (2, "S05"): {"params": {"asset_scale": ("0.35",), "lateral_offset_m": ("0.15",)}},
    (3, "S05"): {"params": {"asset_scale": ("0.45",), "lateral_offset_m": ("0.15",)}},
    (4, "S05"): {"params": {"asset_scale": ("0.45",), "lateral_offset_m": ("0.15",)}},
    (5, "S05"): {"params": {"asset_scale": ("0.45",), "lateral_offset_m": ("0.15",)}},
    (7, "S05"): {"params": {"asset_scale": ("0.80",), "lateral_offset_m": ("0.15",)}},
    (9, "S05"): {"params": {"asset_scale": ("0.35",), "lateral_offset_m": ("0.15",)}},
    (0, "S06"): {"fields": {"targets": ("wooden_cabinet_1",)}, "params": {"fixture_variant": ("true",), "geometry_factors": ("1.0", "1.0", "1.0")}, "declaration": ("wooden_cabinet_1 - wooden_cabinet", "wooden_cabinet_1 - yellow_cabinet")},
    (6, "S06"): {"params": {"asset_id": ("prl/gelatin_box",), "asset_scale": ("0.45",), "replacement_rotation_axis": ("x",), "replacement_rotation_rad": ("1.57079632679",)}},
    (7, "S06"): {"fields": {"targets": ("flat_stove_1",)}, "params": {"fixture_variant": ("true",), "geometry_factors": ("1.0", "1.0", "1.0")}, "declaration": ("flat_stove_1 - flat_stove", "flat_stove_1 - yellow_stove")},
    (7, "S08"): {"fields": {"targets": ("flat_stove_1",)}, "params": {"geometry_factors": ("1.15", "0.90", "1.0")}},
    (9, "S08"): {"params": {"geometry_factors": ("1.25", "1.25", "0.75")}},
    (0, "S12"): {"params": {"asset_scale": ("1.30",), "occlusion_part": ("handle",)}},
    (7, "S12"): {"params": {"asset_scale": ("1.10",), "occlusion_part": ("button",)}},
}


def case_path(task_id: int, case_id: str) -> Path:
    task_name = SUITE_TASKS["libero_goal"][task_id]
    folder = "01_static" if case_id.startswith("S") else "02_dynamic"
    return BDDL_ROOT / folder / f"{case_id}__{task_name}.bddl"


def replace_case_field(text: str, case_id: str, key: str, atoms: tuple[str, ...]) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing case {case_id}")
    end = group_end(text, match.start())
    block = text[match.start():end]
    field = f"(:{key} {' '.join(atoms)})"
    field_match = re.search(rf"\(\s*:{re.escape(key)}\b[^)]*\)", block)
    if not field_match:
        raise ValueError(f"Missing {case_id} field {key}")
    block = block[:field_match.start()] + field + block[field_match.end():]
    return text[:match.start()] + block + text[end:]


def apply_fix(text: str, case_id: str, fix: dict[str, Any]) -> str:
    declaration = fix.get("declaration")
    if declaration and declaration[1] not in text:
        if declaration[0] not in text:
            raise ValueError(f"Missing declaration {declaration[0]!r}")
        text = text.replace(declaration[0], declaration[1], 1)
    for key, atoms in fix.get("fields", {}).items():
        text = replace_case_field(text, case_id, key, atoms)
    return update_case(text, case_id, fix.get("params", {}))


def sync_manifest_hashes(paths: list[Path]) -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for path in paths:
        relative = path.relative_to(ROOT / "assets").as_posix()
        digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        pattern = (
            rf'("bddl_path"\s*:\s*"{re.escape(relative)}"\s*,\s*\n\s*'
            rf'"bddl_sha256"\s*:\s*")[0-9a-f]+(")'
        )
        manifest, count = re.subn(
            pattern,
            lambda match, value=digest: match.group(1) + value + match.group(2),
            manifest,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Missing manifest entry for {relative}")
    MANIFEST.write_text(manifest, encoding="utf-8", newline="\n")


def main() -> None:
    raise SystemExit(
        "This legacy helper is retired: its 47 task/case fixes are outside "
        "the current human-review scope. Use apply_review_weak_overrides.py "
        "for the approved 259-key ledger."
    )


if __name__ == "__main__":
    main()
