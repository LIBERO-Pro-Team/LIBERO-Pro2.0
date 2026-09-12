"""Publish only the reviewed Libero10 configurations and matching hashes."""

from __future__ import annotations

import hashlib
import json

import pytest

from test_libero10_task0_receiver_perturbations import ASSET_ROOT, PARSER, ROOT, RUNTIME


def _entry(task_id, case_id):
    manifest = json.loads((ROOT / "assets/task_manifest.json").read_text(encoding="utf-8"))
    return next(
        entry for entry in manifest["tasks"]
        if entry["suite"] == "libero_10"
        and entry["base_task_id"] == task_id
        and entry["case_id"] == case_id
    )


def _path(task_id, case_id):
    return ROOT / "assets" / _entry(task_id, case_id)["bddl_path"]


def _plan(task_id, case_id):
    return RUNTIME.build_execution_plan(
        PARSER.parse_bddl_perturbation_config(_path(task_id, case_id)), ASSET_ROOT
    )


@pytest.mark.parametrize("task_id,case_id", [(0, "S03"), (0, "D03"), (5, "D03"), (6, "S13")])
def test_reviewed_entry_hash_and_original_scene_match(task_id, case_id):
    path = _path(task_id, case_id)
    canonical = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    assert hashlib.sha256(canonical).hexdigest() == _entry(task_id, case_id)["bddl_sha256"]

    def scene(path):
        return [node for node in PARSER.scan_tokens(filename=str(path))
                if not (isinstance(node, list) and node and node[0] == ":perturbation_config")]

    assert scene(path) == scene(_path(task_id, "BASE"))


def test_task5_d03_uses_larger_independent_movable_obstacle():
    plan = _plan(5, "D03")
    assert plan.targets == ("desk_caddy_1",)
    assert not plan.references
    assert plan.params["persistent_movable_asset"] is True
    assert not plan.params.get("persistent_existing_obstacle", False)
    assert plan.assets[0].asset_id == "ycb/YcbChipsCan"
    assert plan.assets[0].scale == 0.70
    assert plan.params["receiver_anchor"] == "desk_caddy_1_back_contain_region"
    assert plan.params["asset_offset_xyz"] == [0.005, -0.009, -0.075]
    assert "event_duration_steps" not in plan.params


def test_task6_s13_colors_all_three_targets_and_leaves_red_mug_alone():
    plan = _plan(6, "S13")
    assert plan.targets == ("porcelain_mug_1", "plate_1", "chocolate_pudding_1")
    assert plan.params["color_rgb"] == [0.18, 0.72, 0.38]
