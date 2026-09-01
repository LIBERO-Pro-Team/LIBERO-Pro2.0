from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "assets"
    / "perturbation_assets"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PARSER = _load_module(
    "_spatial_d01_parser",
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "perturbation_config.py",
)
RUNTIME = _load_module(
    "_spatial_d01_runtime",
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "nonphysical_perturbations.py",
)


def test_only_spatial_task3_d01_opts_into_support_preservation() -> None:
    manifest = json.loads(
        (ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8")
    )
    enabled: list[tuple[str, int, dict[str, object]]] = []

    for item in manifest["tasks"]:
        if item["case_id"] != "D01":
            continue
        path = ROOT / "assets" / item["bddl_path"]
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )
        if plan.params.get("preserve_original_support_relation") is True:
            enabled.append((str(item["suite"]), int(item["base_task_id"]), plan.params))

    assert len(enabled) == 1
    suite, task_id, params = enabled[0]
    assert (suite, task_id) == ("libero_spatial", 3)
    assert params["offset_xy"] == [0.020, -0.015]
    assert params["yaw_rad"] == 0.28
    assert params["support_surface"] == "cookies_1"
    assert params["support_relation_clearance_m"] == 0.018


class _SupportSceneSim:
    def __init__(self) -> None:
        body_positions = np.array(
            [
                [0.0, 0.0, 0.88],
                [0.08, 0.03, 0.91],
                [0.08, 0.03, 0.963],
            ],
            dtype=float,
        )
        body_quaternions = np.tile([1.0, 0.0, 0.0, 0.0], (3, 1))
        self.model = SimpleNamespace(
            nbody=3,
            body_pos=body_positions.copy(),
            body_quat=body_quaternions.copy(),
            body_parentid=np.array([-1, -1, -1], dtype=int),
            geom_bodyid=np.array([0, 1, 2], dtype=int),
            geom_group=np.zeros(3, dtype=int),
            geom_contype=np.ones(3, dtype=int),
            geom_aabb=np.array(
                [
                    [0.0, 0.0, 0.0, 0.50, 0.50, 0.02],
                    [0.0, 0.0, 0.0, 0.05, 0.04, 0.03],
                    [0.0, 0.0, 0.0, 0.025, 0.025, 0.02],
                ],
                dtype=float,
            ),
        )
        body_names = ("main_table", "cookies_1", "akita_black_bowl_1")
        geom_names = ("table_collision", "cookies_1_g0", "bowl_g0")
        self.model.body_id2name = lambda index: body_names[index]
        self.model.geom_id2name = lambda index: geom_names[index]
        self.data = SimpleNamespace(
            body_xpos=body_positions.copy(),
            body_xquat=body_quaternions.copy(),
            geom_xpos=body_positions.copy(),
            geom_xmat=np.tile(np.eye(3).reshape(1, 9), (3, 1)),
            ncon=0,
            contact=[],
        )

    def forward(self) -> None:
        self.data.body_xpos[:] = self.model.body_pos
        self.data.body_xquat[:] = self.model.body_quat
        self.data.geom_xpos[:] = self.model.body_pos


def test_opted_in_d01_moves_locally_and_stays_on_declared_support() -> None:
    plan = RUNTIME.ExecutionPlan(
        case_id="D01",
        schedule="dynamic",
        operator="pose_transform",
        variant="xy_yaw_update",
        targets=("akita_black_bowl_1",),
        references=(),
        mechanisms=("dynamic_pose",),
        assets=(),
        trigger="approach_or_pregrasp",
        params={
            "offset_xy": [0.020, -0.015],
            "yaw_rad": 0.28,
            "support_surface": "cookies_1",
            "preserve_original_support_relation": True,
            "support_relation_clearance_m": 0.018,
        },
    )
    sim = _SupportSceneSim()
    env = SimpleNamespace(
        obj_body_id={
            "main_table": 0,
            "cookies_1": 1,
            "akita_black_bowl_1": 2,
        },
        objects_dict={
            "cookies_1": SimpleNamespace(joints=None),
            "akita_black_bowl_1": SimpleNamespace(joints=None),
        },
        workspace_offset=np.array([0.0, 0.0, 0.9]),
        sim=sim,
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=143)
    runtime._dynamic_triggered = lambda _env, _step: True

    runtime.before_simulation_step(env, step=12)

    np.testing.assert_allclose(
        sim.data.body_xpos[2], [0.10, 0.015, 0.963], atol=1e-9
    )
    assert [event["event"] for event in runtime.events] == [
        "support_relation_preserved",
        "dynamic_state_change",
    ]
    assert runtime.events[0]["support"] == "cookies_1"
    assert runtime.events[0]["support_geom"] == "cookies_1_g0"


def test_d01_without_opt_in_keeps_existing_clearance_behavior() -> None:
    plan = RUNTIME.ExecutionPlan(
        case_id="D01",
        schedule="dynamic",
        operator="pose_transform",
        variant="xy_yaw_update",
        targets=("akita_black_bowl_1",),
        references=(),
        mechanisms=("dynamic_pose",),
        assets=(),
        trigger="approach_or_pregrasp",
        params={"offset_xy": [0.020, -0.015]},
    )
    sim = _SupportSceneSim()
    env = SimpleNamespace(
        obj_body_id={
            "main_table": 0,
            "cookies_1": 1,
            "akita_black_bowl_1": 2,
        },
        objects_dict={
            "cookies_1": SimpleNamespace(joints=None),
            "akita_black_bowl_1": SimpleNamespace(joints=None),
        },
        workspace_offset=np.array([0.0, 0.0, 0.9]),
        sim=sim,
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=143)
    runtime._dynamic_triggered = lambda _env, _step: True

    runtime.before_simulation_step(env, step=12)

    cookie_xy = sim.data.body_xpos[1, :2]
    bowl_xy = sim.data.body_xpos[2, :2]
    assert np.linalg.norm(bowl_xy - cookie_xy) >= 0.08
    assert all(
        event["event"] != "support_relation_preserved" for event in runtime.events
    )


def test_opted_in_d01_rejects_a_candidate_outside_declared_support() -> None:
    plan = RUNTIME.ExecutionPlan(
        case_id="D01",
        schedule="dynamic",
        operator="pose_transform",
        variant="xy_yaw_update",
        targets=("akita_black_bowl_1",),
        references=(),
        mechanisms=("dynamic_pose",),
        assets=(),
        trigger="approach_or_pregrasp",
        params={
            "offset_xy": [0.20, 0.0],
            "support_surface": "cookies_1",
            "preserve_original_support_relation": True,
            "support_relation_clearance_m": 0.018,
        },
    )
    sim = _SupportSceneSim()
    original_pose = sim.data.body_xpos[2].copy()
    env = SimpleNamespace(
        obj_body_id={
            "main_table": 0,
            "cookies_1": 1,
            "akita_black_bowl_1": 2,
        },
        objects_dict={
            "cookies_1": SimpleNamespace(joints=None),
            "akita_black_bowl_1": SimpleNamespace(joints=None),
        },
        workspace_offset=np.array([0.0, 0.0, 0.9]),
        sim=sim,
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=143)
    runtime._dynamic_triggered = lambda _env, _step: True

    with pytest.raises(RUNTIME.PerturbationValidationError):
        runtime.before_simulation_step(env, step=12)

    np.testing.assert_array_equal(sim.data.body_xpos[2], original_pose)
    assert runtime.events == []
