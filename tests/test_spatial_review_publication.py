from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SIMULATOR_ROOT = ROOT / "simulator-source" / "libero" / "libero"
ASSET_ROOT = SIMULATOR_ROOT / "assets" / "perturbation_assets"
FINALIZER_PATH = ROOT / "scripts" / "apply_goal_review_finalization.py"
FINALIZER_SPEC = importlib.util.spec_from_file_location(
    "_goal_review_finalizer_for_spatial", FINALIZER_PATH
)
assert FINALIZER_SPEC is not None and FINALIZER_SPEC.loader is not None
FINALIZER = importlib.util.module_from_spec(FINALIZER_SPEC)
sys.modules[FINALIZER_SPEC.name] = FINALIZER
FINALIZER_SPEC.loader.exec_module(FINALIZER)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PARSER = _load_module(
    "_spatial_review_parser", SIMULATOR_ROOT / "envs" / "perturbation_config.py"
)
RUNTIME = _load_module(
    "_spatial_review_runtime",
    SIMULATOR_ROOT / "envs" / "nonphysical_perturbations.py",
)
SELECTED_TASKS = {
    "S03": {0, 2, 8},
    "S06": {0, 2, 4, 5, 8},
    "S10": {0, 1, 2, 4, 7, 9},
    "S11": {0, 1, 3, 4, 5, 7, 8, 9},
    "S18": {0},
    "D01": {3},
    "D03": set(range(10)),
}


def _case_block(text: str, case_id: str) -> str:
    match = re.search(rf"(?m)^[ \t]*\({re.escape(case_id)}[ \t]*$", text)
    assert match is not None
    depth = 0
    for index in range(match.start(), len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise AssertionError(f"Unterminated {case_id} block")


def _param(block: str, name: str) -> tuple[str, ...]:
    match = re.search(rf"\(:{re.escape(name)}\s+([^)]+)\)", block)
    assert match is not None, name
    return tuple(match.group(1).split())


def _selected_entries() -> dict[tuple[str, int], dict[str, object]]:
    manifest = json.loads(
        (ASSETS / "task_manifest.json").read_text(encoding="utf-8")
    )
    return {
        (str(item["case_id"]), int(item["base_task_id"])): item
        for item in manifest["tasks"]
        if item["suite"] == "libero_spatial"
        and int(item["base_task_id"])
        in SELECTED_TASKS.get(str(item["case_id"]), set())
    }


def _selected_blocks() -> dict[tuple[str, int], str]:
    blocks: dict[tuple[str, int], str] = {}
    for key, item in _selected_entries().items():
        path = ASSETS / str(item["bddl_path"])
        blocks[key] = _case_block(path.read_text(encoding="utf-8"), key[0])
        digest = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        ).hexdigest()
        assert item["bddl_sha256"] == digest, path
    return blocks


def test_spatial_review_publication_contains_exactly_34_selected_tasks() -> None:
    expected = {
        (case_id, task_id)
        for case_id, task_ids in SELECTED_TASKS.items()
        for task_id in task_ids
    }
    assert set(_selected_entries()) == expected
    assert len(expected) == 34


