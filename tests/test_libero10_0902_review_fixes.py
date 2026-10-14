import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LIBERO10 = (
    ROOT
    / "assets"
    / "bddl"
    / "libero-pro2.0-1680-v1"
    / "libero_10"
)
TASK2_NAME = "KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it.bddl"
RUNTIME_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "nonphysical_perturbations.py"
)
SPEC = importlib.util.spec_from_file_location("_libero10_0902_runtime", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)


def _case_block(text: str, case_id: str) -> str:
    marker = f"      ({case_id}\n"
    start = text.index(marker) + 6
    depth = 0
    for index in range(start, len(text)):
        depth += text[index] == "("
        depth -= text[index] == ")"
        if depth == 0:
            return text[start : index + 1]
    raise AssertionError(f"unterminated {case_id} block")


def _task2_d03_runtime() -> object:
    plan = RUNTIME.ExecutionPlan(
        case_id="D03",
        schedule="dynamic",
        operator="occlusion_or_obstacle",
        variant="persistent_triggered_receiver_occupation",
        targets=("flat_stove_1",),
        references=("chefmate_8_frypan_1",),
        mechanisms=("asset", "dynamic_pose"),
        assets=(),
        trigger="preplace",
        params={
            "receiver_trigger_distance_m": 0.32,
            "require_grasp_for_trigger": True,
        },
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=142)
    runtime.previous_action = np.array([0.0, 0.0, 0.0, 1.0])
    runtime._saved_poses["moka_pot_1"] = (
        np.array([0.0, 0.0, 0.90]),
        np.array([1.0, 0.0, 0.0, 0.0]),
    )
    return runtime


def _task2_d03_env(grasped: bool) -> SimpleNamespace:
    positions = np.array(
        [
            [0.15, 0.0, 0.95],
            [0.20, 0.0, 0.90],
        ],
        dtype=np.float64,
    )
    target = SimpleNamespace(name="moka_pot_1")
    gripper = SimpleNamespace(name="gripper")
    data = SimpleNamespace(
        body_xpos=positions,
        body_xquat=np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)),
        site_xpos=np.array([[0.20, 0.0, 1.00]], dtype=np.float64),
        get_site_xpos=lambda _name: np.array([0.20, 0.0, 0.90]),
    )
    return SimpleNamespace(
        obj_body_id={"moka_pot_1": 0, "flat_stove_1": 1},
        objects_dict={"moka_pot_1": target},
        object_sites_dict={
            "flat_stove_1_cook_region": SimpleNamespace(
                parent_name="flat_stove_1"
            )
        },
        parsed_problem={
            "goal_state": [
                ["On", "moka_pot_1", "flat_stove_1_cook_region"],
            ],
            "regions": {
                "flat_stove_1_cook_region": {"target": "flat_stove_1"}
            },
        },
        robots=[SimpleNamespace(eef_site_id=0, gripper=gripper)],
        sim=SimpleNamespace(data=data),
        _check_grasp=lambda actual_gripper, actual_target: (
            actual_gripper is gripper and actual_target is target and grasped
        ),
    )


def test_task2_d03_requires_a_real_grasp_before_triggering() -> None:
    runtime = _task2_d03_runtime()

    assert not runtime._dynamic_triggered(_task2_d03_env(grasped=False), 1)


def test_task2_d03_triggers_after_the_moka_pot_is_really_grasped() -> None:
    runtime = _task2_d03_runtime()

    assert runtime._dynamic_triggered(_task2_d03_env(grasped=True), 1)


def test_task2_d03_does_not_trigger_while_the_gripper_is_open() -> None:
    runtime = _task2_d03_runtime()
    runtime.previous_action[-1] = -1.0

    assert not runtime._dynamic_triggered(_task2_d03_env(grasped=True), 1)


def test_other_d03_tasks_keep_the_existing_trigger_behavior_by_default() -> None:
    runtime = _task2_d03_runtime()
    runtime.plan.params.pop("require_grasp_for_trigger")

    assert runtime._dynamic_triggered(_task2_d03_env(grasped=False), 1)


def test_only_task2_d03_requires_a_real_grasp_for_its_trigger() -> None:
    target = LIBERO10 / "02_dynamic" / f"D03__{TASK2_NAME}"
    enabled = []
    for path in (
        ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
    ).rglob("*.bddl"):
        if "(:require_grasp_for_trigger true)" in path.read_text(encoding="utf-8"):
            enabled.append(path)

    assert enabled == [target]


def test_task2_d05_obstacle_overlaps_the_transport_corridor() -> None:
    path = LIBERO10 / "02_dynamic" / f"D05__{TASK2_NAME}"
    text = path.read_text(encoding="utf-8")
    block = _case_block(text, "D05")

    assert "(:active_cases D05)" in text
    assert "(:lateral_offset_m 0.030)" in block
    assert "(:physical_collision true)" in block
    assert "(:visual_only_asset false)" in block


def test_task2_s11_uses_only_the_reviewed_same_class_distractor() -> None:
    path = LIBERO10 / "01_static" / f"S11__{TASK2_NAME}"
    text = path.read_text(encoding="utf-8")
    active = _case_block(text, "S11")
    inactive_s06 = _case_block(text, "S06")

    assert "(:active_cases S11)" in text
    assert "(:asset_id libero/yellow_moka_pot)" in active
    assert "(:asset_scale 1.0)" in active
    assert "(:movable_asset true)" in active
    assert "(:physical_collision true)" in active
    assert "(:clear_of_task_entities true)" in active
    assert "(:asset_id prl/gelatin_box)" in inactive_s06
    assert "(:asset_scale 0.7)" in inactive_s06
