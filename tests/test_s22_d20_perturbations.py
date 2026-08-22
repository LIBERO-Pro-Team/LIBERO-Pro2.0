from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "nonphysical_perturbations.py"
)
SPEC = importlib.util.spec_from_file_location("_s22_d20_runtime", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)


def _plan(case_id: str, **params):
    return RUNTIME.ExecutionPlan(
        case_id=case_id,
        schedule="static" if case_id.startswith("S") else "dynamic",
        operator="asset_or_appearance" if case_id == "S22" else "pose_transform",
        variant=(
            "support_surface_texture_replacement"
            if case_id == "S22"
            else "collision_induced_reachable_joint_displacement"
        ),
        targets=("workspace_surface",) if case_id == "S22" else ("robot0",),
        references=(),
        mechanisms=("appearance",) if case_id == "S22" else ("robot_state",),
        assets=(),
        trigger="reset" if case_id == "S22" else "robot_in_motion",
        params=params,
        constraints=("collision_geometry_unchanged",) if case_id == "S22" else (),
    )


def test_s22_changes_only_the_workspace_visual_material() -> None:
    class Model:
        def __init__(self) -> None:
            self.geom_matid = np.array([2, 3], dtype=int)
            self.geom_size = np.array([[0.4, 0.4, 0.4], [0.4, 0.4, 0.4]])
            self.geom_friction = np.array([[1.0, 0.005, 0.0001]] * 2)
            self.geom_contype = np.array([0, 1], dtype=int)
            self.geom_conaffinity = np.array([0, 1], dtype=int)

        @staticmethod
        def geom_name2id(name: str) -> int:
            if name == "table_visual":
                return 0
            if name == "table_collision":
                return 1
            raise KeyError(name)

        @staticmethod
        def material_name2id(name: str) -> int:
            if name == "s22_table_texture":
                return 7
            raise KeyError(name)

    model = Model()
    env = SimpleNamespace(
        workspace_name="main_table",
        sim=SimpleNamespace(model=model, forward=lambda: None),
    )
    collision_before = model.geom_size.copy(), model.geom_friction.copy()

    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("S22", material_id="s22_table_texture"), seed=11
    )
    runtime.apply_static(env)

    assert model.geom_matid.tolist() == [7, 3]
    np.testing.assert_array_equal(model.geom_size, collision_before[0])
    np.testing.assert_array_equal(model.geom_friction, collision_before[1])
    assert runtime.events[-1]["event"] == "workspace_texture_replaced"


class _D20Model:
    def __init__(self) -> None:
        self.jnt_qposadr = np.array([0, 1], dtype=int)
        self.jnt_range = np.array([[-2.0, 2.0], [-2.0, 2.0]])
        self.jnt_limited = np.array([1, 1], dtype=int)
        self.njnt = 2
        self.geom_bodyid = np.array([], dtype=int)
        self.body_parentid = np.array([0], dtype=int)
        self.nbody = 1

    @staticmethod
    def body_name2id(name: str) -> int:
        if name == "robot0_base":
            return 0
        raise KeyError(name)


class _D20Data:
    def __init__(self) -> None:
        self.qpos = np.array([0.0, 0.0])
        self.qvel = np.array([0.4, -0.2])
        self.site_xpos = np.array([[0.0, 0.0, 1.0]])
        self.site_xmat = np.eye(3).reshape(1, 9)
        self.ncon = 0
        self.contact = []


class _D20Sim:
    def __init__(self, *, collide_after_teleport: bool = False) -> None:
        self.model = _D20Model()
        self.data = _D20Data()
        self.collide_after_teleport = collide_after_teleport

    def forward(self) -> None:
        self.data.site_xpos[0] = [0.5 * self.data.qpos[0], 0.5 * self.data.qpos[1], 1.0]
        displaced_from_trigger_pose = not np.allclose(
            self.data.qpos, np.array([0.06, 0.0])
        )
        if self.collide_after_teleport and displaced_from_trigger_pose:
            self.data.ncon = 1
            self.data.contact = [SimpleNamespace(geom1=0, geom2=1, dist=-0.01)]
            self.model.geom_bodyid = np.array([0, 0], dtype=int)
        else:
            self.data.ncon = 0
            self.data.contact = []


def _d20_env(*, collide_after_teleport: bool = False):
    sim = _D20Sim(collide_after_teleport=collide_after_teleport)
    robot_model = SimpleNamespace(root_body="robot0_base", naming_prefix="robot0_")
    robot = SimpleNamespace(
        _ref_joint_pos_indexes=[0, 1],
        _ref_joint_vel_indexes=[0, 1],
        eef_site_id=0,
        robot_model=robot_model,
    )
    return SimpleNamespace(
        sim=sim,
        robots=[robot],
        workspace_offset=np.array([0.0, 0.0, 0.8]),
        objects_dict={},
        object_sites_dict={},
        parsed_problem={"goal_state": []},
    )