def test_spatial_review_parameters_match_validated_values() -> None:
    blocks = _selected_blocks()

    assert _param(blocks[("S03", 0)], "asset_geometry_factors") == (
        "0.88",
        "0.88",
        "1.3",
    )
    assert _param(blocks[("S03", 0)], "height_delta_m") == ("0.005",)
    assert _param(blocks[("S03", 8)], "asset_geometry_factors") == (
        "0.70",
        "0.70",
        "1.6",
    )
    assert _param(blocks[("S03", 8)], "height_delta_m") == ("0.020",)
    assert _param(blocks[("S03", 2)], "asset_id") == (
        "generated/support_riser_wide_top",
    )
    assert _param(blocks[("S03", 2)], "asset_geometry_factors") == (
        "1.0",
        "1.0",
        "2.0",
    )
    assert _param(blocks[("S03", 2)], "height_delta_m") == ("0.10",)

    for task_id in SELECTED_TASKS["S06"]:
        assert _param(blocks[("S06", task_id)], "asset_id") == (
            "github/object_sim_bowl",
        )
        expected_scale = "0.6696" if task_id in {0, 8} else "0.70"
        assert _param(blocks[("S06", task_id)], "asset_scale") == (expected_scale,)
    for task_id in (0, 2, 8):
        assert _param(blocks[("S06", task_id)], "asset_quat") == (
            "1.0",
            "0.0",
            "0.0",
            "0.0",
        )

    for task_id in SELECTED_TASKS["S10"]:
        block = blocks[("S10", task_id)]
        assert _param(block, "movable_asset") == ("true",)
        assert _param(block, "physical_collision") == ("true",)
        assert _param(block, "visual_only_asset") == ("false",)
        assert _param(block, "clear_of_task_entities") == ("true",)
        assert _param(block, "asset_contact_margin_m") == ("0.006",)
    assert _param(blocks[("S10", 0)], "clutter_offsets_xy") == (
        "0.00",
        "0.12",
        "-0.15",
        "-0.12",
        "0.00",
        "-0.12",
    )
    assert _param(blocks[("S10", 0)], "clutter_minimum_gap_m") == ("0.10",)
    assert _param(blocks[("S10", 1)], "clutter_offsets_xy") == (
        "0.11",
        "-0.10",
        "-0.11",
        "-0.10",
    )
    assert _param(blocks[("S10", 2)], "clutter_offsets_xy") == (
        "0.12",
        "-0.12",
        "-0.12",
        "-0.12",
    )

    for task_id in SELECTED_TASKS["S11"]:
        block = blocks[("S11", task_id)]
        assert _param(block, "movable_asset") == ("true",)
        assert _param(block, "physical_collision") == ("true",)
        assert _param(block, "visual_only_asset") == ("false",)
        assert _param(block, "clear_of_task_entities") == ("true",)
    assert _param(blocks[("S11", 0)], "clutter_offsets_xy") == ("-0.14", "-0.12")
    assert _param(blocks[("S11", 1)], "clutter_offsets_xy") == ("0.10", "-0.18")
    assert _param(blocks[("S11", 7)], "clutter_offsets_xy") == (
        "0.20",
        "0.30",
    )
    assert _param(blocks[("S11", 7)], "support_surface") == ("main_table",)
    assert _param(blocks[("S11", 8)], "clutter_offsets_xy") == (
        "0.22",
        "-0.10",
    )

    for task_id in {0, 1, 3, 5, 7, 8}:
        assert _param(blocks[("S11", task_id)], "asset_id") == (
            "github/object_sim_bowl",
        )
        expected_scale = "0.45" if task_id in {1, 8} else "0.70"
        assert _param(blocks[("S11", task_id)], "asset_scale") == (expected_scale,)

    assert _param(blocks[("S11", 4)], "asset_id") == ("prl/plastic_bowl",)
    assert _param(blocks[("S11", 4)], "asset_scale") == ("0.60",)
    assert _param(blocks[("S11", 4)], "clutter_offsets_xy") == ("0.12", "0.10")
    assert _param(blocks[("S11", 4)], "support_surface") == ("main_table",)

    assert _param(blocks[("S11", 9)], "asset_id") == ("prl/plastic_bowl",)
    assert _param(blocks[("S11", 9)], "asset_scale") == ("0.60",)
    assert _param(blocks[("S11", 9)], "clutter_offsets_xy") == ("-0.10", "0.00")
    assert _param(blocks[("S11", 9)], "support_surface") == ("wooden_cabinet_1",)
    assert _param(blocks[("S11", 9)], "asset_contact_margin_m") == ("0.004",)

    generated_s03, _ = FINALIZER.case_updates("libero_spatial", 2, "S03")
    assert generated_s03 == {
        "asset_id": ("generated/support_riser_wide_top",),
        "asset_geometry_factors": ("1.0", "1.0", "2.0"),
        "height_delta_m": ("0.10",),
    }
    generated_s11, _ = FINALIZER.case_updates("libero_spatial", 9, "S11")
    assert generated_s11["clutter_offsets_xy"] == ("-0.10", "0.00")
    assert generated_s11["support_surface"] == ("wooden_cabinet_1",)
    for key in (
        ("libero_spatial", 2, "S11"),
        ("libero_spatial", 9, "S10"),
        ("libero_goal", 2, "S03"),
    ):
        generated, _ = FINALIZER.case_updates(*key)
        assert "asset_id" not in generated
        assert "asset_geometry_factors" not in generated
        assert "height_delta_m" not in generated

    s18 = blocks[("S18", 0)]
    assert _param(s18, "eef_offset_xyz") == ("0.080", "-0.060", "0.050")
    assert _param(s18, "joint_zero_offset_rad") == (
        "0.080",
        "-0.060",
        "0.050",
    )

    d01 = blocks[("D01", 3)]
    assert _param(d01, "offset_xy") == ("0.10", "-0.08")
    assert _param(d01, "yaw_rad") == ("0.28",)
    assert _param(d01, "move_support_with_target") == ("true",)
    assert _param(d01, "support_object") == ("cookies_1",)
    assert _param(d01, "support_ground_surface") == ("main_table",)
    assert _param(d01, "group_minimum_clearance_m") == ("0.018",)


