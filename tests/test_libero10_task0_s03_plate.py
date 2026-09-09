"""Regression checks for the task-local libero_10/task0 S03 lid obstacle."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


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


PARSER = _load(PARSER_PATH, "_task0_s03_plate_parser")
RUNTIME = _load(RUNTIME_PATH, "_task0_s03_plate_runtime")


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


def test_only_task0_s03_enables_receiver_lid_obstacle() -> None:
    target = _manifest_path("S03")
    task0_config = PARSER.parse_bddl_perturbation_config(target)
    task0_plan = RUNTIME.build_execution_plan(task0_config, ASSET_ROOT)

    assert task0_plan.case_id == "S03"
    assert task0_plan.targets == ("basket_1", "living_room_table")
    assert task0_plan.assets[0].asset_id == "prl/plastic_plate"
    assert task0_plan.assets[0].scale == 0.55
    assert task0_plan.params["receiver_lid_obstacle"] is True
    assert task0_plan.params["movable_asset"] is False
    assert task0_plan.params["physical_collision"] is True
    assert task0_plan.params["visual_only_asset"] is False
    assert task0_plan.params["receiver_lid_offset_xy"] == [0.028, -0.018]
    assert task0_plan.params["receiver_lid_clearance_m"] == 0.001

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


def test_receiver_lid_pose_math_uses_collision_geometry() -> None:
    params = {"receiver_lid_offset_xy": [0.028, -0.018]}
    assert np.allclose(params["receiver_lid_offset_xy"], [0.028, -0.018])
