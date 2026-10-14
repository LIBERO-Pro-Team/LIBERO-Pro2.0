from __future__ import annotations

import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FIXER_PATH = ROOT / "scripts" / "apply_feedback_task_fixes.py"
FIXER_SPEC = importlib.util.spec_from_file_location("_task_level_fixer", FIXER_PATH)
assert FIXER_SPEC is not None and FIXER_SPEC.loader is not None
FIXER = importlib.util.module_from_spec(FIXER_SPEC)
sys.modules[FIXER_SPEC.name] = FIXER
FIXER_SPEC.loader.exec_module(FIXER)

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


def test_s11_fixture_distractor_uses_declared_fixture_without_injected_asset() -> None:
    plan = RUNTIME.ExecutionPlan(
        case_id="S11",
        schedule="static",
        operator="test",
        variant="test",
        targets=("yellow_cabinet_2",),
        references=("wooden_cabinet_1",),
        mechanisms=(),
        assets=(),
        trigger="reset",
        params={
            "fixture_distractor": True,
            "fixture_distractor_targets": "yellow_cabinet_2",
        },
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan)
    env = SimpleNamespace(obj_body_id={"yellow_cabinet_2": 1})

    runtime.apply_static(env)

    assert runtime.events == [
        {
            "case_id": "S11",
            "event": "static_fixture_distractor_present",
            "step": 0,
            "targets": ["yellow_cabinet_2"],
        }
    ]


def test_task_local_clutter_clearance_can_include_task_entities() -> None:
    default = _plan("S10")
    default = RUNTIME.ExecutionPlan(
        **{
            **default.__dict__,
            "targets": ("target",),
            "references": ("reference",),
        }
    )
    strict = RUNTIME.ExecutionPlan(
        **{
            **default.__dict__,
            "params": {"clear_of_task_entities": True},
        }
    )

    assert {"target", "reference"} <= set(
        RUNTIME._clutter_clearance_ignored(default, "asset", ("placed",), ("table",))
    )
    assert {"target", "reference"}.isdisjoint(
        RUNTIME._clutter_clearance_ignored(strict, "asset", ("placed",), ("table",))
    )


def test_grounded_s04_tasks_keep_declared_supports_available_for_grounding() -> None:
    dataset = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
    grounded = []
    missing = []
    for path in dataset.rglob("S04__*.bddl"):
        text = path.read_text(encoding="utf-8")
        if "(:grounded_swap true)" not in text:
            continue
        grounded.append(path)
        if "(:ground_support_from_declared_surface true)" not in text:
            missing.append(path.relative_to(dataset).as_posix())

    assert len(grounded) == 20
    assert missing == []


def test_libero10_task2_s04_uses_collision_safe_grounded_swap() -> None:
    path = (
        ROOT
        / "assets"
        / "bddl"
        / "libero-pro2.0-1680-v1"
        / "libero_10"
        / "01_static"
        / "S04__KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it.bddl"
    )
    text = path.read_text(encoding="utf-8")
    _, _, block = FIXER.case_slice(text, "S04")

    assert "(:grounded_swap true)" in block
    assert "(:ground_support_from_declared_surface true)" in block
    assert "(:swap_cluster_radius_m 0.18)" in block
    assert "(:support_surface kitchen_table)" in block


def test_goal_task0_s11_uses_a_movable_rigid_yellow_cabinet_asset() -> None:
    path = (
        ROOT
        / "assets"
        / "bddl"
        / "libero-pro2.0-1680-v1"
        / "libero_goal"
        / "01_static"
        / "S11__open_the_middle_drawer_of_the_cabinet.bddl"
    )
    text = path.read_text(encoding="utf-8")
    _, _, block = FIXER.case_slice(text, "S11")

    assert "yellow_cabinet_2 - yellow_cabinet" not in text
    assert "(On yellow_cabinet_2 " not in text
    assert "(:targets wooden_cabinet_1)" in block
    assert "(:asset_id libero/yellow_cabinet)" in block
    assert "(:movable_asset true)" in block
    assert "(:physical_collision true)" in block
    assert "(:weld_internal_asset_joints true)" in block
    assert "(:weld_asset_joints true)" not in block
    assert "(:clutter_offsets_xy -0.067791 0.639295)" in block


