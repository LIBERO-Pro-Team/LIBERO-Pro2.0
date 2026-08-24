"""Apply approved weak-perturbation parameter overrides to reviewed BDDL files.

The input ledger is the source of truth for scope. A file is edited only when
its ``suite|task|case`` key occurs in ``weak_rows.json``.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BDDL_ROOT = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
LEDGER = ROOT / ".codex-workbook-audit-20260819" / "weak_rows.json"

SUITE_TASKS = {
    "libero_spatial": (
        "pick_up_the_black_bowl_between_the_plate_and_the_ramekin_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_next_to_the_ramekin_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_from_table_center_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_on_the_cookie_box_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_in_the_top_drawer_of_the_wooden_cabinet_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_on_the_ramekin_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_next_to_the_cookie_box_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_on_the_stove_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_next_to_the_plate_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_on_the_wooden_cabinet_and_place_it_on_the_plate",
    ),
    "libero_object": (
        "pick_up_the_alphabet_soup_and_place_it_in_the_basket",
        "pick_up_the_cream_cheese_and_place_it_in_the_basket",
        "pick_up_the_salad_dressing_and_place_it_in_the_basket",
        "pick_up_the_bbq_sauce_and_place_it_in_the_basket",
        "pick_up_the_ketchup_and_place_it_in_the_basket",
        "pick_up_the_tomato_sauce_and_place_it_in_the_basket",
        "pick_up_the_butter_and_place_it_in_the_basket",
        "pick_up_the_milk_and_place_it_in_the_basket",
        "pick_up_the_chocolate_pudding_and_place_it_in_the_basket",
        "pick_up_the_orange_juice_and_place_it_in_the_basket",
    ),
    "libero_goal": (
        "open_the_middle_drawer_of_the_cabinet",
        "put_the_bowl_on_the_stove",
        "put_the_wine_bottle_on_top_of_the_cabinet",
        "open_the_top_drawer_and_put_the_bowl_inside",
        "put_the_bowl_on_top_of_the_cabinet",
        "push_the_plate_to_the_front_of_the_stove",
        "put_the_cream_cheese_in_the_bowl",
        "turn_on_the_stove",
        "put_the_bowl_on_the_plate",
        "put_the_wine_bottle_on_the_rack",
    ),
    "libero_10": (
        "LIVING_ROOM_SCENE2_put_both_the_alphabet_soup_and_the_tomato_sauce_in_the_basket",
        "LIVING_ROOM_SCENE2_put_both_the_cream_cheese_box_and_the_butter_in_the_basket",
        "KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it",
        "KITCHEN_SCENE4_put_the_black_bowl_in_the_bottom_drawer_of_the_cabinet_and_close_it",
        "LIVING_ROOM_SCENE5_put_the_white_mug_on_the_left_plate_and_put_the_yellow_and_white_mug_on_the_right_plate",
        "STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy",
        "LIVING_ROOM_SCENE6_put_the_white_mug_on_the_plate_and_put_the_chocolate_pudding_to_the_right_of_the_plate",
        "LIVING_ROOM_SCENE1_put_both_the_alphabet_soup_and_the_cream_cheese_box_in_the_basket",
        "KITCHEN_SCENE8_put_both_moka_pots_on_the_stove",
        "KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it",
    ),
}


def overrides(
    suite: str, task_id: int, case_id: str
) -> dict[str, tuple[str, ...]]:
    common: dict[str, dict[str, tuple[str, ...]]] = {
        "D03": {
            "event_duration_steps": ("18",),
            "receiver_trigger_distance_m": ("0.24",),
            "receiver_approach_distance_m": ("0.24",),
            "asset_scale": ("1.35",),
        },
        "D05": {
            "asset_scale": ("1.35",),
            "lateral_offset_m": ("0.04",),
            "path_progress_min_fraction": ("0.18",),
            "path_progress_max_fraction": ("0.95",),
            "path_progress_tolerance_m": ("0.22",),
        },
        "D06": {"offset_xy": ("0.12", "-0.09")},
        "D07": {"camera_offset_m": ("0.045", "-0.032", "0.020")},
        "D10": {"event_duration_steps": ("36",)},
        "D11": {"event_duration_steps": ("36",)},
        "D12": {
            "event_duration_steps": ("36",),
            "observation_delay_steps": ("6",),
        },
        "D14": {"event_duration_steps": ("4",)},
        "D15": {"chunk_size": ("8",), "stale_chunk_steps": ("8",)},
        "D16": {
            "event_duration_steps": ("12",),
            "takeover_action_value": ("0.18",),
        },
        "D19": {
            "receiver_approach_distance_m": ("0.24",),
            "misplacement_distance_m": ("0.07",),
        },
        "S03": {"height_delta_m": ("0.06",), "asset_scale": ("1.20",)},
        "S04": {"layout_offset_xy": ("0.16", "0.10")},
        "S07": {"geometry_factors": ("1.0", "0.72", "1.18")},
        "S09": {
            "target_geometry_factors": ("1.15", "1.15", "1.15"),
            "receiver_geometry_factors": ("0.88", "0.88", "0.88"),
        },
        "S10": {
            "asset_scale": ("1.50",),
            "clutter_radius_m": ("0.14",),
            "clutter_minimum_gap_m": ("0.08",),
        },
        "S11": {
            "distractor_offset_xy": ("0.07", "0.04"),
            "distractor_minimum_gap_m": ("0.05",),
        },
        "S15": {"camera_offset_m": ("0.065", "-0.050", "0.035")},
        "S16": {"fov_scale": ("1.20",), "image_shift_fraction": ("0.08",)},
        "S17": {
            "joint_offset": ("0.060", "-0.045", "0.035", "0", "0", "0", "0")
        },
        "S18": {"calibration_offset_m": ("0.012", "-0.008", "0.006")},
        "S20": {
            "observation_delay_steps": ("3",),
            "action_delay_steps": ("3",),
            "gripper_delay_steps": ("3",),
        },
    }
    values = dict(common.get(case_id, {}))
    if case_id == "S11":
        values["asset_scale"] = {
            "libero_10": ("0.78",),
            "libero_object": ("0.80",),
            "libero_spatial": ("0.36",),
        }.get(suite, ("0.75",))
    if suite == "libero_10" and task_id == 0 and case_id == "S10":
        # The living-room task has a particularly dense table layout. Keep
        # the clutter visible while fitting the collision-clear workspace.
        values.update(
            {
                "asset_scale": ("1.20",),
                "clutter_radius_m": ("0.10",),
                "clutter_minimum_gap_m": ("0.06",),
            }
        )
    if suite == "libero_10" and task_id == 0 and case_id == "D03":
        # A 1.35x foam brick intersects this basket's side wall. A compact,
        # upright bottle visibly occupies the opening without penetration and
        # is still removed by the normal 18-step restoration window.
        values.update(
            {
                "asset_id": ("prl/fuze_bottle",),
                "asset_scale": ("0.70",),
                "allow_compact_asset": ("true",),
            }
        )
    return values


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


def update_case(text: str, case_id: str, values: dict[str, tuple[str, ...]]) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing perturbation case {case_id}")
    case_end = group_end(text, match.start())
    case_text = text[match.start() : case_end]
    params_match = re.search(r"\(\s*:params\b", case_text)
    if not params_match:
        raise ValueError(f"Case {case_id} has no :params group")
    params_start = params_match.start()
    params_end = group_end(case_text, params_start)
    params_text = case_text[params_start:params_end]
    for key, atoms in values.items():
        field = f"(:{key} {' '.join(atoms)})"
        field_match = re.search(rf"\(\s*:{re.escape(key)}\b[^)]*\)", params_text)
        if field_match:
            params_text = (
                params_text[: field_match.start()]
                + field
                + params_text[field_match.end() :]
            )
        else:
            insertion = params_text.rfind(")")
            params_text = (
                params_text[:insertion]
                + f"\n          {field}"
                + params_text[insertion:]
            )
    case_text = case_text[:params_start] + params_text + case_text[params_end:]
    return text[: match.start()] + case_text + text[case_end:]


def path_for(suite: str, task_id: int, case_id: str) -> Path:
    try:
        task_name = SUITE_TASKS[suite][task_id]
    except (KeyError, IndexError) as exc:
        raise ValueError(f"Unknown task mapping {suite}|{task_id}") from exc
    directory = "01_static" if case_id.startswith("S") else "02_dynamic"
    path = BDDL_ROOT / suite / directory / f"{case_id}__{task_name}.bddl"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    rows = json.loads(LEDGER.read_text(encoding="utf-8"))
    keys = sorted({(row["套件"], int(row["任务ID"].removeprefix("task")), row["扰动"]) for row in rows})
    changed: list[str] = []
    for suite, task_id, case_id in keys:
        path = path_for(suite, task_id, case_id)
        original = path.read_text(encoding="utf-8")
        updated = update_case(original, case_id, overrides(suite, task_id, case_id))
        if updated != original:
            if not args.check_only:
                path.write_text(updated, encoding="utf-8", newline="\n")
            changed.append(str(path.relative_to(ROOT)))
    print(json.dumps({"keys": len(keys), "changed": len(changed), "paths": changed}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