def test_d20_triggers_from_robot_motion_once_and_zeros_joint_velocity() -> None:
    env = _d20_env()
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan(
            "D20",
            trigger_eef_motion_m=0.025,
            trigger_action_norm=0.05,
            min_eef_displacement_m=0.035,
            joint_delta_rad=0.12,
        ),
        seed=3,
    )
    runtime.begin_rollout(env)

    runtime.previous_action = np.array([0.0, 0.0, 0.0, 0.0])
    runtime.before_simulation_step(env, step=5)
    assert not runtime._dynamic_applied

    env.sim.data.qpos[0] = 0.06
    env.sim.forward()
    runtime.previous_action = np.array([0.2, 0.0, 0.0, 0.0])
    before = env.sim.data.qpos.copy()
    runtime.before_simulation_step(env, step=19)

    assert runtime._dynamic_applied
    assert np.linalg.norm(env.sim.data.qpos - before) > 0.0
    np.testing.assert_array_equal(env.sim.data.qvel, [0.0, 0.0])
    assert runtime.events[-1]["event"] == "robot_collision_displacement"
    event_count = len(runtime.events)

    runtime.before_simulation_step(env, step=20)
    assert len(runtime.events) == event_count


def test_d20_rolls_back_when_every_candidate_has_new_penetration() -> None:
    env = _d20_env(collide_after_teleport=True)
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan(
            "D20",
            trigger_eef_motion_m=0.025,
            trigger_action_norm=0.05,
            min_eef_displacement_m=0.035,
            joint_delta_rad=0.12,
            penetration_tolerance_m=0.001,
        ),
        seed=3,
    )
    runtime.begin_rollout(env)
    env.sim.data.qpos[0] = 0.06
    env.sim.forward()
    runtime.previous_action = np.array([0.2, 0.0, 0.0, 0.0])
    before_qpos = env.sim.data.qpos.copy()
    before_qvel = env.sim.data.qvel.copy()

    with pytest.raises(RUNTIME.PerturbationValidationError, match="collision-free D20"):
        runtime.before_simulation_step(env, step=19)

    np.testing.assert_array_equal(env.sim.data.qpos, before_qpos)
    np.testing.assert_array_equal(env.sim.data.qvel, before_qvel)
    assert not runtime._dynamic_applied


def test_four_published_scene_types_precompile_the_s22_material() -> None:
    scenes = (
        "libero_tabletop_base_style.xml",
        "libero_kitchen_tabletop_base_style.xml",
        "libero_living_room_tabletop_base_style.xml",
        "libero_study_base_style.xml",
        "libero_floor_base_style.xml",
    )
    root = ROOT / "simulator-source" / "libero" / "libero" / "assets" / "scenes"
    for filename in scenes:
        source = (root / filename).read_text(encoding="utf-8")
        assert 'name="tex-s22-table"' in source
        assert 'name="s22_table_texture"' in source
        assert "table_light_wood.png" in source


def test_new_bddl_cases_resolve_with_runtime_parameters() -> None:
    parser_path = (
        ROOT
        / "simulator-source"
        / "libero"
        / "libero"
        / "envs"
        / "perturbation_config.py"
    )
    parser_spec = importlib.util.spec_from_file_location("_s22_d20_parser", parser_path)
    assert parser_spec is not None and parser_spec.loader is not None
    parser = importlib.util.module_from_spec(parser_spec)
    sys.modules[parser_spec.name] = parser
    parser_spec.loader.exec_module(parser)

    root = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
    s22 = next((root / "libero_spatial" / "01_static").glob("S22__*.bddl"))
    d20 = next((root / "libero_spatial" / "02_dynamic").glob("D20__*.bddl"))
    s22_plan = RUNTIME.build_execution_plan(
        parser.parse_bddl_perturbation_config(s22),
        ROOT / "simulator-source" / "libero" / "libero" / "assets" / "perturbation_assets",
    )
    d20_plan = RUNTIME.build_execution_plan(
        parser.parse_bddl_perturbation_config(d20),
        ROOT / "simulator-source" / "libero" / "libero" / "assets" / "perturbation_assets",
    )
    assert s22_plan.case_id == "S22"
    assert s22_plan.params["material_id"] == "s22_table_texture"
    assert d20_plan.case_id == "D20"
    assert d20_plan.params["min_eef_displacement_m"] == 0.035
