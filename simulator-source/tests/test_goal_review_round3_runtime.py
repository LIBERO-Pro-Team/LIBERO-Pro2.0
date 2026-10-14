from __future__ import annotations

import importlib.util
import sys
import types
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "libero" / "libero" / "envs" / "nonphysical_perturbations.py"
SPEC = importlib.util.spec_from_file_location("goal_review_round3_runtime", MODULE_PATH)
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNTIME)


def _plan(case_id: str, *, targets=(), references=(), trigger="none", **params):
    return RUNTIME.ExecutionPlan(
        case_id=case_id,
        schedule="static" if case_id.startswith("S") else "dynamic",
        operator="test",
        variant="test",
        targets=tuple(targets),
        references=tuple(references),
        mechanisms=(),
        assets=(),
        trigger=trigger,
        params=params,
    )


def test_task_phase_trigger_anchor_is_opt_in() -> None:
    data = types.SimpleNamespace(
        body_xpos=np.array([[1.0, 0.0, 0.0]]),
        body_xquat=np.array([[1.0, 0.0, 0.0, 0.0]]),
        site_xpos=np.array([[0.20, 0.0, 0.0]]),
        get_site_xpos=lambda name: np.array([0.0, 0.0, 0.0]),
    )
    env = types.SimpleNamespace(
        obj_body_id={"cabinet": 0},
        object_sites_dict={"drawer_anchor": types.SimpleNamespace(parent_name="cabinet")},
        parsed_problem={"goal_state": [["Open", "drawer_anchor"]]},
        sim=types.SimpleNamespace(data=data),
        robots=[types.SimpleNamespace(eef_site_id=0)],
    )
    plan = _plan(
        "D08",
        targets=("agentview",),
        trigger="task_phase",
        trigger_anchor="drawer_anchor",
        trigger_distance_m=0.30,
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan)

    assert runtime._dynamic_triggered(env, 0)

    runtime.plan.params.pop("trigger_anchor")
    assert not runtime._dynamic_triggered(env, 0)


def test_camera_occluder_offset_defaults_to_zero() -> None:
    model = types.SimpleNamespace(camera_name2id=lambda _name: 0)
    data = types.SimpleNamespace(
        body_xpos=np.array([[0.0, 0.0, 0.0]]),
        body_xquat=np.array([[1.0, 0.0, 0.0, 0.0]]),
        cam_xpos=np.array([[0.0, 0.0, 2.0]]),
    )
    env = types.SimpleNamespace(
        obj_body_id={"target": 0}, sim=types.SimpleNamespace(model=model, data=data)
    )

    baseline, baseline_quat = RUNTIME._camera_occluder_pose(env, "target")
    shifted, shifted_quat = RUNTIME._camera_occluder_pose(
        env, "target", offset_xyz=(0.05, -0.02, 0.01)
    )

    np.testing.assert_allclose(shifted - baseline, [0.05, -0.02, 0.01])
    np.testing.assert_allclose(shifted_quat, baseline_quat)


def test_d05_barrier_path_fraction_defaults_to_legacy_value(monkeypatch) -> None:
    captured: list[np.ndarray] = []
    monkeypatch.setattr(
        RUNTIME,
        "_entity_exists",
        lambda _env, name: name in {"reference", "perturbation_d05_0"},
    )
    monkeypatch.setattr(
        RUNTIME,
        "_entity_pose",
        lambda _env, _name: (
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0, 0.0]),
        ),
    )
    monkeypatch.setattr(
        RUNTIME,
        "_goal_path_anchors",
        lambda _env: (
            "target",
            np.array([0.0, 0.0, 0.0]),
            "receiver_anchor",
            np.array([1.0, 0.0, 0.0]),
        ),
    )

    def capture_pose(_env, _name, requested, _quat, _params, **_kwargs):
        captured.append(np.asarray(requested).copy())
        return np.asarray(requested).copy(), "support"

    monkeypatch.setattr(RUNTIME, "_safe_dynamic_asset_pose", capture_pose)
    env = types.SimpleNamespace()

    legacy = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D05", targets=("robot_future_path",), references=("reference",))
    )
    monkeypatch.setattr(legacy, "_dynamic_triggered", lambda _env, _step: True)
    legacy.before_simulation_step(env, 1)

    configured = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan(
            "D05",
            targets=("robot_future_path",),
            references=("reference",),
            barrier_path_fraction=0.35,
            lateral_offset_m=0.0,
        )
    )
    monkeypatch.setattr(configured, "_dynamic_triggered", lambda _env, _step: True)
    configured.before_simulation_step(env, 1)

    assert captured[0][0] == pytest.approx(0.62)
    assert captured[1][0] == pytest.approx(0.35)


class _ArticulatedFixture:
    def __init__(self) -> None:
        self.asset = ET.fromstring('<asset><mesh name="mesh" scale="1 1 1" /></asset>')
        self.worldbody = ET.fromstring(
            '<worldbody><body pos="0 0 0.2">'
            '<joint name="top_level" type="slide" range="-0.16 0.01" />'
            '<geom size="0.1 0.2 0.3" pos="0 0 0.1" />'
            '<site size="0.08 0.08 0.1" pos="0 0.1 0.15" />'
            "</body></worldbody>"
        )
        self.object_properties = {
            "articulation": {
                "default_open_ranges": [-0.16, -0.14],
                "default_close_ranges": [0.0, 0.005],
            }
        }


def test_articulation_range_and_goal_region_scaling_are_task_local() -> None:
    configured = _ArticulatedFixture()
    plan = _plan(
        "S07",
        targets=("cabinet",),
        geometry_factors=(1.0, 0.64, 1.20),
        goal_region_scale=(1.0, 0.64, 1.20),
        articulation_joint_range_scale=0.64,
    )

    RUNTIME.apply_precompile_geometry({"cabinet": configured}, {}, plan)

    joint = configured.worldbody.find(".//joint")
    site = configured.worldbody.find(".//site")
    np.testing.assert_allclose(np.fromstring(joint.get("range"), sep=" "), [-0.1024, 0.0064])
    np.testing.assert_allclose(
        configured.object_properties["articulation"]["default_open_ranges"],
        [-0.1024, -0.0896],
    )
    np.testing.assert_allclose(
        np.fromstring(site.get("pos"), sep=" "), [0.0, 0.064, 0.18]
    )
    np.testing.assert_allclose(
        np.fromstring(site.get("size"), sep=" "), [0.08, 0.0512, 0.12]
    )

    legacy = _ArticulatedFixture()
    legacy_plan = _plan(
        "S07",
        targets=("cabinet",),
        geometry_factors=(1.0, 0.64, 1.20),
        goal_region_scale=(1.0, 1.0, 1.0),
    )
    RUNTIME.apply_precompile_geometry({"cabinet": legacy}, {}, legacy_plan)
    assert legacy.worldbody.find(".//joint").get("range") == "-0.16 0.01"
    assert legacy.object_properties["articulation"]["default_open_ranges"] == [
        -0.16,
        -0.14,
    ]
