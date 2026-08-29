"""Finalize the published dataset from the human-review requirements.

The script owns the rules explicitly marked "all tasks" across all four
suites, the task-local static fixes from the Goal review, and published-case
deletions. BASE, S21, and D21 are never edited.

Reviewed D03 tasks use task-local receiver occupancy parameters; unreviewed
D03 tasks retain their generated baseline. D05 always uses physical collision
geometry, and D14 repeats commands for a full eight-step window.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts import build_full_perturbation_dataset as generator
except ImportError:  # Direct execution from the scripts directory.
    import build_full_perturbation_dataset as generator


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DATASET = ASSETS / "bddl" / "libero-pro2.0-1680-v1"
MANIFEST = ASSETS / "task_manifest.json"
PUBLISHED_VERSION = "libero-pro2.0-1707-v1"
SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
PUBLISHED_CASES = (
    "BASE",
    *(f"S{index:02d}" for index in range(1, 23)),
    *(f"D{index:02d}" for index in range(1, 22)),
)

GOAL_NOT_APPLICABLE = {
    ("libero_goal", 0, "D02"),
    ("libero_goal", 0, "D18"),
    ("libero_goal", 0, "S02"),
    ("libero_goal", 5, "D02"),
    ("libero_goal", 5, "D13"),
    ("libero_goal", 5, "D17"),
    ("libero_goal", 5, "D18"),
    ("libero_goal", 5, "S02"),
    ("libero_goal", 5, "S03"),
    ("libero_goal", 5, "S09"),
    ("libero_goal", 7, "D02"),
    ("libero_goal", 7, "D18"),
    ("libero_goal", 7, "S02"),
}

GLOBAL_CASES = {
    "S05",
    "S06",
    "S07",
    "S08",
    "S09",
    "S18",
    "S20",
    "D03",
    "D05",
    "D12",
    "D13",
    "D14",
    "D15",
}
GOAL_S10_TASKS = {0, 1, 3, 4, 6, 7, 8}

D03_FEEDBACK_OVERRIDES: dict[
    tuple[str, int], dict[str, tuple[str, ...]]
] = {
    ("libero_10", task_id): {
        "event_duration_steps": ("48",),
        "receiver_trigger_distance_m": (("0.28",) if task_id == 9 else ("0.24",)),
        **(
            {
                "asset_scale": ("0.80",),
                "support_surface": ("plate_1",),
            }
            if task_id == 4
            else {}
        ),
        **(
            {
                "asset_scale": ("0.80",),
                "asset_offset_xyz": ("0.0", "-0.08", "0.025"),
            }
            if task_id == 9
            else {}
        ),
    }
    for task_id in (0, 1, 2, 4, 5, 9)
}
D03_FEEDBACK_OVERRIDES[("libero_object", 0)] = {
    "event_duration_steps": ("48",),
    "receiver_trigger_distance_m": ("0.24",),
}
for _task_id in (0, 1, 8, 9):
    D03_FEEDBACK_OVERRIDES[("libero_spatial", _task_id)] = {
        "event_duration_steps": ("48",),
        "receiver_trigger_distance_m": ("0.24",),
        "asset_scale": ("0.80",),
        "support_surface": ("plate_1",),
    }
D03_FEEDBACK_OVERRIDES.update(
    {
        ("libero_goal", 0): {
            "event_duration_steps": ("72",),
            "receiver_trigger_distance_m": ("0.24",),
            "asset_id": ("generated/barrier_panel",),
            "asset_scale": ("0.55",),
            "receiver_anchor": ("wooden_cabinet_1_middle_region",),
            "asset_offset_xyz": ("0.07", "0.12", "-0.16"),
            "support_surface": ("main_table",),
        },
        ("libero_goal", 2): {
            "event_duration_steps": ("72",),
            "receiver_trigger_distance_m": ("0.24",),
            "asset_id": ("prl/plastic_plate",),
            "asset_scale": ("0.60",),
            "asset_offset_xyz": ("-0.055", "0.0", "0.025"),
            "support_surface": ("wooden_cabinet_1",),
        },
        ("libero_goal", 3): {
            "event_duration_steps": ("72",),
            "receiver_trigger_distance_m": ("0.24",),
        },
        ("libero_goal", 6): {
            "event_duration_steps": ("72",),
            "receiver_trigger_distance_m": ("0.24",),
            "asset_scale": ("0.80",),
            "asset_offset_xyz": ("0.0", "0.14", "0.025"),
            "support_surface": ("main_table",),
        },
        ("libero_goal", 9): {
            "event_duration_steps": ("72",),
            "receiver_trigger_distance_m": ("0.24",),
        },
    }
)


def is_excluded(suite: str, task_id: int, case_id: str) -> bool:
    key = (str(suite), int(task_id), str(case_id).upper())
    return key[2] == "D19" or key in GOAL_NOT_APPLICABLE


def _profile(suite: str, task_id: int) -> generator.TaskProfile:
    task_name = generator.SUITE_TASKS[suite][task_id]
    return generator.load_profile(suite, task_id, task_name)


def case_updates(
    suite: str, task_id: int, case_id: str
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    """Return BDDL parameter and case-field updates for one active case."""

    suite = str(suite)
    task_id = int(task_id)
    case_id = str(case_id).upper()
    params: dict[str, tuple[str, ...]] = {}
    fields: dict[str, tuple[str, ...]] = {}

    if case_id == "S05":
        params.update(
            barrier_scale=("0.65",),
            barrier_path_fraction=("0.35",),
            barrier_lateral_offset_m=("0.0",),
            visual_only_asset=("false",),
        )
        if (suite, task_id) == ("libero_10", 0):
            params.update(
                barrier_scale=("1.15",),
                barrier_path_fraction=("0.50",),
                barrier_lateral_offset_m=("0.04",),
            )
        elif (suite, task_id) == ("libero_object", 0):
            params.update(
                barrier_scale=("1.35",),
                barrier_path_fraction=("0.50",),
                barrier_lateral_offset_m=("-0.07",),
            )
        elif (suite, task_id) == ("libero_spatial", 0):
            params.update(
                barrier_scale=("0.65",),
                barrier_path_fraction=("0.40",),
                barrier_lateral_offset_m=("0.0",),
                barrier_geometry_factors=("1.0", "0.20", "1.0"),
            )
        elif (suite, task_id) == ("libero_spatial", 8):
            params.update(
                barrier_scale=("0.35",),
                barrier_path_fraction=("0.50",),
                barrier_lateral_offset_m=("0.100",),
            )
    elif case_id == "S06":
        profile = _profile(suite, task_id)
        params.update(
            asset_id=(profile.s06_asset,),
            asset_scale=(str(profile.s06_scale),),
        )
        if (suite, task_id) == ("libero_10", 8):
            params.update(
                asset_id=("libero/yellow_moka_pot",), asset_scale=("1.0",)
            )
        elif (suite, task_id) == ("libero_goal", 0):
            params.pop("asset_id", None)
            params.pop("asset_scale", None)
            fields["targets"] = ("wooden_cabinet_1",)
            params.update(
                fixture_variant=("true",),
                fixture_geometry_factors=("1.0", "1.0", "1.0"),
            )
        elif (suite, task_id) == ("libero_goal", 7):
            params.pop("asset_id", None)
            params.pop("asset_scale", None)
            fields["targets"] = ("flat_stove_1",)
            params.update(
                fixture_variant=("true",),
                fixture_geometry_factors=("1.0", "1.0", "1.0"),
            )
        elif (suite, task_id) == ("libero_goal", 6):
            params.update(
                asset_id=("prl/gelatin_box",),
                asset_scale=("0.45",),
                asset_quat=("0.70710678", "0.70710678", "0.0", "0.0"),
                grounded_replacement=("true",),
                support_surface=("table",),
            )
    elif case_id == "S07":
        params.update(
            geometry_factors=("1.0", "0.64", "1.20"),
            goal_region_scale=("1.0", "1.0", "1.0"),
        )
    elif case_id == "S08":
        params["geometry_factors"] = ("1.28", "1.28", "0.72")
        if (suite, task_id) == ("libero_goal", 0):
            fields["targets"] = ("wooden_cabinet_1",)
            params["geometry_factors"] = ("1.15", "0.90", "1.0")
        elif (suite, task_id) == ("libero_goal", 7):
            fields["targets"] = ("flat_stove_1",)
            params["geometry_factors"] = ("1.15", "0.90", "1.0")
    elif case_id == "S09":
        params.update(
            target_geometry_factors=("1.2", "1.2", "1.2"),
            receiver_geometry_factors=("0.8", "0.8", "0.8"),
        )
    elif case_id == "S18":
        params.update(
            eef_offset_xyz=("0.050", "-0.040", "0.030"),
            joint_zero_offset_rad=("0.050", "-0.040", "0.030"),
            grasp_center_offset_xyz=("0.0", "0.0", "0.0"),
        )
    elif case_id == "S20":
        params["delay_steps"] = ("7",)
    elif case_id == "D03":
        params.update(D03_FEEDBACK_OVERRIDES.get((suite, task_id), {}))
    elif case_id == "D05":
        params.update(
            visual_only_asset=("false",),
            physical_collision=("true",),
        )
    elif case_id == "D12":
        params["delay_steps"] = ("10",)
    elif case_id == "D13":
        params.update(
            arm_delay_steps=("8",),
            gripper_delay_steps=("8",),
        )
    elif case_id == "D14":
        params.update(
            repeat_count=("8",),
            event_duration_steps=("8",),
        )
    elif case_id == "D15":
        params.update(
            chunk_size=("12",),
            stale_chunk_steps=("8",),
        )

    if suite != "libero_goal":
        return params, fields

    if case_id == "S03" and task_id in {6, 8, 9}:
        params["height_delta_m"] = (("0.07",) if task_id == 9 else ("0.05",))
    elif case_id == "S10" and task_id in GOAL_S10_TASKS:
        params.update(
            asset_count=("3",),
            clutter_minimum_gap_m=("0.080",),
            clutter_offsets_xy=(
                "0.14",
                "-0.10",
                "0.10",
                "0.12",
                "-0.13",
                "-0.08",
            ),
            support_surface=("table",),
            visual_only_asset=("false",),
            clear_of_task_entities=("true",),
        )
    elif case_id == "S11":
        if task_id == 0:
            fields.update(
                targets=("yellow_cabinet_2",), references=("wooden_cabinet_1",)
            )
            params.update(
                fixture_distractor=("true",),
                fixture_distractor_targets=("yellow_cabinet_2",),
            )
        elif task_id in {1, 5, 6}:
            params.update(
                asset_count=("1",),
                clutter_minimum_gap_m=("0.080",),
                clutter_offsets_xy=("0.18", "0.12"),
                support_surface=("table",),
                visual_only_asset=("false",),
                clear_of_task_entities=("true",),
                asset_quat=("1.0", "0.0", "0.0", "0.0"),
            )
            if task_id == 1:
                params.update(asset_id=("prl/plastic_bowl",), asset_scale=("0.45",))
            elif task_id == 5:
                params.update(asset_id=("prl/plastic_plate",), asset_scale=("0.55",))
            else:
                params.update(asset_id=("prl/gelatin_box",), asset_scale=("0.45",))
    elif case_id == "S12" and task_id == 0:
        params.update(asset_scale=("1.45",), occlusion_fraction=("0.58",))
    elif case_id == "S13" and task_id == 5:
        fields["targets"] = ("plate_1",)

    return params, fields


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


def _replace_field(
    block: str, field: str, atoms: tuple[str, ...], *, inside_params: bool
) -> str:
    prefix = ""
    suffix = ""
    scope = block
    if inside_params:
        match = re.search(r"\(\s*:params\b", block)
        if match is None:
            raise ValueError("Case has no :params group")
        end = group_end(block, match.start())
        prefix, scope, suffix = block[: match.start()], block[match.start() : end], block[end:]
    replacement = f"(:{field} {' '.join(atoms)})"
    match = re.search(rf"\(\s*:{re.escape(field)}\b[^)]*\)", scope)
    if match is not None:
        scope = scope[: match.start()] + replacement + scope[match.end() :]
    else:
        insertion = scope.rfind(")")
        scope = scope[:insertion].rstrip() + f"\n          {replacement}\n        " + scope[insertion:]
    return prefix + scope + suffix


def _remove_param_fields(block: str, fields: set[str]) -> str:
    match = re.search(r"\(\s*:params\b", block)
    if match is None:
        return block
    end = group_end(block, match.start())
    params = block[match.start() : end]
    for field in fields:
        params = re.sub(
            rf"\n\s*\(\s*:{re.escape(field)}\b[^)]*\)", "", params
        )
    return block[: match.start()] + params + block[end:]


def update_case(
    text: str,
    case_id: str,
    params: dict[str, tuple[str, ...]],
    fields: dict[str, tuple[str, ...]],
    *,
    remove_params: set[str] | None = None,
) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if match is None:
        raise ValueError(f"Missing case {case_id}")
    end = group_end(text, match.start())
    block = text[match.start() : end]
    if remove_params:
        block = _remove_param_fields(block, remove_params)
    for field, atoms in fields.items():
        block = _replace_field(block, field, atoms, inside_params=False)
    for field, atoms in params.items():
        block = _replace_field(block, field, atoms, inside_params=True)
    return text[: match.start()] + block + text[end:]


def _insert_in_group(text: str, group_name: str, value: str) -> str:
    match = re.search(rf"\(\s*:{re.escape(group_name)}\b", text)
    if match is None:
        raise ValueError(f"Missing :{group_name} group")
    end = group_end(text, match.start())
    group = text[match.start() : end]
    insertion = group.rfind(")")
    group = group[:insertion].rstrip() + "\n" + value + "\n  " + group[insertion:]
    return text[: match.start()] + group + text[end:]


def _remove_named_group(text: str, group_name: str) -> str:
    """Remove every top-level occurrence of a named BDDL subgroup."""

    while True:
        match = re.search(rf"\(\s*{re.escape(group_name)}\b", text)
        if match is None:
            return text
        end = group_end(text, match.start())
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", end)
        if line_end < 0:
            line_end = end
        else:
            line_end += 1
        text = text[:line_start] + text[line_end:]


def apply_goal_structural_overrides(text: str, task_id: int, case_id: str) -> str:
    case_id = str(case_id).upper()
    if (task_id, case_id) == (0, "S06"):
        text = text.replace(
            "wooden_cabinet_1 - wooden_cabinet",
            "wooden_cabinet_1 - yellow_cabinet",
            1,
        )
    elif (task_id, case_id) == (7, "S06"):
        text = text.replace(
            "flat_stove_1 - flat_stove", "flat_stove_1 - yellow_stove", 1
        )
    elif (task_id, case_id) == (0, "S11"):
        # Keep the custom region inside :regions. The earlier insertion before
        # :fixtures placed it after the :regions closing parenthesis, so LIBERO
        # ignored the placement and left the distractor below the table.
        markers = (
            "yellow_cabinet_2 - yellow_cabinet",
            "(-0.06 0.39 -0.04 0.41)",
            "(0.0 0.0)",
            "(On yellow_cabinet_2 main_table_similar_cabinet_region)",
        )
        regions_match = re.search(r"\(\s*:regions\b", text)
        similar_match = re.search(r"\(\s*similar_cabinet_region\b", text)
        if regions_match is not None and similar_match is not None:
            regions_end = group_end(text, regions_match.start())
            if (
                regions_match.start() < similar_match.start() < regions_end
                and all(marker in text for marker in markers)
            ):
                return text
        text = _remove_named_group(text, "similar_cabinet_region")
        region = """      (similar_cabinet_region
          (:target main_table)
          (:ranges (
              (-0.06 0.39 -0.04 0.41)
            )
          )
          (:yaw_rotation (
              (0.0 0.0)
            )
          )
      )"""
        text = _insert_in_group(text, "regions", region)
        if "yellow_cabinet_2 - yellow_cabinet" not in text:
            text = _insert_in_group(
                text, "fixtures", "    yellow_cabinet_2 - yellow_cabinet"
            )
        init = "(On yellow_cabinet_2 main_table_similar_cabinet_region)"
        if init not in text:
            text = _insert_in_group(text, "init", f"    {init}")
    return text


def _remove_params_for(suite: str, task_id: int, case_id: str) -> set[str]:
    if case_id == "D03":
        return {
            "allow_compact_asset",
            "allow_goal_overlap",
            "articulation_obstacle_offset_xy",
            "asset_id",
            "asset_offset_xyz",
            "asset_scale",
            "event_duration_steps",
            "obstacle_part",
            "receiver_anchor",
            "receiver_trigger_distance_m",
            "support_surface",
            "visual_only_asset",
        }
    if case_id == "S06" and suite == "libero_goal" and task_id in {0, 7}:
        return {
            "asset_id",
            "asset_scale",
            "asset_quat",
            "geometry_factors",
            "grounded_replacement",
            "sampler_compatible",
            "support_surface",
        }
    if case_id == "S11" and suite == "libero_goal" and task_id == 0:
        return {
            "asset_id",
            "asset_scale",
            "asset_count",
            "asset_quat",
            "clutter_minimum_gap_m",
            "clutter_offsets_xy",
            "support_surface",
            "visual_only_asset",
        }
    return set()


def canonical_hash(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def apply(*, check_only: bool = False) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = list(manifest["tasks"])
    changed: list[Path] = []
    changes: list[dict[str, Any]] = []

    for item in entries:
        suite = str(item["suite"])
        task_id = int(item["base_task_id"])
        case_id = str(item["case_id"]).upper()
        if is_excluded(suite, task_id, case_id):
            continue
        params, fields = case_updates(suite, task_id, case_id)
        remove_params = _remove_params_for(suite, task_id, case_id)
        structural = suite == "libero_goal" and (
            (task_id, case_id) in {(0, "S06"), (7, "S06"), (0, "S11")}
        )
        if not params and not fields and not structural and not remove_params:
            continue
        path = ASSETS / str(item["bddl_path"])
        original = path.read_text(encoding="utf-8")
        updated = original
        if structural:
            updated = apply_goal_structural_overrides(updated, task_id, case_id)
        updated = update_case(
            updated,
            case_id,
            params,
            fields,
            remove_params=remove_params,
        )
        if updated == original:
            continue
        changed.append(path)
        changes.append(
            {
                "suite": suite,
                "task_id": task_id,
                "case_id": case_id,
                "bddl": str(path.relative_to(ROOT)),
                "params": params,
                "fields": fields,
            }
        )
        if not check_only:
            path.write_text(updated, encoding="utf-8", newline="\n")

    excluded_entries = [
        item
        for item in entries
        if is_excluded(item["suite"], int(item["base_task_id"]), item["case_id"])
    ]
    deleted: list[Path] = []
    for item in excluded_entries:
        path = ASSETS / str(item["bddl_path"])
        if path.is_file():
            deleted.append(path)
            if not check_only:
                path.unlink()

    retained = [item for item in entries if item not in excluded_entries]
    if len(retained) != 1707:
        raise ValueError(f"Expected 1707 retained tasks, found {len(retained)}")
    if not check_only:
        for item in retained:
            path = ASSETS / str(item["bddl_path"])
            if not path.is_file():
                raise FileNotFoundError(path)
            item["bddl_sha256"] = canonical_hash(path)
            item["task_version"] = PUBLISHED_VERSION
        manifest.update(
            manifest_version=PUBLISHED_VERSION,
            task_count=len(retained),
            tasks=retained,
        )
        MANIFEST.write_text(
            json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    return {
        "check_only": check_only,
        "changed_bddl_count": len(changed),
        "deleted_bddl_count": len(deleted),
        "retained_task_count": len(retained),
        "changed_bddls": [str(path.relative_to(ROOT)) for path in changed],
        "deleted_bddls": [str(path.relative_to(ROOT)) for path in deleted],
        "changes": changes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    result = apply(check_only=args.check_only)
    if args.report is not None and not args.check_only:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
