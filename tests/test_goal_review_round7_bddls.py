"""Task-local contracts for the Goal(7) human review fixes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PARSER_SPEC = importlib.util.spec_from_file_location(
    "_goal7_parser",
    ROOT / "simulator-source/libero/libero/envs/perturbation_config.py",
)
assert PARSER_SPEC is not None and PARSER_SPEC.loader is not None
PARSER = importlib.util.module_from_spec(PARSER_SPEC)
PARSER_SPEC.loader.exec_module(PARSER)


def entries() -> dict[tuple[int, str], dict[str, object]]:
    manifest = json.loads((ASSETS / "task_manifest.json").read_text(encoding="utf-8"))
    return {
        (int(item["base_task_id"]), str(item["case_id"])): item
        for item in manifest["tasks"]
        if item["suite"] == "libero_goal"
    }


def active_fields(task: int, case: str) -> dict[str, object]:
    entry = entries()[task, case]
    path = ASSETS / str(entry["bddl_path"])
    canonical = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    assert hashlib.sha256(canonical).hexdigest() == entry["bddl_sha256"]
    config = PARSER.parse_bddl_perturbation_config(path)
    active = next(
        item for item in config["perturbations"] if str(item[0]).upper() == case
    )
    fields: dict[str, object] = {}
    for field in active[1:]:
        fields.update(field)
    return fields


def params(task: int, case: str) -> dict[str, object]:
    return active_fields(task, case)["params"]


@pytest.mark.parametrize("task", [0, 1, 2])
def test_reported_s10_clutter_is_fixed_but_physically_solid(task: int) -> None:
    p = params(task, "S10")
    assert p["movable_asset"] is False
    assert p["physical_collision"] is True
    assert p["visual_only_asset"] is False


def test_reported_s10_clutter_uses_task_local_plate_clearance() -> None:
    assert params(0, "S10")["clutter_offsets_xy"] == [
        0.24,
        0.18,
        0.24,
        -0.18,
        -0.24,
        -0.18,
    ]
    assert params(1, "S10")["clutter_offsets_xy"] == [
        0.24,
        0.18,
        0.24,
        -0.18,
        -0.24,
        -0.18,
    ]
    assert params(2, "S10")["clutter_offsets_xy"] == [0.38, 0.20, 0.40, -0.08]
    for task in (0, 1, 2):
        assert params(task, "S10")["clutter_minimum_gap_m"] == 0.14


def test_task0_cabinet_geometry_scales_collision_and_limits_drawer_extension() -> None:
    for case, range_scale in (("S07", 0.64), ("S09", 0.80)):
        p = params(0, case)
        assert p["scale_compiled_geometry"] is True
        assert p["articulation_joint_range_scale"] == range_scale


def test_task0_s08_has_a_clearer_collision_backed_geometry_change() -> None:
    p = params(0, "S08")
    assert p["geometry_factors"] == [1.30, 0.76, 1.0]
    assert p["scale_compiled_geometry"] is True
    assert p["articulation_joint_range_scale"] == 0.76


def test_task3_d02_moves_cabinet_away_from_the_wine_rack() -> None:
    p = params(3, "D02")
    assert p["offset_xy"] == [0.12, -0.09]
    assert p["yaw_rad"] == -0.24


def test_task2_d03_uses_a_larger_injected_plate() -> None:
    p = params(2, "D03")
    assert p["persistent_movable_asset"] is True
    assert p["asset_id"] == "prl/plastic_plate"
    assert p["asset_scale"] == 0.75


def test_task5_d03_preserves_scene_objects_and_injects_an_absent_asset() -> None:
    fields = active_fields(5, "D03")
    p = fields["params"]
    assert fields["references"] == "none"
    assert p["persistent_movable_asset"] is True
    assert "persistent_existing_obstacle" not in p
    assert p["asset_id"] == "ycb/ycbfoambrick"
    assert p["asset_contact_margin_m"] == 0.006


def test_task6_d03_places_a_red_brick_inside_the_bowl() -> None:
    fields = active_fields(6, "D03")
    p = fields["params"]
    assert fields["references"] == "none"
    assert p["persistent_movable_asset"] is True
    assert p["support_surface"] == "akita_black_bowl_1"
    assert p["asset_id"] == "ycb/ycbfoambrick"
    assert p["asset_scale"] == 0.60
    assert p["asset_offset_xyz"] == [0.00835045, 0.00205392, 0.0]


@pytest.mark.parametrize("case", ["S05", "D05"])
def test_task8_barrier_stays_between_bowl_and_plate(case: str) -> None:
    p = params(8, case)
    key = "barrier_path_fraction"
    assert p[key] == (0.45 if case == "S05" else 0.50)
    lateral_key = "barrier_lateral_offset_m" if case == "S05" else "lateral_offset_m"
    assert p[lateral_key] == 0.0


def test_task8_s05_alone_opts_into_support_grounding() -> None:
    p = params(8, "S05")
    assert p["barrier_scale"] == 0.65
    assert p["barrier_geometry_factors"] == [1.25, 1.0, 1.25]
    assert p["ground_barrier_to_support"] is True
    assert p["support_surface"] == "main_table"
    configured = {
        (task, case)
        for task, case in entries()
        if case == "S05" and params(task, case).get("ground_barrier_to_support") is True
    }
    assert configured == {(8, "S05")}


def test_task8_d05_uses_a_task_local_height_correction() -> None:
    assert params(8, "D05")["barrier_height_m"] == -0.035


def test_task2_s09_alone_closes_regions_at_the_endpoint() -> None:
    assert params(2, "S09")["initial_closed_region_endpoint"] is True
    configured = {
        (task, case)
        for task, case in entries()
        if case == "S09"
        and params(task, case).get("initial_closed_region_endpoint") is True
    }
    assert configured == {(2, "S09")}


def test_task8_s08_scales_compiled_collision_geometry() -> None:
    p = params(8, "S08")
    assert p["geometry_factors"] == [1.32, 1.20, 0.72]
    assert p["scale_compiled_geometry"] is True


def test_task8_s10_has_extra_plate_clearance() -> None:
    p = params(8, "S10")
    assert p["movable_asset"] is False
    assert p["clutter_minimum_gap_m"] == 0.14
    assert p["clutter_offsets_xy"] == [0.26, -0.20, 0.22, 0.22, -0.21, 0.10]


def test_round7_task_local_opt_ins_do_not_expand_to_unreported_goal_tasks() -> None:
    compiled_geometry = {
        (task, case)
        for task, case in entries()
        if case in {"S07", "S08", "S09"}
        and params(task, case).get("scale_compiled_geometry") is True
    }
    assert compiled_geometry == {
        (0, "S07"),
        (0, "S08"),
        (0, "S09"),
        (2, "S07"),
        (2, "S08"),
        (2, "S09"),
        (4, "S07"),
        (8, "S08"),
        (9, "S07"),
    }
