import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "nonphysical_perturbations.py"
)
SPEC = importlib.util.spec_from_file_location("_libero10_d03_runtime", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)


def _task4_d03_path() -> Path:
    return next(
        (
            ROOT
            / "assets"
            / "bddl"
            / "libero-pro2.0-1680-v1"
            / "libero_10"
            / "02_dynamic"
        ).glob("D03__LIVING_ROOM_SCENE5*")
    )


def _multi_goal_env() -> SimpleNamespace:
    names = {
        "plate_1": 0,
        "plate_2": 1,
        "porcelain_mug_1": 2,
        "white_yellow_mug_1": 3,
        "red_coffee_mug_1": 4,
    }
    body_xpos = np.zeros((len(names), 3), dtype=np.float64)
    body_xquat = np.tile([1.0, 0.0, 0.0, 0.0], (len(names), 1))
    body_xpos[names["porcelain_mug_1"]] = [0.0, -0.30, 0.50]
    body_xpos[names["white_yellow_mug_1"]] = [0.0, 0.30, 0.50]
    body_xpos[names["plate_1"]] = [0.0, -0.30, 0.48]
    body_xpos[names["plate_2"]] = [0.0, 0.30, 0.48]
    body_xpos[names["red_coffee_mug_1"]] = [-0.25, 0.0, 0.50]
    site_positions = {
        "plate_left_region": np.array([0.0, -0.30, 0.48]),
        "plate_right_region": np.array([0.0, 0.30, 0.48]),
    }
    data = SimpleNamespace(
        body_xpos=body_xpos,
        body_xquat=body_xquat,
        site_xpos=np.array([[0.0, 0.30, 0.48]], dtype=np.float64),
        get_site_xpos=lambda name: site_positions[name],
    )
    return SimpleNamespace(
        obj_body_id=names,
        sim=SimpleNamespace(data=data),
        robots=[SimpleNamespace(eef_site_id=0)],
        object_sites_dict={
            "plate_left_region": SimpleNamespace(parent_name="plate_1"),
            "plate_right_region": SimpleNamespace(parent_name="plate_2"),
        },
        parsed_problem={
            "goal_state": [
                ["On", "porcelain_mug_1", "plate_left_region"],
                ["On", "white_yellow_mug_1", "plate_right_region"],
            ],
            "regions": {
                "plate_left_region": {"target": "living_room_table"},
                "plate_right_region": {"target": "living_room_table"},
            },
        },
    )


def _active_plan() -> object:
    return RUNTIME.ExecutionPlan(
        case_id="D03",
        schedule="dynamic",
        operator="occlusion_or_obstacle",
        variant="persistent_triggered_receiver_occupation",
        targets=("plate_1", "plate_2"),
        references=("red_coffee_mug_1",),
        mechanisms=("asset", "dynamic_pose"),
        assets=(),
        trigger="preplace",
        params={
            "persistent_existing_obstacle": True,
            "receiver_selection": "active_goal_path",
            "receiver_trigger_distance_m": 0.24,
        },
    )


def test_only_libero10_task4_d03_enables_active_goal_receiver_selection() -> None:
    target_bddl = _task4_d03_path()
    text = target_bddl.read_text(encoding="utf-8")
    assert "(:targets plate_1 plate_2)" in text
    assert "(:receiver_selection active_goal_path)" in text
    assert "(:support_surface living_room_table)" in text

    enabled = []
    for path in (
        ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
    ).glob("libero_*/02_dynamic/D03__*.bddl"):
        if "(:receiver_selection active_goal_path)" in path.read_text(
            encoding="utf-8"
        ):
            enabled.append(path)
    assert enabled == [target_bddl]


def test_active_goal_receiver_tracks_the_goal_object_near_the_eef() -> None:
    env = _multi_goal_env()
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(_active_plan(), seed=143)
    identity = np.array([1.0, 0.0, 0.0, 0.0])
    runtime._saved_poses = {
        "porcelain_mug_1": (np.array([0.0, -0.30, 0.50]), identity),
        "white_yellow_mug_1": (np.array([0.0, 0.30, 0.50]), identity),
    }
    env.sim.data.body_xpos[3] = [0.0, 0.30, 0.56]

    assert runtime._dynamic_triggered(env, 1)
    assert runtime._dynamic_active_goal_target == "white_yellow_mug_1"
    receiver, position, anchor = RUNTIME._goal_path_receiver_for_target(
        env, runtime._dynamic_active_goal_target
    )
    assert receiver == "plate_2"
    assert anchor == "plate_right_region"
    np.testing.assert_allclose(position, [0.0, 0.30, 0.48])


def test_d03_without_opt_in_keeps_configured_first_receiver_mode() -> None:
    plan = _active_plan()
    plan = RUNTIME.ExecutionPlan(
        case_id=plan.case_id,
        schedule=plan.schedule,
        operator=plan.operator,
        variant=plan.variant,
        targets=plan.targets,
        references=plan.references,
        mechanisms=plan.mechanisms,
        assets=plan.assets,
        trigger=plan.trigger,
        params={
            key: value
            for key, value in plan.params.items()
            if key != "receiver_selection"
        },
    )
    assert RUNTIME.NonPhysicalPerturbationRuntime(plan)._d03_receiver_selection() == (
        "configured_target"
    )
