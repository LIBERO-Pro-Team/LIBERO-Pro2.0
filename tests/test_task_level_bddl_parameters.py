from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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
SPEC = importlib.util.spec_from_file_location("_task_level_runtime", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)


def _plan(case_id: str, **params):
    return RUNTIME.ExecutionPlan(
        case_id=case_id,
        schedule="static" if case_id.startswith("S") else "dynamic",
        operator="test",
        variant="test",
        targets=(),
        references=(),
        mechanisms=(),
        assets=(),
        trigger="task_phase" if case_id.startswith("D") else "reset",
        params=params,
    )


def test_s16_default_image_shift_keeps_legacy_height_rule() -> None:
    value = np.arange(4 * 5 * 1, dtype=np.uint8).reshape(4, 5, 1)
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(_plan("S16"))

    transformed = runtime.transform_observation({"agentview_image": value}, 0)

    expected = np.roll(value, shift=(1, -1), axis=(-3, -2))
    np.testing.assert_array_equal(transformed["agentview_image"], expected)


def test_s20_delay_steps_controls_observation_action_and_gripper() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(_plan("S20", delay_steps=2))

    actions = [
        runtime.transform_action(np.array([value, 0.0]), step)
        for step, value in enumerate((1.0, 2.0, 3.0))
    ]
    grippers = [
        runtime.transform_gripper_force_command(value, step)
        for step, value in enumerate((0.1, 0.2, 0.3))
    ]
    observations = [
        runtime.transform_observation({"state": np.array([value])}, step)["state"]
        for step, value in enumerate((1, 2, 3))
    ]

    np.testing.assert_array_equal(actions[0], [1.0, 0.0])
    np.testing.assert_array_equal(actions[1], [2.0, 0.0])
    np.testing.assert_array_equal(actions[2], [1.0, 0.0])
    assert grippers == [0.1, 0.2, 0.1]
    assert [item.tolist() for item in observations] == [[1], [2], [1]]


def test_d13_task_parameters_keep_arm_and_gripper_delays_independent() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D13", arm_delay_steps=2, gripper_delay_steps=1)
    )
    runtime._dynamic_event_step = 2

    runtime.transform_action(np.array([1.0, 10.0]), 0)
    runtime.transform_action(np.array([2.0, 20.0]), 1)
    action = runtime.transform_action(np.array([3.0, 30.0]), 2)

    runtime.transform_gripper_force_command(0.1, 0)
    runtime.transform_gripper_force_command(0.2, 1)
    gripper = runtime.transform_gripper_force_command(0.3, 2)

    np.testing.assert_array_equal(action, [1.0, 30.0])
    assert gripper == 0.2


def test_d21_value_parameter_replaces_fixed_language_prefix() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D21", value="Proceed_carefully")
    )
    runtime._dynamic_event_step = 0

    assert runtime.language_instruction("place the mug", 0) == (
        "Proceed carefully: place the mug"
    )


def test_d16_takeover_action_parameter_is_padded_to_action_size() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D16", takeover_action=(0.2, -0.1), event_duration_steps=2)
    )
    runtime._dynamic_event_step = 0

    action = runtime.transform_action(np.ones(4), 0)

    np.testing.assert_array_equal(action, [0.2, -0.1, 0.0, 0.0])


def test_d14_drop_repeat_counts_advance_when_event_starts_at_zero() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D14", drop_count=1, repeat_count=1, event_duration_steps=3)
    )
    runtime._dynamic_event_step = 0

    first = runtime.transform_action(np.array([1.0, 0.0]), 0)
    second = runtime.transform_action(np.array([2.0, 0.0]), 1)
    third = runtime.transform_action(np.array([3.0, 0.0]), 2)

    np.testing.assert_array_equal(first, [1.0, 0.0])
    np.testing.assert_array_equal(second, [1.0, 0.0])
    np.testing.assert_array_equal(third, [3.0, 0.0])


def test_d09_lighting_factor_is_task_local_and_visible_in_observations() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D09", event_duration_steps=2, lighting_factor=0.25)
    )
    runtime._dynamic_event_step = 0
    image = np.full((2, 2, 3), 200, dtype=np.uint8)

    transformed = runtime.transform_observation({"agentview_image": image}, 0)

    np.testing.assert_array_equal(transformed["agentview_image"], 50)
    event = runtime.events[-1]
    assert event["lighting_factor"] == 0.25
    assert event["requested_value"] == {"lighting_factor": 0.25}
    assert event["applied_value"]["agentview_image"]["before_mean"] == 200.0
    assert event["applied_value"]["agentview_image"]["after_mean"] == 50.0


def test_d11_freezes_only_declared_modalities() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D11", event_duration_steps=2, freeze_modalities=("rgb",))
    )
    runtime._dynamic_event_step = 0
    runtime.transform_observation(
        {
            "agentview_image": np.array([1], dtype=np.uint8),
            "agentview_depth": np.array([2], dtype=np.float32),
            "robot_state": np.array([3], dtype=np.float32),
        },
        0,
    )
    transformed = runtime.transform_observation(
        {
            "agentview_image": np.array([9], dtype=np.uint8),
            "agentview_depth": np.array([8], dtype=np.float32),
            "robot_state": np.array([7], dtype=np.float32),
        },
        1,
    )

    np.testing.assert_array_equal(transformed["agentview_image"], [1])
    np.testing.assert_array_equal(transformed["agentview_depth"], [8])
    np.testing.assert_array_equal(transformed["robot_state"], [7])


