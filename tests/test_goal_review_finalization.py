from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "apply_goal_review_finalization.py"
SPEC = importlib.util.spec_from_file_location("_goal_review_finalization", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
FINALIZER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FINALIZER
SPEC.loader.exec_module(FINALIZER)

PARSER_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "perturbation_config.py"
)
PARSER_SPEC = importlib.util.spec_from_file_location(
    "_goal_review_parameter_parser", PARSER_PATH
)
assert PARSER_SPEC is not None and PARSER_SPEC.loader is not None
PARSER = importlib.util.module_from_spec(PARSER_SPEC)
PARSER_SPEC.loader.exec_module(PARSER)


def _active_params(path: Path, case_id: str) -> dict[str, object]:
    config = PARSER.parse_bddl_perturbation_config(path)
    active = next(
        entry
        for entry in config["perturbations"]
        if isinstance(entry, list) and str(entry[0]).upper() == case_id
    )
    fields: dict[str, object] = {}
    for field in active[1:]:
        if isinstance(field, dict):
            fields.update(field)
    return fields["params"]


def test_global_review_parameters_apply_to_every_supported_suite_task() -> None:
    s05_safety_overrides = {
        ("libero_10", 0): {
            "barrier_scale": ("1.15",),
            "barrier_path_fraction": ("0.50",),
            "barrier_lateral_offset_m": ("0.04",),
        },
        ("libero_object", 0): {
            "barrier_scale": ("1.35",),
            "barrier_path_fraction": ("0.50",),
            "barrier_lateral_offset_m": ("-0.07",),
        },
        ("libero_spatial", 0): {
            "barrier_scale": ("0.65",),
            "barrier_path_fraction": ("0.40",),
            "barrier_lateral_offset_m": ("0.0",),
        },
        ("libero_spatial", 8): {
            "barrier_scale": ("0.35",),
            "barrier_path_fraction": ("0.50",),
            "barrier_lateral_offset_m": ("0.100",),
        },
        ("libero_goal", 3): {
            "barrier_scale": ("0.60",),
            "barrier_path_fraction": ("0.30",),
            "barrier_lateral_offset_m": ("0.08",),
        },
        ("libero_goal", 9): {
            "barrier_scale": ("1.0",),
            "barrier_path_fraction": ("0.62",),
            "barrier_lateral_offset_m": ("0.025",),
        },
    }
    s09_safety_overrides = {
        ("libero_goal", 1): {
            "target_geometry_factors": ("1.2", "1.2", "1.2"),
            "receiver_geometry_factors": ("0.8", "0.8", "1.0"),
        },
        ("libero_goal", 2): {
            "target_geometry_factors": ("1.2", "1.2", "1.2"),
            "receiver_geometry_factors": ("0.8", "0.8", "1.0"),
        },
        ("libero_goal", 3): {
            "target_geometry_factors": ("1.2", "1.2", "1.2"),
            "receiver_geometry_factors": ("0.8", "0.8", "1.0"),
        },
        ("libero_goal", 4): {
            "target_geometry_factors": ("1.2", "1.2", "1.2"),
            "receiver_geometry_factors": ("0.8", "0.8", "1.0"),
        },
        ("libero_goal", 7): {
            "target_geometry_factors": ("1.2", "1.2", "1.2"),
            "receiver_geometry_factors": ("0.8", "0.8", "1.0"),
        },
        ("libero_goal", 9): {
            "target_geometry_factors": ("1.2", "1.2", "1.2"),
            "receiver_geometry_factors": ("0.90", "0.90", "1.0"),
        },
    }
    s07_goal_overrides = {
        ("libero_goal", task_id): {
            "geometry_factors": ("1.0", "0.64", "1.20"),
            "goal_region_scale": ("1.0", "0.64", "1.20"),
        }
        for task_id in (2, 3, 4, 9)
    }
    for suite in FINALIZER.SUITES:
        for task_id in range(10):
            s05_params = FINALIZER.case_updates(suite, task_id, "S05")[0]
            expected_s05 = s05_safety_overrides.get((suite, task_id), {
                "barrier_scale": ("0.65",),
                "barrier_path_fraction": ("0.35",),
                "barrier_lateral_offset_m": ("0.0",),
            })
            assert expected_s05.items() <= s05_params.items()
            assert s05_params["visual_only_asset"] == ("false",)
            expected_s07 = s07_goal_overrides.get((suite, task_id), {
                "geometry_factors": ("1.0", "0.64", "1.20"),
                "goal_region_scale": ("1.0", "1.0", "1.0"),
            })
            assert expected_s07.items() <= FINALIZER.case_updates(
                suite, task_id, "S07"
            )[0].items()
            expected_s09 = s09_safety_overrides.get((suite, task_id), {
                "target_geometry_factors": ("1.2", "1.2", "1.2"),
                "receiver_geometry_factors": ("0.8", "0.8", "0.8"),
            })
            assert expected_s09.items() <= FINALIZER.case_updates(
                suite, task_id, "S09"
            )[0].items()
            assert {
                "eef_offset_xyz": ("0.050", "-0.040", "0.030"),
                "joint_zero_offset_rad": ("0.050", "-0.040", "0.030"),
                "grasp_center_offset_xyz": ("0.0", "0.0", "0.0"),
            }.items() <= FINALIZER.case_updates(suite, task_id, "S18")[0].items()
            assert FINALIZER.case_updates(suite, task_id, "S20")[0][
                "delay_steps"
            ] == ("7",)
            assert FINALIZER.case_updates(suite, task_id, "D12")[0][
                "delay_steps"
            ] == ("10",)
            assert {
                "arm_delay_steps": ("8",),
                "gripper_delay_steps": ("8",),
            }.items() <= FINALIZER.case_updates(suite, task_id, "D13")[0].items()
            assert {
                "visual_only_asset": ("false",),
                "physical_collision": ("true",),
            }.items() <= FINALIZER.case_updates(suite, task_id, "D05")[0].items()
            assert {
                "repeat_count": ("8",),
                "event_duration_steps": ("8",),
            }.items() <= FINALIZER.case_updates(suite, task_id, "D14")[0].items()
            assert {
                "chunk_size": ("12",),
                "stale_chunk_steps": ("8",),
            }.items() <= FINALIZER.case_updates(suite, task_id, "D15")[0].items()