def test_asset_joint_welding_removes_internal_stateful_joints() -> None:
    root = ET.fromstring(
        "<body><body><joint name='drawer'/><geom type='box' size='1 1 1'/></body></body>"
    )
    calls = []

    class FakeObject:
        category_name = ""
        rotation = (0.0, 0.0)
        rotation_axis = "z"
        object_properties = {}

        def __init__(self):
            self.joints = []

        def get_obj(self):
            return root

    def factory(path, *, name, joints):
        calls.append((path, name, joints))
        return FakeObject()

    plan = RUNTIME.ExecutionPlan(
        case_id="S11",
        schedule="static",
        operator="asset_or_appearance",
        variant="same_class_or_visually_similar_distractor",
        targets=("wooden_cabinet_1",),
        references=("wooden_cabinet_1",),
        mechanisms=("asset",),
        assets=(
            RUNTIME.AssetSpec(
                "libero/yellow_cabinet",
                ROOT / "yellow_cabinet.xml",
                staged=False,
            ),
        ),
        params={"weld_asset_joints": True},
    )

    result = RUNTIME.inject_plan_assets({}, plan, factory)

    assert result.injected_names == ("perturbation_s11_0",)
    assert calls[0][2] is None
    assert root.findall(".//joint") == []


def test_object_task9_s06_keeps_the_original_sampling_envelope() -> None:
    path = (
        ROOT
        / "assets"
        / "bddl"
        / "libero-pro2.0-1680-v1"
        / "libero_object"
        / "01_static"
        / "S06__pick_up_the_orange_juice_and_place_it_in_the_basket.bddl"
    )
    text = path.read_text(encoding="utf-8")
    _, _, block = FIXER.case_slice(text, "S06")

    assert "(:asset_id prl/cracker_box)" in block
    assert "(:asset_scale 0.7)" in block
    assert "(:sampler_compatible true)" in block
    assert "(:grounded_replacement true)" in block
    assert "(:support_surface floor)" in block


def _object_case_block(folder: str, case_id: str, object_name: str) -> str:
    path = (
        ROOT
        / "assets"
        / "bddl"
        / "libero-pro2.0-1680-v1"
        / "libero_object"
        / folder
        / f"{case_id}__pick_up_the_{object_name}_and_place_it_in_the_basket.bddl"
    )
    text = path.read_text(encoding="utf-8")
    _, _, block = FIXER.case_slice(text, case_id)
    return block


def test_object_review_feedback_keeps_d02_original_and_strengthens_reviewed_bddls() -> None:
    d02_task0 = _object_case_block("02_dynamic", "D02", "alphabet_soup")
    assert "(:offset_xy -0.12 0.09)" in d02_task0
    assert "(:yaw_rad -0.24)" in d02_task0
    assert "(:receiver_trigger_distance_m" not in d02_task0

    for object_name in (
        "alphabet_soup",
        "cream_cheese",
        "salad_dressing",
        "bbq_sauce",
        "ketchup",
        "tomato_sauce",
        "butter",
        "milk",
        "chocolate_pudding",
        "orange_juice",
    ):
        s02_block = _object_case_block("01_static", "S02", object_name)
        assert "(:offset_xy -0.12 0.09)" in s02_block
        assert "(:yaw_rad -0.30)" in s02_block

    expected_distances = {
        "alphabet_soup": "0.28",
        "cream_cheese": "0.34",
    }
    for object_name, distance in expected_distances.items():
        d03_block = _object_case_block("02_dynamic", "D03", object_name)
        assert f"(:receiver_trigger_distance_m {distance})" in d03_block
        assert "(:references none)" in d03_block
        assert "(:persistent_movable_asset true)" in d03_block
        assert "(:asset_id prl/plastic_plate)" in d03_block
        assert "(:asset_scale 0.85)" in d03_block
        assert "(:asset_offset_xyz 0.0 0.0 0.10)" in d03_block
        assert "(:persistent_existing_obstacle true)" not in d03_block
        assert "(:event_duration_steps" not in d03_block

    d03_task2 = _object_case_block("02_dynamic", "D03", "salad_dressing")
    assert "(:receiver_trigger_distance_m 0.28)" in d03_task2
    assert "(:references none)" in d03_task2
    assert "(:persistent_movable_asset true)" in d03_task2
    assert "(:asset_id prl/plastic_plate)" in d03_task2
    assert "(:asset_scale 0.85)" in d03_task2
    assert "(:asset_offset_xyz 0.0 0.0 0.10)" in d03_task2
    assert "(:persistent_existing_obstacle true)" not in d03_task2
    assert "(:event_duration_steps" not in d03_task2

    for object_name in ("cream_cheese", "salad_dressing"):
        s05_block = _object_case_block("01_static", "S05", object_name)
        assert "(:barrier_scale 1.35)" in s05_block
        assert "(:barrier_path_fraction 0.50)" in s05_block
        assert "(:barrier_lateral_offset_m -0.07)" in s05_block
        assert "(:visual_only_asset false)" in s05_block


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


