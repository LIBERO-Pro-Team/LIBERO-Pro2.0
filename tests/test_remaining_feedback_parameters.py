from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"
PARSER_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "perturbation_config.py"
)
SPEC = importlib.util.spec_from_file_location("_remaining_feedback_parser", PARSER_PATH)
assert SPEC is not None and SPEC.loader is not None
PARSER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PARSER)

# Published review overrides through 2026-09-13; all other tasks keep defaults.
S07_REVIEW_OVERRIDES = {
    ("libero_goal", 2, "S07"): ([1.0, 0.64, 1.2], [1.0, 0.64, 1.2]),
    ("libero_goal", 3, "S07"): ([0.64, 1.0, 1.2], [1.2, 1.0, 0.64]),
    ("libero_goal", 4, "S07"): ([1.0, 0.64, 1.2], [1.0, 0.64, 1.2]),
    ("libero_goal", 9, "S07"): ([1.0, 0.9, 1.1], [1.0, 1.6, 1.2]),
    ("libero_object", 8, "S07"): ([1.0, 0.64, 1.2], [0.3, 0.22, 1.0]),
}


def _params_by_key() -> dict[tuple[str, int, str], dict[str, object]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = {}
    for item in payload["tasks"]:
        case_id = str(item["case_id"])
        if case_id not in {"D17", "S07", "S13", "S14", "S18"}:
            continue
        config = PARSER.parse_bddl_perturbation_config(
            ROOT / "assets" / item["bddl_path"]
        )
        active = next(
            entry
            for entry in config["perturbations"]
            if isinstance(entry, list) and str(entry[0]).upper() == case_id
        )
        fields = {}
        for field in active[1:]:
            if isinstance(field, dict):
                fields.update(field)
        result[(item["suite"], int(item["base_task_id"]), case_id)] = fields[
            "params"
        ]
    return result


def test_remaining_runtime_defaults_are_explicit_in_all_case_bddls() -> None:
    params = _params_by_key()
    assert len(params) == 198
    assert all(
        {
            "grasp_distance_m",
            "grasp_initial_tolerance_m",
            "contact_fallback_distance_m",
            "wrapper_fallback_distance_m",
            "articulation_grasp_distance_m",
        }
        <= set(values)
        for key, values in params.items()
        if key[2] == "D17"
    )
    assert all(
        {"geometry_factors", "goal_region_scale"} <= set(values)
        for key, values in params.items()
        if key[2] == "S07"
    )
    assert all(
        values["color_rgb"] == [0.18, 0.72, 0.38]
        for key, values in params.items()
        if key[2] == "S13"
    )
    assert all(
        {
            "eef_offset_xyz",
            "joint_zero_offset_rad",
            "grasp_center_offset_xyz",
        }
        <= set(values)
        for key, values in params.items()
        if key[2] == "S18"
    )
    assert all(
        {
            "scene_color_mix",
            "scene_luminance_factors",
            "light_factor",
        }
        <= set(values)
        for key, values in params.items()
        if key[2] == "S14"
    )


def test_feedback_tasks_have_only_the_intended_task_level_overrides() -> None:
    params = _params_by_key()
    assert params[("libero_goal", 2, "D17")]["event_duration_steps"] == 48
    assert params[("libero_goal", 7, "D17")]["event_duration_steps"] == 48
    assert params[("libero_goal", 7, "D17")][
        "articulation_grasp_distance_m"
    ] == 0.16

    for key, (geometry, region) in S07_REVIEW_OVERRIDES.items():
        assert params[key]["geometry_factors"] == geometry
        assert params[key]["goal_region_scale"] == region

    assert params[("libero_spatial", 9, "S14")]["scene_color_mix"] == 0.32
    assert params[("libero_spatial", 9, "S14")]["light_factor"] == 0.78


def test_unreported_tasks_keep_the_previous_runtime_default_values() -> None:
    params = _params_by_key()
    for key, values in params.items():
        case_id = key[2]
        if case_id == "D17":
            task2 = key == ("libero_goal", 2, "D17")
            assert values["grasp_distance_m"] == (0.16 if task2 else 0.12)
            assert values["grasp_initial_tolerance_m"] == (0.05 if task2 else 0.035)
            assert values["contact_fallback_distance_m"] == (0.08 if task2 else 0.055)
            assert values["wrapper_fallback_distance_m"] == (0.16 if task2 else 0.12)
            expected_articulation = 0.16 if key == ("libero_goal", 7, "D17") else 0.14
            assert values["articulation_grasp_distance_m"] == expected_articulation
        elif case_id == "S07":
            geometry, region = S07_REVIEW_OVERRIDES.get(
                key, ([1.0, 0.64, 1.20], [1.0, 1.0, 1.0])
            )
            assert values["geometry_factors"] == geometry
            assert values["goal_region_scale"] == region
        elif case_id == "S13":
            assert values["color_rgb"] == [0.18, 0.72, 0.38]
        elif case_id == "S14":
            expected_mix = 0.32 if key == ("libero_spatial", 9, "S14") else 0.48
            expected_light = 0.78 if key == ("libero_spatial", 9, "S14") else 0.64
            assert values["scene_color_mix"] == expected_mix
            assert values["scene_luminance_factors"] == [0.72, 0.86, 1.18]
            assert values["light_factor"] == expected_light


@pytest.mark.parametrize(
    ("case_id", "missing_field"),
    [
        ("D17", "grasp_initial_tolerance_m"),
        ("D19", "misplace_offset_xy"),
        ("S07", "goal_region_scale"),
        ("S13", "color_rgb"),
        ("S14", "scene_color_mix"),
        ("S18", "joint_zero_offset_rad"),
    ],
)
def test_remaining_runtime_fields_are_not_backfilled_by_runtime(
    case_id: str, missing_field: str
) -> None:
    runtime_path = (
        ROOT
        / "simulator-source"
        / "libero"
        / "libero"
        / "envs"
        / "nonphysical_perturbations.py"
    )
    tree = ast.parse(runtime_path.read_text(encoding="utf-8"))
    required_fields: set[str] = set()
    optional_fields: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if len(node.args) < 2 or not isinstance(node.args[1], ast.Constant):
            continue
        field = node.args[1].value
        if not isinstance(field, str):
            continue
        if node.func.id in {"_required_param_float", "_required_param_vector"}:
            required_fields.add(field)
        elif node.func.id in {"_param_float", "_param_vector"}:
            optional_fields.add(field)

    assert missing_field in required_fields, case_id
    assert missing_field not in optional_fields, case_id