def test_published_all_task_parameters_cover_all_four_suites() -> None:
    payload = json.loads(FINALIZER.MANIFEST.read_text(encoding="utf-8"))
    expected = {
        "S09": {
            "target_geometry_factors": [1.2, 1.2, 1.2],
            "receiver_geometry_factors": [0.8, 0.8, 0.8],
        },
        "S18": {
            "eef_offset_xyz": [0.05, -0.04, 0.03],
            "joint_zero_offset_rad": [0.05, -0.04, 0.03],
            "grasp_center_offset_xyz": [0.0, 0.0, 0.0],
        },
        "S20": {"delay_steps": 7},
        "D12": {"delay_steps": 10},
        "D13": {"arm_delay_steps": 8, "gripper_delay_steps": 8},
        "D14": {"repeat_count": 8, "event_duration_steps": 8},
        "D15": {"chunk_size": 12, "stale_chunk_steps": 8},
        "D05": {"visual_only_asset": False, "physical_collision": True},
    }
    counts = {case_id: 0 for case_id in expected}
    s09_overrides = {
        ("libero_10", 2): {
            "target_geometry_factors": [1.1, 1.1, 1.1],
            "receiver_geometry_factors": [0.95, 0.95, 0.95],
        },
        ("libero_10", 9): {
            "target_geometry_factors": [1.1, 1.1, 1.1],
            "receiver_geometry_factors": [1.0, 1.0, 1.0],
        },
        ("libero_goal", 1): {
            "target_geometry_factors": [1.2, 1.2, 1.2],
            "receiver_geometry_factors": [0.8, 0.8, 1.0],
        },
        ("libero_goal", 2): {
            "target_geometry_factors": [1.0, 1.0, 1.0],
            "receiver_geometry_factors": [0.8, 0.8, 1.0],
        },
        ("libero_goal", 3): {
            "target_geometry_factors": [1.2, 1.2, 1.2],
            "receiver_geometry_factors": [0.8, 0.8, 1.0],
        },
        ("libero_goal", 4): {
            "target_geometry_factors": [1.2, 1.2, 1.2],
            "receiver_geometry_factors": [0.8, 0.8, 1.0],
        },
        ("libero_goal", 7): {
            "target_geometry_factors": [1.2, 1.2, 1.2],
            "receiver_geometry_factors": [0.8, 0.8, 1.0],
        },
        ("libero_goal", 9): {
            "target_geometry_factors": [1.2, 1.2, 1.2],
            "receiver_geometry_factors": [0.9, 0.9, 1.0],
        },
    }

    for item in payload["tasks"]:
        case_id = str(item["case_id"])
        if case_id not in expected:
            continue
        params = _active_params(ROOT / "assets" / item["bddl_path"], case_id)
        expected_params = s09_overrides.get((item["suite"], item["base_task_id"]), expected[case_id]) if case_id == "S09" else expected[case_id]
        assert expected_params.items() <= params.items(), (
            item["suite"],
            item["base_task_id"],
            case_id,
            params,
        )
        counts[case_id] += 1

    assert counts == {
        "S09": 39,
        "S18": 40,
        "S20": 40,
        "D12": 40,
        "D13": 39,
        "D14": 40,
        "D15": 40,
        "D05": 38,
    }