def test_d12_delay_steps_controls_observation_during_the_event() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D12", delay_steps=2, event_duration_steps=3)
    )
    runtime._dynamic_event_step = 0

    observations = [
        runtime.transform_observation({"state": np.array([value])}, step)["state"]
        for step, value in enumerate((1, 2, 3))
    ]

    assert [item.tolist() for item in observations] == [[1], [2], [1]]
    assert runtime.events[-1]["delay_steps"] == 2


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


def test_d14_repeat_count_eight_has_an_eight_step_event_window() -> None:
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D14", drop_count=0, repeat_count=8, event_duration_steps=8)
    )
    runtime.transform_action(np.array([9.0, 0.0]), -1)
    runtime._dynamic_event_step = 0

    repeated = [
        runtime.transform_action(np.array([float(step), 0.0]), step)
        for step in range(8)
    ]
    restored = runtime.transform_action(np.array([8.0, 0.0]), 8)

    for action in repeated:
        np.testing.assert_array_equal(action, [9.0, 0.0])
    np.testing.assert_array_equal(restored, [8.0, 0.0])


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


def test_receiver_trigger_distance_keeps_defaults_and_allows_task_local_early_trigger() -> None:
    default_d02 = RUNTIME.NonPhysicalPerturbationRuntime(_plan("D02"))
    default_d05 = RUNTIME.NonPhysicalPerturbationRuntime(_plan("D05"))
    early_d02 = RUNTIME.NonPhysicalPerturbationRuntime(
        _plan("D02", receiver_trigger_distance_m=0.24)
    )

    assert default_d02._receiver_trigger_distance_m("D02") == 0.16
    assert default_d05._receiver_trigger_distance_m("D05") == 0.18
    assert early_d02._receiver_trigger_distance_m("D02") == 0.24


def test_functional_anchor_allows_task_local_receiver_site_override() -> None:
    sites = {
        "cabinet_top": SimpleNamespace(parent_name="cabinet"),
        "cabinet_middle": SimpleNamespace(parent_name="cabinet"),
    }
    positions = {
        "cabinet_top": np.array([0.0, -0.2, 1.1]),
        "cabinet_middle": np.array([0.0, -0.2, 1.0]),
    }
    env = SimpleNamespace(
        object_sites_dict=sites,
        parsed_problem={"goal_state": [], "regions": {}},
        sim=SimpleNamespace(
            data=SimpleNamespace(get_site_xpos=lambda name: positions[name])
        ),
    )

    default_position, default_name = RUNTIME._functional_anchor(env, "cabinet")
    override_position, override_name = RUNTIME._functional_anchor(
        env, "cabinet", "cabinet_middle"
    )

    assert default_name == "cabinet_top"
    np.testing.assert_array_equal(default_position, positions["cabinet_top"])
    assert override_name == "cabinet_middle"
    np.testing.assert_array_equal(override_position, positions["cabinet_middle"])


