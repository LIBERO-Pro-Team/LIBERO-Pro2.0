"""Finalize the published dataset from the human-review requirements.

The script owns the rules explicitly marked "all tasks" across all four
suites, the task-local static fixes from the Goal review, and published-case
deletions. BASE, S21, and D21 are never edited.

All D03 tasks use task-local, distance-triggered persistent movable obstacles.
D05 always uses physical collision geometry, and D14 repeats commands for a
full eight-step window.
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
PUBLISHED_VERSION = "libero-pro2.0-1706-v1"
PUBLISHED_TASK_COUNT = 1688
SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
PUBLISHED_CASES = (
    "BASE",
    *(f"S{index:02d}" for index in range(1, 23)),
    *(f"D{index:02d}" for index in range(1, 22)),
)

SPATIAL_S04_REMOVED_TASKS = {0, 1, 2, 4, 6, 7, 8, 9}

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
    ("libero_goal", 0, "D05"),
    ("libero_goal", 0, "D17"),
    ("libero_goal", 7, "D03"),
    ("libero_goal", 7, "D05"),
    ("libero_goal", 7, "S05"),
    ("libero_goal", 3, "S05"),
    ("libero_goal", 9, "D03"),
}

GOAL_REVIEW_ROUND3_FEEDBACK_KEYS = {
    *((0, case_id) for case_id in ("D04", "D05", "D08", "D09", "D10", "D11", "D12", "D16", "D17", "S04", "S12")),
    *((1, case_id) for case_id in ("D02", "D03", "D05", "S02", "S06", "S09")),
    *((2, case_id) for case_id in ("D01", "D02", "D05", "D17", "S02", "S07", "S09")),
    *((3, case_id) for case_id in ("D02", "D05", "D16", "S05", "S07", "S09")),
    *((4, case_id) for case_id in ("D02", "D03", "D05", "S02", "S07", "S09")),
    (5, "D05"),
    *((6, case_id) for case_id in ("D03", "D05", "S03", "S06")),
    *((7, case_id) for case_id in ("D03", "D05", "S04", "S05", "S09")),
    *((8, case_id) for case_id in ("D03", "S03")),
    *((9, case_id) for case_id in ("S02", "S05", "S07", "S09")),
}

GOAL_REVIEW_ROUND3_DELETIONS = {
    (0, "D05"),
    (0, "D17"),
    (7, "D03"),
    (7, "D05"),
    (7, "S05"),
    (3, "S05"),
    (9, "D03"),
}

GOAL_REVIEW_ROUND3_PARAMS: dict[
    tuple[int, str], dict[str, tuple[str, ...]]
] = {
    **{
        (0, case_id): {
            "trigger_anchor": ("wooden_cabinet_1_middle_region",),
            "trigger_distance_m": ("0.20",),
        }
        for case_id in (
            "D01",
            "D04",
            "D06",
            "D07",
            "D08",
            "D09",
            "D10",
            "D11",
            "D12",
        )
    },
    (0, "D14"): {
        "repeat_count": ("24",),
        "event_duration_steps": ("24",),
    },
    (0, "D15"): {
        "chunk_size": ("24",),
        "stale_chunk_steps": ("24",),
        "event_duration_steps": ("24",),
    },
    (0, "D16"): {
        "event_duration_steps": ("6",),
        "takeover_action": ("0.18", "-0.08"),
        "takeover_duration_steps": ("12",),
    },
    (0, "S12"): {"occlusion_offset_xyz": ("-0.05", "0.0", "0.0")},
    (1, "D02"): {"offset_xy": ("-0.12", "0.09"), "yaw_rad": ("-0.24",)},
    (1, "D05"): {
        "barrier_path_fraction": ("0.35",),
        "lateral_offset_m": ("0.0",),
    },
    (1, "S02"): {"offset_xy": ("-0.12", "0.09"), "yaw_rad": ("-0.30",)},
    (1, "S06"): {
        "asset_id": ("github/object_sim_bowl",),
        "asset_scale": ("0.70",),
        "sampler_compatible": ("true",),
    },
    (1, "S09"): {"receiver_geometry_factors": ("0.8", "0.8", "1.0")},
    (2, "D01"): {
        "trigger_distance_m": ("0.20",),
        "offset_xy": ("0.10", "-0.08"),
        "yaw_rad": ("0.28",),
    },
    (2, "D02"): {
        "offset_xy": ("-0.12", "-0.09"),
        "yaw_rad": ("-0.24",),
        "receiver_trigger_distance_m": ("0.24",),
    },
    (2, "D05"): {"asset_scale": ("0.85",)},
    (2, "D17"): {
        "grasp_initial_tolerance_m": ("0.05",),
        "grasp_distance_m": ("0.16",),
        "contact_fallback_distance_m": ("0.08",),
        "wrapper_fallback_distance_m": ("0.16",),
    },
    (2, "S02"): {"offset_xy": ("-0.12", "-0.09"), "yaw_rad": ("-0.30",)},
    (2, "S07"): {"goal_region_scale": ("1.0", "0.64", "1.20")},
    (2, "S09"): {"receiver_geometry_factors": ("0.8", "0.8", "1.0")},
    (3, "D02"): {"offset_xy": ("-0.12", "-0.09"), "yaw_rad": ("-0.24",)},
    (3, "D05"): {"asset_scale": ("0.75",)},
    (3, "D16"): {"takeover_duration_steps": ("20",)},
    (3, "S05"): {
        "barrier_scale": ("0.60",),
        "barrier_path_fraction": ("0.30",),
        "barrier_lateral_offset_m": ("0.08",),
    },
    (3, "S07"): {
        "goal_region_scale": ("1.0", "0.64", "1.20"),
        "articulation_joint_range_scale": ("0.64",),
    },
    (3, "S09"): {
        "receiver_geometry_factors": ("0.8", "0.8", "1.0"),
        "articulation_joint_range_scale": ("0.80",),
    },
    (4, "D02"): {"offset_xy": ("-0.12", "-0.09"), "yaw_rad": ("-0.24",)},
    (4, "D05"): {"asset_scale": ("0.85",)},
    (4, "S02"): {"offset_xy": ("-0.12", "-0.09"), "yaw_rad": ("-0.30",)},
    (4, "S07"): {"goal_region_scale": ("1.0", "0.64", "1.20")},
    (4, "S09"): {"receiver_geometry_factors": ("0.8", "0.8", "1.0")},
    (5, "D05"): {"receiver_trigger_distance_m": ("0.28",)},
    (6, "D03"): {
        "receiver_trigger_distance_m": ("0.24",),
        "support_surface": ("akita_black_bowl_1",),
        "asset_offset_xyz": ("0.0", "0.0", "0.02"),
    },
    (6, "D05"): {
        "barrier_path_fraction": ("0.58",),
        "lateral_offset_m": ("-0.05",),
    },
    (6, "S03"): {"asset_geometry_factors": ("0.60", "0.60", "2.0")},
    (6, "S06"): {"asset_scale": ("0.70",)},
    (7, "S09"): {"receiver_geometry_factors": ("0.8", "0.8", "1.0")},
    (8, "D03"): {"receiver_trigger_distance_m": ("0.32",)},
    (8, "S03"): {"asset_geometry_factors": ("0.70", "0.70", "2.0")},
    (9, "S02"): {"offset_xy": ("0.0", "0.09"), "yaw_rad": ("-0.24",)},
    (9, "S05"): {
        "barrier_scale": ("1.0",),
        "barrier_path_fraction": ("0.62",),
        "barrier_lateral_offset_m": ("0.025",),
        "barrier_height_m": ("0.0",),
    },
    (9, "S07"): {"goal_region_scale": ("1.0", "0.64", "1.20")},
    (9, "S09"): {"receiver_geometry_factors": ("0.90", "0.90", "1.0")},
}

GOAL_REVIEW_ROUND3_FIELDS: dict[
    tuple[int, str], dict[str, tuple[str, ...]]
] = {
    (4, "D03"): {"references": ("plate_1",)},
    (6, "D03"): {"references": ("plate_1",)},
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
S04_GROUNDED_TASKS = {
    *(("libero_10", task_id) for task_id in (0, 1, 2, 3, 7, 9)),
    *(("libero_goal", task_id) for task_id in (0, 7)),
    *(("libero_object", task_id) for task_id in range(10)),
    *(("libero_spatial", task_id) for task_id in (0, 1, 2, 3, 4, 5, 6, 7, 9)),
}

D03_RECEIVER_ANCHORS: dict[tuple[str, int], str] = {
    **{("libero_10", task_id): "basket_1_contain_region" for task_id in (0, 1, 7)},
    ("libero_10", 2): "flat_stove_1_cook_region",
    ("libero_10", 3): "white_cabinet_1_bottom_region",
    ("libero_10", 5): "desk_caddy_1_back_contain_region",
    ("libero_10", 8): "flat_stove_1_cook_region",
    ("libero_10", 9): "microwave_1_heating_region",
    ("libero_goal", 0): "wooden_cabinet_1_middle_region",
    ("libero_goal", 1): "flat_stove_1_cook_region",
    ("libero_goal", 2): "wooden_cabinet_1_top_side",
    ("libero_goal", 3): "wooden_cabinet_1_top_region",
    ("libero_goal", 4): "wooden_cabinet_1_top_side",
    ("libero_goal", 5): "main_table_stove_front_region",
    ("libero_goal", 7): "flat_stove_1_cook_region",
    ("libero_goal", 9): "wine_rack_1_top_region",
    **{("libero_object", task_id): "basket_1_contain_region" for task_id in range(10)},
}

D03_SUPPORT_SURFACES: dict[tuple[str, int], str] = {
    **{("libero_10", task_id): "basket_1" for task_id in (0, 1, 7)},
    ("libero_10", 2): "flat_stove_1",
    ("libero_10", 3): "white_cabinet_1",
    ("libero_10", 4): "plate_1",
    ("libero_10", 5): "study_table",
    ("libero_10", 6): "plate_1",
    ("libero_10", 8): "flat_stove_1",
    ("libero_10", 9): "microwave_1",
    ("libero_goal", 0): "main_table",
    ("libero_goal", 1): "flat_stove_1",
    ("libero_goal", 2): "wooden_cabinet_1",
    ("libero_goal", 3): "wooden_cabinet_1",
    ("libero_goal", 4): "wooden_cabinet_1",
    ("libero_goal", 5): "main_table",
    ("libero_goal", 6): "main_table",
    ("libero_goal", 7): "flat_stove_1",
    ("libero_goal", 8): "plate_1",
    ("libero_goal", 9): "main_table",
    **{("libero_object", task_id): "basket_1" for task_id in range(10)},
    **{("libero_spatial", task_id): "plate_1" for task_id in range(10)},
}

D03_ASSET_OFFSETS: dict[tuple[str, int], tuple[str, str, str]] = {
    # Align the red brick mesh center, whose local origin is off-center.
    **{("libero_spatial", task_id): ("0.00835045", "0.00205392", "0.0") for task_id in range(10)},
    ("libero_10", 9): ("0.0", "-0.08", "-0.12"),
    ("libero_goal", 0): ("0.07", "0.12", "-0.16"),
    ("libero_goal", 2): ("-0.055", "0.0", "0.0"),
    ("libero_goal", 6): ("-0.03", "0.14", "0.0"),
    ("libero_goal", 9): ("0.14", "0.05", "-0.22"),
}


def d03_persistent_updates(
    suite: str, task_id: int
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    """Return the complete task-local contract for one published D03."""

    key = (str(suite), int(task_id))
    if key not in D03_SUPPORT_SURFACES:
        raise KeyError(f"Missing D03 support surface for {key}")
    trigger_distance = "0.24"
    if key == ("libero_10", 2):
        trigger_distance = "0.32"
    elif key == ("libero_10", 9) or (
        key[0] == "libero_object" and key[1] in {0, 1, 2}
    ):
        trigger_distance = "0.28"
    params: dict[str, tuple[str, ...]] = {
        "receiver_trigger_distance_m": (trigger_distance,),
        "support_surface": (D03_SUPPORT_SURFACES[key],),
        "asset_offset_xyz": D03_ASSET_OFFSETS.get(
            key, ("0.0", "0.0", "0.0")
        ),
        "staging_position_xyz": ("0.0", "0.0", "-5.0"),
    }
    anchor = D03_RECEIVER_ANCHORS.get(key)
    if anchor is not None:
        params["receiver_anchor"] = (anchor,)
    fields = {"variant": ("persistent_triggered_receiver_occupation",)}
    if key[0] == "libero_spatial":
        fields["references"] = ("none",)
        params.update(
            persistent_movable_asset=("true",),
            asset_id=("ycb/YcbFoamBrick",),
            asset_scale=("0.85",),
            asset_contact_margin_m=("0.0",),
        )
    elif key == ("libero_10", 8):
        fields["references"] = ("none",)
        params.update(
            persistent_movable_asset=("true",),
            asset_id=("prl/can",),
            asset_scale=("1.0",),
        )
    else:
        params["persistent_existing_obstacle"] = ("true",)
    return params, fields


def is_excluded(suite: str, task_id: int, case_id: str) -> bool:
    key = (str(suite), int(task_id), str(case_id).upper())
    return (
        key[2] == "D19"
        or key in GOAL_NOT_APPLICABLE
        or key == ("libero_10", 8, "S04")
        or (
            key[0] == "libero_spatial"
            and key[1] in SPATIAL_S04_REMOVED_TASKS
            and key[2] == "S04"
        )
    )


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

    if case_id in {"S10", "S11"}:
        params.update(
            clear_of_task_entities=("true",),
            movable_asset=("true",),
            physical_collision=("true",),
            visual_only_asset=("false",),
        )
        if case_id == "S10":
            params["asset_contact_margin_m"] = ("0.006",)

    if (suite, task_id, case_id) == ("libero_10", 8, "D06"):
        fields["disturbance_targets"] = ("none",)
        params.update(
            asset_id=("libero/red_coffee_mug",),
            asset_scale=("1.0",),
            asset_initial_anchor=("moka_pot_2",),
            asset_initial_offset_xy=("0.134437", "0.194625"),
            asset_initial_clearance_m=("0.10",),
            support_surface=("kitchen_table",),
            minimum_clearance_m=("0.10",),
            minimum_displacement_m=("0.10",),
            offset_xy=("0.12", "-0.09"),
        )
    elif case_id == "S04" and (suite, task_id) in S04_GROUNDED_TASKS:
        params["ground_support_from_declared_surface"] = ("true",)
        if (suite, task_id) == ("libero_10", 2):
            params.update(
                grounded_swap=("true",),
                swap_cluster_radius_m=("0.18",),
                support_surface=("kitchen_table",),
            )
        if (suite, task_id) == ("libero_spatial", 3):
            params.update(
                swap_single_support_group=("true",),
                support_object=("cookies_1",),
                support_ground_surface=("wooden_cabinet_1",),
                second_ground_surface=("main_table",),
                group_minimum_clearance_m=("0.018",),
            )
        if (suite, task_id) == ("libero_spatial", 5):
            params.update(
                preserve_swapped_support_heights=("true",),
                swap_support_groups=("true",),
                support_objects=(
                    "glazed_rim_porcelain_ramekin_1",
                    "cookies_1",
                ),
                support_ground_surface=("main_table",),
                group_minimum_clearance_m=("0.018",),
                group_settle_steps=("300",),
            )
    elif case_id == "S05":
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
        elif (suite, task_id) == ("libero_object", 9):
            params.update(
                sampler_compatible=("true",),
                grounded_replacement=("true",),
                support_surface=("floor",),
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
        d03_params, d03_fields = d03_persistent_updates(suite, task_id)
        params.update(d03_params)
        fields.update(d03_fields)
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

    if (suite, task_id, case_id) == ("libero_spatial", 9, "S11"):
        params.update(
            asset_contact_margin_m=("0.004",),
            clutter_offsets_xy=("-0.10", "0.00"),
            support_surface=("wooden_cabinet_1",),
        )

    if (suite, task_id, case_id) == ("libero_spatial", 2, "S03"):
        params.update(
            asset_id=("generated/support_riser_wide_top",),
            asset_geometry_factors=("1.0", "1.0", "2.0"),
            height_delta_m=("0.10",),
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
                targets=("wooden_cabinet_1",), references=("wooden_cabinet_1",)
            )
            params.update(
                asset_id=("libero/yellow_cabinet",),
                asset_scale=("1.0",),
                asset_count=("1",),
                asset_quat=("1.0", "0.0", "0.0", "0.0"),
                weld_internal_asset_joints=("true",),
                clutter_minimum_gap_m=("0.080",),
                clutter_offsets_xy=("-0.067791", "0.639295"),
                support_surface=("main_table",),
                clear_of_task_entities=("true",),
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
                params.update(asset_id=("github/object_sim_bowl",), asset_scale=("0.70",))
            elif task_id == 5:
                params.update(
                    asset_id=("prl/plastic_plate",),
                    asset_scale=("0.55",),
                    asset_contact_margin_m=("0.004",),
                )
            else:
                params.update(asset_id=("prl/gelatin_box",), asset_scale=("0.45",))
    elif case_id == "S12" and task_id == 0:
        params.update(asset_scale=("1.45",), occlusion_fraction=("0.58",))
    elif case_id == "S13" and task_id == 5:
        fields["targets"] = ("plate_1",)

    params.update(GOAL_REVIEW_ROUND3_PARAMS.get((task_id, case_id), {}))
    fields.update(GOAL_REVIEW_ROUND3_FIELDS.get((task_id, case_id), {}))

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
        text = _remove_named_group(text, "similar_cabinet_region")
        text = re.sub(
            r"\n\s*yellow_cabinet_2\s+-\s+yellow_cabinet\s*", "\n", text, count=1
        )
        text = re.sub(
            r"\n\s*\(On\s+yellow_cabinet_2\s+[^)]+\)\s*", "\n", text, count=1
        )
    return text


def apply_published_structural_overrides(
    text: str, suite: str, task_id: int, case_id: str
) -> str:
    if (str(suite), int(task_id), str(case_id).upper()) == (
        "libero_10",
        8,
        "D06",
    ):
        text = _remove_named_group(text, "d06_distractor_init_region")
        text = re.sub(
            r"\n\s*red_coffee_mug_1\s+-\s+red_coffee_mug\s*", "\n", text, count=1
        )
        text = re.sub(
            r"\n\s*\(On\s+red_coffee_mug_1\s+[^)]+\)\s*", "\n", text, count=1
        )
        return text
    if str(suite) == "libero_goal":
        return apply_goal_structural_overrides(text, task_id, case_id)
    return text


def _remove_params_for(suite: str, task_id: int, case_id: str) -> set[str]:
    if (
        suite == "libero_goal"
        and task_id == 0
        and case_id in {"D13", "D14", "D15", "D16", "D20"}
    ):
        return {"trigger_anchor", "trigger_distance_m"}
    if case_id == "D03":
        fields = {
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
            "persistent_existing_obstacle",
            "persistent_movable_asset",
            "staging_position_xyz",
            "support_surface",
            "visual_only_asset",
        }
        if suite == "libero_spatial":
            fields.add("asset_contact_margin_m")
        return fields
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
            "fixture_distractor",
            "fixture_distractor_targets",
            "weld_asset_joints",
        }
    return set()


def canonical_hash(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def apply(
    *,
    check_only: bool = False,
    case_filter: set[str] | None = None,
    goal_review_round3_only: bool = False,
) -> dict[str, Any]:
    selected_cases = (
        {str(case_id).upper() for case_id in case_filter}
        if case_filter
        else None
    )
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = list(manifest["tasks"])
    changed: list[Path] = []
    changes: list[dict[str, Any]] = []

    for item in entries:
        suite = str(item["suite"])
        task_id = int(item["base_task_id"])
        case_id = str(item["case_id"]).upper()
        if goal_review_round3_only and (
            suite != "libero_goal"
            or (task_id, case_id) not in GOAL_REVIEW_ROUND3_FEEDBACK_KEYS
        ):
            continue
        if selected_cases is not None and case_id not in selected_cases:
            continue
        if is_excluded(suite, task_id, case_id):
            continue
        params, fields = case_updates(suite, task_id, case_id)
        remove_params = _remove_params_for(suite, task_id, case_id)
        structural = (
            suite == "libero_goal"
            and (task_id, case_id) in {(0, "S06"), (7, "S06"), (0, "S11")}
        ) or (suite, task_id, case_id) == ("libero_10", 8, "D06")
        if not params and not fields and not structural and not remove_params:
            continue
        path = ASSETS / str(item["bddl_path"])
        original = path.read_text(encoding="utf-8")
        updated = original
        if structural:
            updated = apply_published_structural_overrides(
                updated, suite, task_id, case_id
            )
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
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(updated)

    excluded_entries = [
        item
        for item in entries
        if (
            not goal_review_round3_only
            or (
                str(item["suite"]) == "libero_goal"
                and (int(item["base_task_id"]), str(item["case_id"]).upper())
                in GOAL_REVIEW_ROUND3_DELETIONS
            )
        )
        if (
            selected_cases is None
            or str(item["case_id"]).upper() in selected_cases
        )
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
    if len(retained) != PUBLISHED_TASK_COUNT:
        raise ValueError(
            f"Expected {PUBLISHED_TASK_COUNT} retained tasks, found {len(retained)}"
        )
    if not check_only:
        for item in retained:
            path = ASSETS / str(item["bddl_path"])
            if not path.is_file():
                raise FileNotFoundError(path)
            if (
                selected_cases is not None
                and str(item["case_id"]).upper() not in selected_cases
            ):
                continue
            if goal_review_round3_only and (
                str(item["suite"]) != "libero_goal"
                or (
                    int(item["base_task_id"]),
                    str(item["case_id"]).upper(),
                )
                not in GOAL_REVIEW_ROUND3_FEEDBACK_KEYS
            ):
                continue
            item["bddl_sha256"] = canonical_hash(path)
            item["task_version"] = PUBLISHED_VERSION
        manifest.update(
            manifest_version=PUBLISHED_VERSION,
            task_count=len(retained),
            tasks=retained,
        )
        with MANIFEST.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n")

    return {
        "check_only": check_only,
        "case_filter": sorted(selected_cases) if selected_cases is not None else None,
        "goal_review_round3_only": goal_review_round3_only,
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
    parser.add_argument(
        "--goal-review-round3-only",
        action="store_true",
        help="Limit edits and hash updates to the Goal round-3 review keys.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Limit updates to one or more case IDs (for example: --case D03).",
    )
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    result = apply(
        check_only=args.check_only,
        case_filter=set(args.case) if args.case else None,
        goal_review_round3_only=args.goal_review_round3_only,
    )
    if args.report is not None and not args.check_only:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
