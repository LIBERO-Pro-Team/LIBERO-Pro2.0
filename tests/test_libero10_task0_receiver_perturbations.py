"""Task0 keeps D03 clutter separate from S03 receiver height changes."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_ROOT = ROOT / "simulator-source"
PARSER_PATH = SIMULATOR_ROOT / "libero" / "libero" / "envs" / "perturbation_config.py"
RUNTIME_PATH = SIMULATOR_ROOT / "libero" / "libero" / "envs" / "nonphysical_perturbations.py"
ASSET_ROOT = SIMULATOR_ROOT / "libero" / "libero" / "assets" / "perturbation_assets"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PARSER = _load(PARSER_PATH, "_task0_receiver_parser")
RUNTIME = _load(RUNTIME_PATH, "_task0_receiver_runtime")


def _manifest_path(case_id: str) -> Path:
    manifest = json.loads((ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8"))
    item = next(
        item
        for item in manifest["tasks"]
        if item["suite"] == "libero_10"
        and int(item["base_task_id"]) == 0
        and item["case_id"] == case_id
    )
    return ROOT / "assets" / item["bddl_path"]


def test_task0_s03_raises_receiver_without_a_lid_obstacle() -> None:
    target = _manifest_path("S03")
    task0_config = PARSER.parse_bddl_perturbation_config(target)
    task0_plan = RUNTIME.build_execution_plan(task0_config, ASSET_ROOT)

    assert task0_plan.case_id == "S03"
    assert task0_plan.targets == ("basket_1", "living_room_table")
    assert task0_plan.assets[0].asset_id == "generated/support_riser"
    assert not task0_plan.params.get("receiver_lid_obstacle", False)
    # The raw basket init pose is above its settled pose; this grounds a 7cm riser.
    assert task0_plan.params["height_delta_m"] == 0.03675
    assert task0_plan.params["asset_geometry_factors"] == [0.70, 0.70, 1.4]

    other_s03 = []
    manifest = json.loads((ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8"))
    for item in manifest["tasks"]:
        if item["suite"] == "libero_10" and item["case_id"] == "S03":
            path = ROOT / "assets" / item["bddl_path"]
            plan = RUNTIME.build_execution_plan(
                PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
            )
            if int(item["base_task_id"]) != 0:
                other_s03.append(plan)
    assert other_s03
    assert all(not plan.params.get("receiver_lid_obstacle", False) for plan in other_s03)


def test_task0_d03_injects_unrelated_movable_obstacle() -> None:
    plan = RUNTIME.build_execution_plan(
        PARSER.parse_bddl_perturbation_config(_manifest_path("D03")), ASSET_ROOT
    )
    assert plan.params.get("persistent_movable_asset", False)
    assert not plan.params.get("persistent_existing_obstacle", False)
    assert not plan.references
    assert len(plan.assets) == 1
    assert plan.assets[0].asset_id == "ycb/YcbFoamBrick"
    assert plan.targets == ("basket_1",)
    assert plan.trigger == "preplace"
    assert plan.variant == "persistent_triggered_receiver_occupation"
    assert plan.params["asset_offset_xyz"] == [0.0, 0.0, -0.07]


def test_task0_base_scene_objects_and_goals_are_unchanged() -> None:
    def scene_sections(path):
        return [node for node in PARSER.scan_tokens(filename=str(path))
                if not (isinstance(node, list) and node and node[0] == ":perturbation_config")]

    base = scene_sections(_manifest_path("BASE"))
    assert scene_sections(_manifest_path("S03")) == base
    assert scene_sections(_manifest_path("D03")) == base