def test_published_d03_uses_persistent_updates_for_active_tasks() -> None:
    payload = json.loads(FINALIZER.MANIFEST.read_text(encoding="utf-8"))
    published: set[tuple[str, int]] = set()

    for item in payload["tasks"]:
        if item["case_id"] != "D03":
            continue
        key = (str(item["suite"]), int(item["base_task_id"]))
        params = _active_params(ROOT / "assets" / item["bddl_path"], "D03")
        assert params["receiver_trigger_distance_m"] > 0
        assert params["staging_position_xyz"] == [0.0, 0.0, -5.0]
        assert params.get("persistent_existing_obstacle") is True or params.get(
            "persistent_movable_asset"
        ) is True
        published.add(key)

    assert len(published) == 39


def test_d03_persistent_updates_are_explicit_for_each_suite_task() -> None:
    for suite in FINALIZER.SUITES:
        for task_id in range(10):
            params, fields = FINALIZER.case_updates(suite, task_id, "D03")
            assert params.get("persistent_existing_obstacle") == ("true",) or params.get(
                "persistent_movable_asset"
            ) == ("true",)
            assert fields["variant"] == ("persistent_triggered_receiver_occupation",)


def test_final_manifest_exclusions_are_exactly_d19_and_reviewed_not_applicable_cases() -> None:
    excluded = {
        (suite, task_id, case_id)
        for suite in FINALIZER.SUITES
        for task_id in range(10)
        for case_id in FINALIZER.PUBLISHED_CASES
        if FINALIZER.is_excluded(suite, task_id, case_id)
    }

    assert len(excluded) == 59
    assert sum(case_id == "D19" for _, _, case_id in excluded) == 40
    assert ("libero_10", 8, "S04") in excluded
    assert excluded - {
        (suite, task_id, "D19")
        for suite in FINALIZER.SUITES
        for task_id in range(10)
    } == FINALIZER.GOAL_NOT_APPLICABLE | {("libero_10", 8, "S04")}


def test_goal_task0_s11_keeps_the_original_scene_structure() -> None:
    source = (
        ROOT
        / "assets"
        / "bddl"
        / "00_original"
        / "bddl"
        / "libero_goal"
        / "open_the_middle_drawer_of_the_cabinet.bddl"
    ).read_text(encoding="utf-8")

    once = FINALIZER.apply_goal_structural_overrides(source, 0, "S11")
    twice = FINALIZER.apply_goal_structural_overrides(once, 0, "S11")

    assert once == twice
    assert "yellow_cabinet_2 - yellow_cabinet" not in once
    assert "similar_cabinet_region" not in once
    assert "(On yellow_cabinet_2 " not in once
    assert once.count("(On wooden_cabinet_1 main_table_cabinet_region)") == 1


def test_goal_task_specific_review_updates_are_scoped() -> None:
    task0_s06, task0_s06_fields = FINALIZER.case_updates(
        "libero_goal", 0, "S06"
    )
    task7_s06, task7_s06_fields = FINALIZER.case_updates(
        "libero_goal", 7, "S06"
    )
    task6_s03, _ = FINALIZER.case_updates("libero_goal", 6, "S03")
    task8_s03, _ = FINALIZER.case_updates("libero_goal", 8, "S03")
    task9_s03, _ = FINALIZER.case_updates("libero_goal", 9, "S03")
    task0_s11, task0_s11_fields = FINALIZER.case_updates(
        "libero_goal", 0, "S11"
    )
    task5_s13, task5_s13_fields = FINALIZER.case_updates(
        "libero_goal", 5, "S13"
    )

    assert "asset_id" not in task0_s06
    assert "asset_scale" not in task0_s06
    assert task0_s06["fixture_variant"] == ("true",)
    assert task0_s06_fields["targets"] == ("wooden_cabinet_1",)
    assert "asset_id" not in task7_s06
    assert "asset_scale" not in task7_s06
    assert task7_s06["fixture_variant"] == ("true",)
    assert task7_s06_fields["targets"] == ("flat_stove_1",)
    assert task6_s03["height_delta_m"] == ("0.05",)
    assert task8_s03["height_delta_m"] == ("0.05",)
    assert task9_s03["height_delta_m"] == ("0.07",)
    assert task0_s11["asset_id"] == ("libero/yellow_cabinet",)
    assert task0_s11["movable_asset"] == ("true",)
    assert task0_s11["physical_collision"] == ("true",)
    assert task0_s11["weld_internal_asset_joints"] == ("true",)
    assert "weld_asset_joints" not in task0_s11
    assert task0_s11["clutter_offsets_xy"] == ("-0.067791", "0.639295")
    assert task0_s11_fields["targets"] == ("wooden_cabinet_1",)
    assert task5_s13_fields["targets"] == ("plate_1",)
