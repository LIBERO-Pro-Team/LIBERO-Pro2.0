from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np


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


def test_only_spatial_task3_and_task5_s01_d01_opt_into_support_group_motion() -> None:
    manifest = json.loads(
        (ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8")
    )
    enabled: dict[tuple[str, int, str], dict[str, object]] = {}

    for item in manifest["tasks"]:
        if item["case_id"] not in {"S01", "D01"}:
            continue
        path = ROOT / "assets" / item["bddl_path"]
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )
        if plan.params.get("move_support_with_target") is True:
            key = (
                str(item["suite"]),
                int(item["base_task_id"]),
                str(item["case_id"]),
            )
            enabled[key] = plan.params

    assert set(enabled) == {
        ("libero_spatial", 3, "S01"),
        ("libero_spatial", 3, "D01"),
        ("libero_spatial", 5, "S01"),
        ("libero_spatial", 5, "D01"),
    }
    expected_supports = {3: "cookies_1", 5: "glazed_rim_porcelain_ramekin_1"}
    for (_, task_id, _), params in enabled.items():
        assert params["support_object"] == expected_supports[task_id]
        assert params["support_ground_surface"] == "main_table"
        assert params["group_minimum_clearance_m"] == 0.018


class _SupportSceneSim:
    def __init__(self) -> None:
        body_positions = np.array(
            [
                [0.0, 0.0, 0.88],
                [0.08, 0.03, 0.933],
                [0.09, 0.04, 0.986],
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


def _support_scene_env() -> SimpleNamespace:
    sim = _SupportSceneSim()
    return SimpleNamespace(
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


def _assert_relative_pose_preserved(
    before_support: tuple[np.ndarray, np.ndarray],
    before_target: tuple[np.ndarray, np.ndarray],
    after_support: tuple[np.ndarray, np.ndarray],
    after_target: tuple[np.ndarray, np.ndarray],
) -> None:
    before_relative = before_target[0] - before_support[0]
    after_relative = after_target[0] - after_support[0]
    before_support_rotation = RUNTIME._quaternion_to_rotation_matrix(before_support[1])
    after_support_rotation = RUNTIME._quaternion_to_rotation_matrix(after_support[1])
    np.testing.assert_allclose(
        after_support_rotation.T @ after_relative,
        before_support_rotation.T @ before_relative,
        atol=1e-9,
    )
    before_relative_quaternion = RUNTIME._quaternion_multiply(
        RUNTIME._quaternion_conjugate(before_support[1]), before_target[1]
    )
    after_relative_quaternion = RUNTIME._quaternion_multiply(
        RUNTIME._quaternion_conjugate(after_support[1]), after_target[1]
    )
    np.testing.assert_allclose(
        after_relative_quaternion, before_relative_quaternion, atol=1e-9
    )


def _group_params(offset_xy: list[float], yaw_rad: float) -> dict[str, object]:
    return {
        "offset_xy": offset_xy,
        "yaw_rad": yaw_rad,
        "move_support_with_target": True,
        "support_object": "cookies_1",
        "support_ground_surface": "main_table",
        "group_minimum_clearance_m": 0.018,
    }


def test_opted_in_s01_moves_support_group_without_changing_relative_pose() -> None:
    plan = RUNTIME.ExecutionPlan(
        case_id="S01",
        schedule="static",
        operator="pose_transform",
        variant="xy_yaw",
        targets=("akita_black_bowl_1",),
        references=(),
        mechanisms=("pose",),
        assets=(),
        params=_group_params([0.055, 0.035], 0.28),
    )
    env = _support_scene_env()
    before_support = RUNTIME._entity_pose(env, "cookies_1")
    before_target = RUNTIME._entity_pose(env, "akita_black_bowl_1")
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=143)

    runtime.apply_static(env)

    after_support = RUNTIME._entity_pose(env, "cookies_1")
    after_target = RUNTIME._entity_pose(env, "akita_black_bowl_1")
    np.testing.assert_allclose(
        after_support[0] - before_support[0], [0.055, 0.035, 0.0], atol=1e-9
    )
    _assert_relative_pose_preserved(
        before_support, before_target, after_support, after_target
    )
    assert [event["event"] for event in runtime.events] == [
        "support_group_transform",
        "static_pose_transform",
    ]


def test_opted_in_d01_moves_support_group_without_changing_relative_pose() -> None:
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
        params=_group_params([0.10, -0.08], 0.28),
    )
    env = _support_scene_env()
    before_support = RUNTIME._entity_pose(env, "cookies_1")
    before_target = RUNTIME._entity_pose(env, "akita_black_bowl_1")
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=143)
    runtime._dynamic_triggered = lambda _env, _step: True

    runtime.before_simulation_step(env, step=12)

    after_support = RUNTIME._entity_pose(env, "cookies_1")
    after_target = RUNTIME._entity_pose(env, "akita_black_bowl_1")
    np.testing.assert_allclose(
        after_support[0] - before_support[0], [0.10, -0.08, 0.0], atol=1e-9
    )
    _assert_relative_pose_preserved(
        before_support, before_target, after_support, after_target
    )
    assert [event["event"] for event in runtime.events] == [
        "support_group_transform",
        "dynamic_state_change",
    ]
    assert runtime.events[0]["support_object"] == "cookies_1"
    assert runtime.events[0]["support_ground_geom"] == "table_collision"


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
    env = _support_scene_env()
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=143)
    runtime._dynamic_triggered = lambda _env, _step: True

    runtime.before_simulation_step(env, step=12)

    cookie_xy = env.sim.data.body_xpos[1, :2]
    bowl_xy = env.sim.data.body_xpos[2, :2]
    assert np.linalg.norm(bowl_xy - cookie_xy) >= 0.08
    assert all(
        event["event"] != "support_group_transform" for event in runtime.events
    )
