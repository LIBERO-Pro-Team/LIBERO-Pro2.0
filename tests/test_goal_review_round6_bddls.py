"""Task-local contracts for the Goal(6) human review fixes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSET_ROOT = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "assets"
    / "perturbation_assets"
)
PARSER_SPEC = importlib.util.spec_from_file_location(
    "_goal6_parser",
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


@pytest.mark.parametrize("task", [2, 9])
def test_reviewed_s06_uses_the_task_local_fitted_collision_bottle(task: int) -> None:
    p = params(task, "S06")
    assert p["asset_id"] == "prl/fuze_bottle_fitted_collision"
    assert p["asset_scale"] == 0.72


def test_fitted_bottle_preserves_visual_mesh_and_uses_profiled_collisions() -> None:
    catalog = json.loads((ASSET_ROOT / "asset_catalog.json").read_text(encoding="utf-8"))
    records = {item["id"]: item for item in catalog["assets"]}
    record = records["prl/fuze_bottle_fitted_collision"]
    tree = ET.parse(ASSET_ROOT / record["path"])
    root = tree.getroot()
    mesh = root.find("./asset/mesh")
    assert mesh is not None
    assert mesh.get("file", "").endswith("fuze_bottle/fuze_bottle_visual.obj")
    collisions = [
        geom
        for geom in root.findall(".//geom")
        if geom.get("group", "0") == "0" and geom.get("type") == "cylinder"
    ]
    assert len(collisions) == 5
    radii = [float(geom.get("size", "").split()[0]) for geom in collisions]
    assert radii == pytest.approx([0.0375, 0.0348, 0.0295, 0.0240, 0.0225])
    assert sum(float(geom.get("mass", "0")) for geom in collisions) == pytest.approx(0.4)


@pytest.mark.parametrize("case", ["S07", "S08", "S09"])
def test_task2_geometry_review_scales_compiled_geometry(case: str) -> None:
    assert params(2, case)["scale_compiled_geometry"] is True


def test_task2_s09_keeps_the_target_clear_while_scaling_the_receiver() -> None:
    p = params(2, "S09")
    assert p["target_geometry_factors"] == [1.0, 1.0, 1.0]
    assert p["receiver_geometry_factors"] == [0.8, 0.8, 1.0]


def test_task2_s09_starts_with_all_cabinet_drawers_closed() -> None:
    entry = entries()[2, "S09"]
    text = (ASSETS / str(entry["bddl_path"])).read_text(encoding="utf-8")
    assert "(Close wooden_cabinet_1_top_region)" in text
    assert "(Close wooden_cabinet_1_middle_region)" in text
    assert "(Close wooden_cabinet_1_bottom_region)" in text
    assert params(2, "S09")["initial_closed_regions"] == [
        "wooden_cabinet_1_top_region",
        "wooden_cabinet_1_middle_region",
        "wooden_cabinet_1_bottom_region",
    ]


def test_initial_closed_regions_is_scoped_to_task2_s09() -> None:
    configured = {
        (task, case)
        for task, case in entries()
        if case == "S09" and "initial_closed_regions" in params(task, case)
    }
    assert configured == {(2, "S09")}


def test_goal_s10_clutter_is_movable_and_starts_at_rest() -> None:
    for task in range(10):
        p = params(task, "S10")
        assert p["movable_asset"] is True
        assert p["zero_initial_asset_velocity"] is True
        assert p["physical_collision"] is True
        assert p["visual_only_asset"] is False


def test_task8_s10_keeps_clutter_clear_of_the_scene_plate() -> None:
    p = params(8, "S10")
    assert p["clutter_offsets_xy"] == [0.26, -0.20, 0.22, 0.22, -0.21, 0.10]
    assert p["clutter_minimum_gap_m"] == 0.140


@pytest.mark.parametrize("task,scale", [(4, 0.65)])
def test_reviewed_d03_injects_a_new_plate_without_moving_the_scene_plate(
    task: int, scale: float
) -> None:
    fields = active_fields(task, "D03")
    p = fields["params"]
    assert p["persistent_movable_asset"] is True
    assert "persistent_existing_obstacle" not in p
    assert p["asset_id"] == "prl/plastic_plate"
    assert p["asset_scale"] == scale
    assert p["asset_contact_margin_m"] == 0.004


def test_task6_d03_supersedes_the_plate_with_a_smaller_red_brick() -> None:
    fields = active_fields(6, "D03")
    p = fields["params"]
    assert fields["references"] == "none"
    assert p["persistent_movable_asset"] is True
    assert p["asset_id"].lower() == "ycb/ycbfoambrick"
    assert p["asset_scale"] == 0.60
    assert p["asset_contact_margin_m"] == 0.0


def test_task6_d05_places_the_obstacle_between_the_cheese_and_bowl() -> None:
    p = params(6, "D05")
    assert p["barrier_path_fraction"] == 0.60
    assert p["lateral_offset_m"] == -0.025
    assert "trigger_anchor" not in p
    assert "trigger_distance_m" not in p
    assert p["asset_scale"] == 0.804
    assert p["barrier_height_m"] == -0.035
    assert p["support_surface"] == "main_table"


def test_task6_s11_places_the_similar_object_nearer_the_target() -> None:
    p = params(6, "S11")
    assert p["clutter_offsets_xy"] == [0.09, 0.05]
    assert p["clutter_minimum_gap_m"] == 0.080


def test_task8_d05_moves_the_obstacle_between_the_bowl_and_plate() -> None:
    p = params(8, "D05")
    assert p["barrier_height_m"] == -0.035
    assert p["barrier_path_fraction"] == 0.50
    assert p["lateral_offset_m"] == 0.0
    assert p["asset_scale"] == 1.10


def test_task9_d05_reduces_the_whole_obstacle_at_the_same_path_position() -> None:
    p = params(9, "D05")
    assert p["asset_scale"] == 0.70
    assert "barrier_path_fraction" not in p
    assert "lateral_offset_m" not in p


def test_task9_s05_reduces_only_obstacle_height() -> None:
    p = params(9, "S05")
    assert p["barrier_geometry_factors"] == [1.0, 1.0, 0.65]
    assert p["barrier_path_fraction"] == 0.62
    assert p["barrier_lateral_offset_m"] == 0.025