def test_goal_d03_tasks_use_persistent_receiver_obstacles() -> None:
    parser_path = (
        ROOT
        / "simulator-source"
        / "libero"
        / "libero"
        / "envs"
        / "perturbation_config.py"
    )
    parser_spec = importlib.util.spec_from_file_location(
        "_d03_asset_parser", parser_path
    )
    assert parser_spec is not None and parser_spec.loader is not None
    parser = importlib.util.module_from_spec(parser_spec)
    sys.modules[parser_spec.name] = parser
    parser_spec.loader.exec_module(parser)

    manifest = json.loads(
        (ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8")
    )
    by_task = {
        int(item["base_task_id"]): ROOT / "assets" / item["bddl_path"]
        for item in manifest["tasks"]
        if item["suite"] == "libero_goal" and item["case_id"] == "D03"
    }
    asset_root = (
        ROOT
        / "simulator-source"
        / "libero"
        / "libero"
        / "assets"
        / "perturbation_assets"
    )

    task2 = RUNTIME.build_execution_plan(
        parser.parse_bddl_perturbation_config(by_task[2]), asset_root
    )
    task1 = RUNTIME.build_execution_plan(
        parser.parse_bddl_perturbation_config(by_task[1]), asset_root
    )

    assert len(task2.assets) == 1
    assert task2.assets[0].asset_id == "prl/plastic_plate"
    assert task2.assets[0].scale == 0.75
    assert task2.references == ()
    assert task2.params["persistent_movable_asset"] is True
    assert len(task1.assets) == 1
    assert task1.assets[0].asset_id == "prl/plastic_plate"
    assert task1.assets[0].scale == 0.55
    assert task1.references == ()
    assert task1.params["persistent_movable_asset"] is True


def test_object_task0_feedback_strength_values_are_task_local() -> None:
    d03, _ = FIXER.task_params("libero_object", 0, "D03")
    d05, _ = FIXER.task_params("libero_object", 0, "D05")
    s05, _ = FIXER.task_params("libero_object", 0, "S05")
    s10, _ = FIXER.task_params("libero_object", 0, "S10")

    assert d03 == {}
    assert d05["lateral_offset_m"] == ("0.0",)
    assert d05["barrier_height_m"] == ("0.08",)
    assert d05["asset_scale"] == ("1.35",)
    assert d05["visual_only_asset"] == ("false",)
    assert d05["physical_collision"] == ("true",)
    assert s05["barrier_scale"] == ("1.35",)
    assert s05["barrier_path_fraction"] == ("0.50",)
    assert s05["barrier_lateral_offset_m"] == ("-0.07",)
    assert s05["visual_only_asset"] == ("false",)
    assert s10["asset_count"] == ("3",)
    assert s10["clutter_minimum_gap_m"] == ("0.055",)


def test_latest_nonspatial_review_values_are_task_local() -> None:
    task0_s05, _ = FIXER.task_params("libero_10", 0, "S05")
    task1_d03, _ = FIXER.task_params("libero_10", 1, "D03")
    task1_d05, _ = FIXER.task_params("libero_10", 1, "D05")
    task1_d20, _ = FIXER.task_params("libero_10", 1, "D20")
    task1_s06, _ = FIXER.task_params("libero_10", 1, "S06")
    task1_s10, _ = FIXER.task_params("libero_10", 1, "S10")
    task5_d03, _ = FIXER.task_params("libero_10", 5, "D03")
    task9_d03, _ = FIXER.task_params("libero_10", 9, "D03")
    task5_d13, _ = FIXER.task_params("libero_10", 5, "D13")
    task0_d20, _ = FIXER.task_params("libero_10", 0, "D20")
    task2_d20, _ = FIXER.task_params("libero_10", 2, "D20")
    task5_s09, _ = FIXER.task_params("libero_10", 5, "S09")

    assert task0_s05["barrier_scale"] == ("1.15",)
    assert task0_s05["barrier_path_fraction"] == ("0.50",)
    assert task1_d03 == {}
    assert task1_d05["barrier_path_fraction"] == ("0.50",)
    assert task1_d05["lateral_offset_m"] == ("0.055",)
    assert task1_d20["joint_delta_rad"] == ("0.14",)
    assert task1_d20["min_eef_displacement_m"] == ("0.05",)
    assert task1_s06["asset_scale"] == ("0.55",)
    assert task1_s10["asset_count"] == ("3",)
    assert task1_s10["clutter_offsets_xy"] == (
        "0.11",
        "-0.10",
        "0.11",
        "0.10",
        "-0.11",
        "0.10",
    )
    assert task5_d03 == {}
    assert task9_d03 == {}
    assert task5_d13["arm_delay_steps"] == ("8",)
    assert task5_d13["gripper_delay_steps"] == ("8",)
    assert task0_d20["trigger_eef_motion_m"] == ("0.01",)
    assert task0_d20["trigger_action_norm"] == ("0.01",)
    assert "trigger_eef_motion_m" not in task2_d20
    assert task5_s09["target_geometry_factors"] == ("1.20", "1.20", "1.20")
    assert task5_s09["receiver_geometry_factors"] == ("0.80", "0.80", "0.80")


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