def test_all_spatial_d03_tasks_use_the_same_movable_red_brick() -> None:
    blocks = _selected_blocks()

    for task_id in range(10):
        d03 = blocks[("D03", task_id)]
        assert _param(d03, "references") == ("none",)
        assert _param(d03, "persistent_movable_asset") == ("true",)
        assert "(:persistent_existing_obstacle " not in d03
        assert _param(d03, "support_surface") == ("plate_1",)
        assert _param(d03, "asset_id") == ("ycb/YcbFoamBrick",)
        assert _param(d03, "asset_scale") == ("0.85",)
        assert _param(d03, "asset_contact_margin_m") == ("0.0",)
        assert _param(d03, "asset_offset_xyz") == ("0.00835045", "0.00205392", "0.0")

        generated_params, generated_fields = FINALIZER.case_updates(
            "libero_spatial", task_id, "D03"
        )
        assert generated_fields["references"] == ("none",)
        assert generated_params["persistent_movable_asset"] == ("true",)
        assert "persistent_existing_obstacle" not in generated_params
        assert generated_params["support_surface"] == ("plate_1",)
        assert generated_params["asset_id"] == ("ycb/YcbFoamBrick",)
        assert generated_params["asset_scale"] == ("0.85",)
        assert generated_params["asset_contact_margin_m"] == ("0.0",)
        assert generated_params["asset_offset_xyz"] == ("0.00835045", "0.00205392", "0.0")


def test_spatial_round5_bowl_size_and_visibility_parameters() -> None:
    blocks = _selected_blocks()

    for task_id in (0, 8):
        assert _param(blocks[("S06", task_id)], "asset_scale") == ("0.6696",)
    assert _param(blocks[("S10", 0)], "clutter_offsets_xy") == (
        "0.00",
        "0.12",
        "-0.15",
        "-0.12",
        "0.00",
        "-0.12",
    )
    assert _param(blocks[("S11", 1)], "clutter_offsets_xy") == ("0.10", "-0.18")


def test_object_sim_bowl_is_published_as_an_explicit_asset() -> None:
    catalog = json.loads(
        (
            ROOT
            / "simulator-source"
            / "libero"
            / "libero"
            / "assets"
            / "perturbation_assets"
            / "asset_catalog.json"
        ).read_text(encoding="utf-8")
    )
    bowl = next(
        asset for asset in catalog["assets"] if asset["id"] == "github/object_sim_bowl"
    )
    xml_path = (
        ROOT
        / "simulator-source"
        / "libero"
        / "libero"
        / "assets"
        / "perturbation_assets"
        / bowl["path"]
    )
    assert bowl["license"] == "Apache-2.0"
    assert xml_path.is_file()


def test_only_reviewed_spatial_s03_tasks_select_the_wide_top_support() -> None:
    manifest = json.loads(
        (ASSETS / "task_manifest.json").read_text(encoding="utf-8")
    )
    resolved_assets: dict[tuple[str, int], tuple[str, ...]] = {}
    explicit_wide_top: set[tuple[str, int]] = set()

    for item in manifest["tasks"]:
        if item["case_id"] != "S03":
            continue
        key = (str(item["suite"]), int(item["base_task_id"]))
        path = ASSETS / str(item["bddl_path"])
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )
        resolved_assets[key] = tuple(asset.asset_id for asset in plan.assets)
        if plan.params.get("asset_id") == "generated/support_riser_wide_top":
            explicit_wide_top.add(key)

    targets = {("libero_spatial", 0), ("libero_spatial", 2)}
    assert RUNTIME.CASE_ASSETS["S03"] == ("generated/support_riser",)
    assert explicit_wide_top == targets
    assert all(
        resolved_assets[target] == ("generated/support_riser_wide_top",)
        for target in targets
    )
    assert all(
        asset_ids == ("generated/support_riser",)
        for key, asset_ids in resolved_assets.items()
        if key not in targets
    )


def test_wide_top_support_geometry_covers_the_plate_with_a_narrow_column() -> None:
    catalog = json.loads((ASSET_ROOT / "asset_catalog.json").read_text(encoding="utf-8"))
    asset = next(
        item
        for item in catalog["assets"]
        if item["id"] == "generated/support_riser_wide_top"
    )
    xml_path = ASSET_ROOT / asset["path"]
    geoms = {
        geom.get("name"): geom
        for geom in ET.parse(xml_path).getroot().findall(".//geom")
    }

    assert geoms["support_column"].get("size") == "0.035 0.035 0.0225"
    assert geoms["support_column"].get("pos") == "0 0 0.0225"
    assert geoms["support_deck"].get("size") == "0.075 0.075 0.0025"
    assert geoms["support_deck"].get("pos") == "0 0 0.0475"
    assert asset["parameters"]["column_half_extents"] == [0.035, 0.035, 0.0225]
    assert asset["parameters"]["deck_half_extents"] == [0.075, 0.075, 0.0025]