def test_s13_color_and_s14_domain_shift_are_task_local() -> None:
    model = type(
        "Model",
        (),
        {
            "ngeom": 1,
            "geom_bodyid": np.array([0]),
            "geom_rgba": np.array([[0.4, 0.5, 0.6, 1.0]], dtype=np.float64),
            "light_diffuse": np.ones((1, 3), dtype=np.float64),
            "light_ambient": np.ones((1, 3), dtype=np.float64),
        },
    )()
    sim = type("Sim", (), {"model": model, "forward": lambda self: None})()
    env = type(
        "Env",
        (),
        {"sim": sim, "obj_body_id": {"target": 0}, "objects_dict": {}},
    )()

    s13 = RUNTIME.NonPhysicalPerturbationRuntime(
        RUNTIME.ExecutionPlan(
            case_id="S13",
            schedule="static",
            operator="test",
            variant="test",
            targets=("target",),
            references=(),
            mechanisms=(),
            assets=(),
            params={"color_rgb": (0.25, 0.60, 0.45)},
        )
    )
    s13._change_appearance(env, ("target",))
    np.testing.assert_allclose(model.geom_rgba[0, :3], [0.25, 0.60, 0.45])

    model.geom_rgba[0] = [0.4, 0.5, 0.6, 1.0]
    s14 = RUNTIME.NonPhysicalPerturbationRuntime(
        RUNTIME.ExecutionPlan(
            case_id="S14",
            schedule="static",
            operator="test",
            variant="test",
            targets=(),
            references=(),
            mechanisms=(),
            assets=(),
            params={
                "scene_color_mix": 0.32,
                "scene_luminance_factors": (0.72, 0.86, 1.18),
            },
        )
    )
    before = model.geom_rgba[0, :3].copy()
    luminance = float(np.dot(before, [0.2126, 0.7152, 0.0722]))
    expected = 0.68 * before + 0.32 * np.array(
        [0.72 * luminance, 0.86 * luminance, min(1.0, 1.18 * luminance)]
    )
    s14._change_scene_domain(env)
    np.testing.assert_allclose(model.geom_rgba[0, :3], expected)


def test_d17_trigger_distances_are_task_local() -> None:
    plan = RUNTIME.ExecutionPlan(
        case_id="D17",
        schedule="dynamic",
        operator="test",
        variant="test",
        targets=("target", "gripper"),
        references=(),
        mechanisms=(),
        assets=(),
        trigger="grasp_attempt",
        params={
            "interaction_mode": "placement",
            "grasp_distance_m": 0.11,
            "grasp_initial_tolerance_m": 0.02,
            "contact_fallback_distance_m": 0.055,
            "wrapper_fallback_distance_m": 0.105,
        },
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan)
    runtime.previous_action = np.array([0.0, 1.0])
    runtime._saved_poses["target"] = (
        np.array([0.0, 0.0, 0.9]),
        np.array([1.0, 0.0, 0.0, 0.0]),
    )
    data = type(
        "Data",
        (),
        {
            "body_xpos": np.array([[0.0, 0.0, 0.9]]),
            "body_xquat": np.array([[1.0, 0.0, 0.0, 0.0]]),
            "site_xpos": np.array([[0.10, 0.0, 0.9]]),
        },
    )()
    env = type(
        "Env",
        (),
        {
            "obj_body_id": {"target": 0},
            "sim": type("Sim", (), {"data": data})(),
            "robots": [type("Robot", (), {"eef_site_id": 0})()],
        },
    )()

    assert runtime._dynamic_triggered(env, 0)
    runtime.plan.params["wrapper_fallback_distance_m"] = 0.09
    assert not runtime._dynamic_triggered(env, 0)


def test_s18_logs_applied_robot_state_offsets() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan(
            "S18",
            eef_offset_xyz=(0.018, -0.012, 0.009),
            joint_zero_offset_rad=(0.018, -0.015, 0.015),
            grasp_center_offset_xyz=(0.006, -0.004, 0.003),
        )
    )
    observation = {
        "robot0_eef_pos": np.array([0.1, 0.2, 0.3]),
        "robot0_joint_pos": np.zeros(7),
        "robot0_joint_pos_cos": np.ones(7),
        "object_to_robot0_eef_pos": np.array([0.4, 0.5, 0.6]),
    }

    transformed = runtime.transform_observation(observation, 0)

    np.testing.assert_allclose(
        transformed["robot0_eef_pos"], [0.124, 0.184, 0.312]
    )
    np.testing.assert_allclose(
        transformed["robot0_joint_pos"],
        [0.018, -0.015, 0.015, 0.0, 0.0, 0.0, 0.0],
    )
    np.testing.assert_allclose(
        transformed["robot0_joint_pos_cos"],
        [1.018, 0.985, 1.015, 1.0, 1.0, 1.0, 1.0],
    )
    np.testing.assert_allclose(
        transformed["object_to_robot0_eef_pos"], [0.424, 0.484, 0.612]
    )
    applied = runtime.events[-1]["applied_offsets"]
    assert set(applied) == set(observation)
    assert applied["robot0_eef_pos"] == [0.024, -0.016, 0.012]
    assert applied["robot0_joint_pos"] == [
        0.018,
        -0.015,
        0.015,
        0.0,
        0.0,
        0.0,
        0.0,
    ]
