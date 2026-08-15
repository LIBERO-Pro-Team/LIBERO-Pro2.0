from __future__ import annotations

import importlib.util
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ENVS_ROOT = ROOT / "libero" / "libero" / "envs"
ASSET_ROOT = ROOT / "libero" / "libero" / "assets" / "perturbation_assets"
BDDL_ROOT = Path.home() / "Desktop" / "LIBERO-Pro2.0_4Suite_42扰动_BDDL"
PUBLISHED_BDDL_ROOT = ROOT.parent / "assets" / "bddl" / "libero-pro2.0-1680-v1"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ENVS_ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


PARSER = load_module("libero_pro_schema_parser", "perturbation_config.py")
RUNTIME = load_module("libero_pro_nonphysical_runtime", "nonphysical_perturbations.py")


class SchemaExecutionPlanTests(unittest.TestCase):
    def test_repo_d08_declares_one_camera_target(self):
        path = next(
            (
                ROOT.parent
                / "assets"
                / "bddl"
                / "libero-pro2.0-1680-v1"
                / "libero_goal"
                / "02_dynamic"
            ).glob("D08__*.bddl")
        )
        config = PARSER.parse_bddl_perturbation_config(path)
        plan = RUNTIME.build_execution_plan(config, ASSET_ROOT)

        self.assertEqual(plan.case_id, "D08")
        self.assertEqual(plan.targets, ("agentview", "robot0_eye_in_hand"))

    def test_repo_d15_declares_replay_chunk_parameters(self):
        path = next(
            (
                ROOT.parent
                / "assets"
                / "bddl"
                / "libero-pro2.0-1680-v1"
                / "libero_goal"
                / "02_dynamic"
            ).glob("D15__*.bddl")
        )
        config = PARSER.parse_bddl_perturbation_config(path)
        plan = RUNTIME.build_execution_plan(config, ASSET_ROOT)

        self.assertEqual(plan.case_id, "D15")
        self.assertEqual(plan.params["chunk_size"], 4)
        self.assertEqual(plan.params["stale_chunk_steps"], 4)

    def test_generated_ycb_asset_id_survives_bddl_atom_lowercasing(self):
        path = next(
            (
                ROOT.parent
                / "assets"
                / "bddl"
                / "libero-pro2.0-1680-v1"
                / "libero_object"
                / "01_static"
            ).glob("S06__pick_up_the_alphabet_soup_and_place_it_in_the_basket.bddl")
        )
        config = PARSER.parse_bddl_perturbation_config(path)
        plan = RUNTIME.build_execution_plan(config, ASSET_ROOT)

        self.assertEqual(plan.case_id, "S06")
        self.assertEqual([asset.asset_id for asset in plan.assets], ["ycb/YcbTomatoSoupCan"])
        self.assertTrue(plan.assets[0].xml_path.is_file())

    def test_all_published_bddls_resolve_to_an_executable_case(self):
        files = sorted(PUBLISHED_BDDL_ROOT.rglob("*.bddl"))
        self.assertEqual(len(files), 1680)

        seen = set()
        for path in files:
            config = PARSER.parse_bddl_perturbation_config(path)
            plan = RUNTIME.build_execution_plan(config, ASSET_ROOT)
            expected = path.name.split("__", 1)[0]
            self.assertEqual(plan.case_id, expected, path)
            self.assertTrue(plan.mechanisms, path)
            for asset in plan.assets:
                self.assertTrue(asset.xml_path.is_file(), asset.xml_path)
            if expected != "BASE":
                seen.add(expected)

        self.assertEqual(
            seen,
            {f"S{i:02d}" for i in range(1, 22)}
            | {f"D{i:02d}" for i in range(1, 20)}
            | {"D21"},
        )

    def test_only_the_selected_case_is_active(self):
        path = next((BDDL_ROOT / "libero_10" / "01_static").glob("S12__*.bddl"))
        config = PARSER.parse_bddl_perturbation_config(path)
        plan = RUNTIME.build_execution_plan(config, ASSET_ROOT)

        self.assertEqual(plan.case_id, "S12")
        self.assertEqual(plan.operator, "occlusion_or_obstacle")
        self.assertEqual(plan.variant, "persistent_front_occlusion")
        self.assertEqual([asset.asset_id for asset in plan.assets], ["generated/occlusion_screen"])

    def test_dynamic_asset_cases_start_staged_outside_the_workspace(self):
        path = next((BDDL_ROOT / "libero_goal" / "02_dynamic").glob("D04__*.bddl"))
        config = PARSER.parse_bddl_perturbation_config(path)
        plan = RUNTIME.build_execution_plan(config, ASSET_ROOT)

        self.assertEqual(plan.schedule, "dynamic")
        self.assertTrue(plan.assets)
        self.assertTrue(all(asset.staged for asset in plan.assets))

    def test_execution_plan_description_is_stable_and_path_independent(self):
        path = next((BDDL_ROOT / "libero_goal" / "02_dynamic").glob("D04__*.bddl"))
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )

        description = RUNTIME.describe_execution_plan(plan, 142, 24)

        self.assertEqual(description["version"], "libero_nonphysical_plan_v2")
        self.assertEqual(description["case_id"], "D04")
        self.assertEqual(description["seed"], 142)
        self.assertEqual(description["trigger"], "task_phase")
        self.assertEqual(description["event_duration_steps"], 24)
        self.assertNotIn("event_start", description)
        self.assertNotIn("event_end", description)
        self.assertEqual(description["targets"], list(plan.targets))
        self.assertEqual(
            [asset["asset_id"] for asset in description["assets"]],
            [asset.asset_id for asset in plan.assets],
        )
        self.assertNotIn(str(ASSET_ROOT), repr(description))

    def test_s04_uses_suite_specific_planar_swap_pairs(self):
        expected_pairs = {
            "libero_10": ("white_yellow_mug_1", "porcelain_mug_1"),
            "libero_object": ("alphabet_soup_1", "milk_1"),
            "libero_goal": ("wine_bottle_1", "cream_cheese_1"),
            "libero_spatial": ("plate_1", "cookies_1"),
        }
        for suite, expected in expected_pairs.items():
            with self.subTest(suite=suite):
                path = next((BDDL_ROOT / suite / "01_static").glob("S04__*.bddl"))
                plan = RUNTIME.build_execution_plan(
                    PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
                )
                self.assertEqual(plan.variant, "planar_object_position_swap")
                self.assertEqual(plan.targets, expected)


class SceneInjectionTests(unittest.TestCase):
    def test_s12_adds_a_real_mjcf_object_before_scene_compilation(self):
        class FakeAssetObject:
            def __init__(self, xml_path, name, joints):
                self.xml_path = Path(xml_path)
                self.name = name
                self.joints = joints

        path = next((BDDL_ROOT / "libero_10" / "01_static").glob("S12__*.bddl"))
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )
        objects = {"white_yellow_mug_1": object()}

        result = RUNTIME.inject_plan_assets(objects, plan, FakeAssetObject)

        self.assertIn("perturbation_s12_0", objects)
        injected = objects["perturbation_s12_0"]
        self.assertEqual(injected.xml_path, plan.assets[0].xml_path)
        self.assertEqual(injected.joints, None)
        self.assertEqual(result.injected_names, ("perturbation_s12_0",))

    def test_s06_replaces_the_target_with_a_semantically_compatible_asset(self):
        class Original:
            category_name = "wine_bottle"

        class FakeAssetObject:
            def __init__(self, xml_path, name, joints):
                self.xml_path = Path(xml_path)
                self.name = name
                self.joints = joints
                self.category_name = "unset"

        path = next((BDDL_ROOT / "libero_goal" / "01_static").glob("S06__*.bddl"))
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )
        objects = {"wine_bottle_1": Original()}

        result = RUNTIME.inject_plan_assets(objects, plan, FakeAssetObject)

        replacement = objects["wine_bottle_1"]
        self.assertEqual(replacement.category_name, "wine_bottle")
        self.assertEqual(replacement.joints, "default")
        self.assertEqual(result.replaced_names, ("wine_bottle_1",))

    def test_s07_s08_s09_have_distinct_compiled_geometry_contracts(self):
        class Receiver:
            def __init__(self):
                self.asset = ET.fromstring(
                    '<asset><mesh name="mesh" scale="1 1 1" /></asset>'
                )
                self.worldbody = ET.fromstring(
                    '<worldbody><body pos="0 0 0.2">'
                    '<geom size="0.1 0.2 0.3" pos="0 0 0.1" />'
                    '<site size="0.08 0.08 0.1" pos="0 0 0.15" />'
                    "</body></worldbody>"
                )

            def get_obj(self):
                return ET.fromstring(ET.tostring(self.worldbody.find("body")))

        cases = {
            "S07": {
                "objects": {"basket_1": Receiver()},
                "expected": ("basket_1",),
                "mesh": {"basket_1": [1.0, 0.64, 1.20]},
            },
            "S08": {
                "objects": {"alphabet_soup_1": Receiver()},
                "expected": ("alphabet_soup_1",),
                "mesh": {"alphabet_soup_1": [1.35, 0.72, 1.0]},
            },
            "S09": {
                "objects": {
                    "alphabet_soup_1": Receiver(),
                    "basket_1": Receiver(),
                },
                "expected": ("alphabet_soup_1", "basket_1"),
                "mesh": {
                    "alphabet_soup_1": [1.12, 1.12, 1.12],
                    "basket_1": [0.90, 0.90, 0.90],
                },
            },
        }
        for case_id, expected in cases.items():
            with self.subTest(case_id=case_id):
                changed = RUNTIME.apply_precompile_geometry(
                    expected["objects"], {}, self._plan("libero_object", case_id)
                )
                self.assertEqual(changed, expected["expected"])
                for name, scale in expected["mesh"].items():
                    np.testing.assert_allclose(
                        np.fromstring(
                            expected["objects"][name].asset.find("mesh").get("scale"),
                            sep=" ",
                        ),
                        scale,
                    )

        receiver = cases["S09"]["objects"]["basket_1"]
        site = receiver.worldbody.find(".//site")
        np.testing.assert_allclose(
            np.fromstring(site.get("size"), sep=" "), [0.072, 0.072, 0.09]
        )
        np.testing.assert_allclose(
            np.fromstring(site.get("pos"), sep=" "), [0.0, 0.0, 0.135]
        )

    @staticmethod
    def _plan(suite: str, case_id: str):
        folder = "01_static" if case_id.startswith("S") else "02_dynamic"
        path = next((BDDL_ROOT / suite / folder).glob(f"{case_id}__*.bddl"))
        return RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )


class RuntimeBehaviorTests(unittest.TestCase):
    def plan(self, suite: str, folder: str, case_id: str):
        path = next((BDDL_ROOT / suite / folder).glob(f"{case_id}__*.bddl"))
        config = PARSER.parse_bddl_perturbation_config(path)
        return RUNTIME.build_execution_plan(config, ASSET_ROOT)

    def test_static_clutter_and_similar_distractor_use_distinct_anchors(self):
        clutter = self.plan("libero_spatial", "01_static", "S10")
        distractor = self.plan("libero_spatial", "01_static", "S11")

        self.assertEqual(
            RUNTIME._static_asset_reference_name(clutter),
            "glazed_rim_porcelain_ramekin_1",
        )
        self.assertEqual(
            RUNTIME._static_asset_reference_name(distractor),
            "akita_black_bowl_2",
        )

    def test_s19_degrades_rgb_without_mutating_the_simulator_observation(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_10", "01_static", "S19"), seed=7
        )
        image = np.full((32, 32, 3), 128, dtype=np.uint8)
        obs = {"agentview_image": image}

        changed = runtime.transform_observation(obs, step=0)

        self.assertFalse(np.array_equal(changed["agentview_image"], image))
        self.assertTrue(np.all(image == 128))

    def test_runtime_seed_can_be_replayed_for_identical_observation_noise(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_10", "01_static", "S19")
        )
        observation = {"agentview_image": np.full((16, 16, 3), 128, dtype=np.uint8)}

        runtime.set_seed(142)
        first = runtime.transform_observation(observation, step=0)
        runtime.set_seed(142)
        second = runtime.transform_observation(observation, step=0)
        runtime.set_seed(143)
        changed = runtime.transform_observation(observation, step=0)

        np.testing.assert_array_equal(first["agentview_image"], second["agentview_image"])
        self.assertFalse(
            np.array_equal(first["agentview_image"], changed["agentview_image"])
        )

    def test_s14_changes_scene_domain_without_flat_s13_green(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_goal", "01_static", "S14"), seed=7
        )

        class Sim:
            def __init__(self):
                self.model = types.SimpleNamespace(
                    ngeom=2,
                    geom_rgba=np.array(
                        [[0.8, 0.4, 0.2, 1.0], [0.2, 0.6, 0.9, 1.0]], dtype=float
                    ),
                    light_diffuse=np.ones((1, 3), dtype=float),
                    light_ambient=np.full((1, 3), 0.5, dtype=float),
                )

            def forward(self):
                pass

        sim = Sim()
        before = sim.model.geom_rgba.copy()
        env = types.SimpleNamespace(sim=sim)

        changed = runtime._change_scene_domain(env)

        self.assertEqual(changed, 2)
        self.assertFalse(np.array_equal(sim.model.geom_rgba, before))
        self.assertFalse(
            np.allclose(sim.model.geom_rgba[0, :3], np.array([0.18, 0.72, 0.38]))
        )

    def test_s04_swaps_xy_without_changing_height_or_orientation(self):
        plan = RUNTIME.ExecutionPlan(
            case_id="S04",
            schedule="static",
            operator="pose_transform",
            variant="planar_object_position_swap",
            targets=("target", "distractor"),
            references=(),
            mechanisms=("pose",),
            assets=(),
        )
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=7)

        class Sim:
            def __init__(self):
                self.model = types.SimpleNamespace(
                    body_pos=np.array(
                        [[-0.20, -0.10, 0.91], [0.16, 0.22, 0.96]], dtype=float
                    ),
                    body_quat=np.array(
                        [[1.0, 0.0, 0.0, 0.0], [0.9239, 0.0, 0.0, 0.3827]],
                        dtype=float,
                    ),
                )
                self.data = types.SimpleNamespace(
                    body_xpos=self.model.body_pos.copy(),
                    body_xquat=self.model.body_quat.copy(),
                )

            def forward(self):
                self.data.body_xpos[:] = self.model.body_pos
                self.data.body_xquat[:] = self.model.body_quat

        sim = Sim()
        before_positions = sim.data.body_xpos.copy()
        before_quaternions = sim.data.body_xquat.copy()
        env = types.SimpleNamespace(
            obj_body_id={"target": 0, "distractor": 1},
            objects_dict={
                "target": types.SimpleNamespace(joints=None),
                "distractor": types.SimpleNamespace(joints=None),
            },
            sim=sim,
        )

        runtime.apply_static(env)

        np.testing.assert_allclose(sim.data.body_xpos[0, :2], before_positions[1, :2])
        np.testing.assert_allclose(sim.data.body_xpos[1, :2], before_positions[0, :2])
        np.testing.assert_allclose(sim.data.body_xpos[:, 2], before_positions[:, 2])
        np.testing.assert_allclose(sim.data.body_xquat, before_quaternions)
        self.assertEqual(runtime.events[-1]["event"], "planar_object_position_swap")

    def test_d08_camera_dropout_is_bounded_and_restores(self):
        plan = RUNTIME.ExecutionPlan(
            case_id="D08",
            schedule="dynamic",
            operator="observation_fault",
            variant="camera_dropout_then_restore",
            targets=("robot0_eye_in_hand",),
            references=(),
            mechanisms=("observation",),
            assets=(),
            trigger="task_phase",
        )
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=7)
        agentview = np.full((8, 8, 3), 200, dtype=np.uint8)
        wrist = np.full((8, 8, 3), 100, dtype=np.uint8)
        obs = {
            "agentview_image": agentview,
            "robot0_eye_in_hand_image": wrist,
        }
        target = np.array([0.0, 0.0, 0.90])
        data = types.SimpleNamespace(
            body_xpos=np.array([target, [0.30, 0.0, 0.90]]),
            body_xquat=np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)),
            site_xpos=np.array([[0.50, 0.50, 1.10]]),
        )
        env = types.SimpleNamespace(
            obj_body_id={"goal_object": 0, "receiver": 1},
            object_sites_dict={},
            parsed_problem={"goal_state": [["on", "goal_object", "receiver"]]},
            sim=types.SimpleNamespace(data=data),
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )

        runtime.before_simulation_step(env, step=200)
        before = runtime.transform_observation(obs, step=200)
        data.site_xpos[0] = target + np.array([0.0, 0.0, 0.10])
        runtime.before_simulation_step(env, step=201)
        during = runtime.transform_observation(obs, step=201)
        after = runtime.transform_observation(obs, step=225)

        self.assertTrue(np.array_equal(before["agentview_image"], agentview))
        self.assertTrue(np.array_equal(before["robot0_eye_in_hand_image"], wrist))
        self.assertTrue(np.array_equal(during["agentview_image"], agentview))
        self.assertTrue(np.all(during["robot0_eye_in_hand_image"] == 0))
        self.assertTrue(np.array_equal(after["agentview_image"], agentview))
        self.assertTrue(np.array_equal(after["robot0_eye_in_hand_image"], wrist))
        self.assertEqual(runtime.events[-1]["step"], 201)

    def test_d14_triggers_on_task_target_approach_not_rollout_step(self):
        plan = RUNTIME.ExecutionPlan(
            case_id="D14",
            schedule="dynamic",
            operator="timing_or_action_fault",
            variant="command_drop_or_repeat",
            targets=("action",),
            references=(),
            mechanisms=("action_timing",),
            assets=(),
            trigger="task_phase",
        )
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=7)
        target = np.array([0.0, 0.0, 0.90])
        receiver = np.array([0.30, 0.0, 0.90])
        data = types.SimpleNamespace(
            body_xpos=np.array([target, receiver]),
            body_xquat=np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)),
            site_xpos=np.array([[0.50, 0.50, 1.10]]),
        )
        env = types.SimpleNamespace(
            obj_body_id={"goal_object": 0, "receiver": 1},
            object_sites_dict={},
            parsed_problem={"goal_state": [["on", "goal_object", "receiver"]]},
            sim=types.SimpleNamespace(data=data),
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        previous = np.array([0.1, 0, 0, 0, 0, 0, -1.0])
        far_action = np.array([0.8, 0, 0, 0, 0, 0, 1.0])
        trigger_action = np.array([-0.4, 0, 0, 0, 0, 0, -1.0])
        runtime.transform_action(previous, step=0)
        runtime.transform_gripper_force_command(0.25, step=0)

        runtime.before_simulation_step(env, step=300)
        np.testing.assert_array_equal(
            runtime.transform_action(far_action, step=300), far_action
        )

        data.site_xpos[0] = target + np.array([0.0, 0.0, 0.10])
        runtime.before_simulation_step(env, step=301)

        np.testing.assert_array_equal(
            runtime.transform_action(trigger_action, step=301), far_action
        )
        self.assertEqual(runtime.transform_gripper_force_command(0.90, step=301), 0.25)
        self.assertEqual(runtime.events[-1]["event"], "command_drop_repeat")
        self.assertEqual(runtime.events[-1]["step"], 301)

    def test_d15_replays_a_stale_action_chunk_in_order_then_resumes(self):
        plan = RUNTIME.ExecutionPlan(
            case_id="D15",
            schedule="dynamic",
            operator="timing_or_action_fault",
            variant="stale_chunk_late_chunk_or_replan_interrupt",
            targets=("action_chunk", "replan"),
            references=(),
            mechanisms=("action_timing",),
            assets=(),
            trigger="state_change",
            params={"chunk_size": 4, "stale_chunk_steps": 4},
        )
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=7)
        target = np.array([0.0, 0.0, 0.90])

        class Sim:
            def __init__(self):
                self.data = types.SimpleNamespace(
                    body_xpos=np.array([target, [0.30, 0.0, 0.90]], dtype=float),
                    body_xquat=np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)),
                    site_xpos=np.array([[0.50, 0.50, 1.10]], dtype=float),
                )

        sim = Sim()
        env = types.SimpleNamespace(
            obj_body_id={"goal_object": 0, "receiver": 1},
            objects_dict={
                "goal_object": types.SimpleNamespace(joints=None),
                "receiver": types.SimpleNamespace(joints=None),
            },
            object_sites_dict={},
            parsed_problem={"goal_state": [["on", "goal_object", "receiver"]]},
            sim=sim,
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        runtime.apply_static(env)
        old_chunk = [
            np.full(7, value, dtype=np.float64) for value in (0.1, 0.2, 0.3, 0.4)
        ]
        for index, action in enumerate(old_chunk, start=44):
            runtime.before_simulation_step(env, step=index)
            np.testing.assert_array_equal(runtime.transform_action(action, step=index), action)

        sim.data.body_xpos[0] = target + np.array([0.08, 0.0, 0.08])
        sim.data.site_xpos[0] = sim.data.body_xpos[0] + np.array([0.0, 0.0, 0.04])
        runtime.before_simulation_step(env, step=97)
        new_actions = [np.full(7, value, dtype=np.float64) for value in (1.1, 1.2, 1.3, 1.4)]
        replayed = [
            runtime.transform_action(action, step=97 + index)
            for index, action in enumerate(new_actions)
        ]
        for actual, expected in zip(replayed, old_chunk):
            np.testing.assert_array_equal(actual, expected)

        resumed = np.full(7, 2.0, dtype=np.float64)
        np.testing.assert_array_equal(runtime.transform_action(resumed, step=101), resumed)
        self.assertEqual(runtime.events[-1]["event"], "stale_action_chunk")
        self.assertEqual(runtime.events[-1]["chunk_length"], 4)
        self.assertEqual(runtime.events[-1]["step"], 97)

    def test_d17_grasp_failure_window_starts_when_the_event_actually_triggers(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_spatial", "02_dynamic", "D17"), seed=7
        )
        target = runtime.plan.targets[0]
        data = types.SimpleNamespace(
            body_xpos=np.array([[0.4, 0.4, 0.9]]),
            body_xquat=np.array([[1.0, 0.0, 0.0, 0.0]]),
            site_xpos=np.array([[0.4, 0.4, 0.98]]),
        )
        env = types.SimpleNamespace(
            obj_body_id={target: 0},
            sim=types.SimpleNamespace(data=data),
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        runtime.previous_action = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
        runtime.before_simulation_step(env, step=37)

        changed = runtime.transform_action(
            np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]), step=37
        )

        self.assertEqual(changed[-1], -1.0)
        self.assertEqual(runtime.transform_gripper_force_command(0.8, step=37), 0.0)

    def test_d17_does_not_use_a_time_fallback_without_a_grasp_attempt(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_spatial", "02_dynamic", "D17"), seed=7
        )
        target = runtime.plan.targets[0]
        env = types.SimpleNamespace(
            obj_body_id={target: 0},
            sim=types.SimpleNamespace(
                data=types.SimpleNamespace(
                    body_xpos=np.array([[0.4, 0.4, 0.9]]),
                    body_xquat=np.array([[1.0, 0.0, 0.0, 0.0]]),
                    site_xpos=np.array([[0.4, 0.4, 0.98]]),
                )
            ),
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )

        runtime.before_simulation_step(env, step=300)

        self.assertFalse(runtime.events)

    def test_d01_combines_xy_translation_with_yaw_rotation(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_goal", "02_dynamic", "D01"), seed=7
        )
        target = runtime.plan.targets[0]

        class Sim:
            def __init__(self):
                self.model = types.SimpleNamespace(
                    body_pos=np.array([[0.0, 0.0, 0.9]]),
                    body_quat=np.array([[1.0, 0.0, 0.0, 0.0]]),
                )
                self.data = types.SimpleNamespace(
                    body_xpos=self.model.body_pos.copy(),
                    body_xquat=self.model.body_quat.copy(),
                    site_xpos=np.array([[0.05, 0.05, 0.95]]),
                )

            def forward(self):
                self.data.body_xpos[:] = self.model.body_pos
                self.data.body_xquat[:] = self.model.body_quat

        sim = Sim()
        env = types.SimpleNamespace(
            obj_body_id={target: 0},
            objects_dict={target: types.SimpleNamespace(joints=None)},
            workspace_offset=np.array([0.0, 0.0, 0.9]),
            sim=sim,
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        runtime.before_simulation_step(env, step=23)

        self.assertFalse(np.allclose(sim.data.body_xpos[0, :2], [0.0, 0.0]))
        self.assertFalse(np.allclose(sim.data.body_xquat[0], [1.0, 0.0, 0.0, 0.0]))

    def test_d02_moves_wine_rack_across_its_narrow_goal_axis(self):
        delta = RUNTIME._dynamic_pose_requested_delta("D02", "wine_rack_1")

        np.testing.assert_allclose(delta, [0.0, 0.09])
        self.assertGreater(np.linalg.norm(delta), 0.08)

    def test_repo_d02_moves_basket_far_enough_from_a_held_can(self):
        path = next(
            (
                ROOT.parent
                / "assets"
                / "bddl"
                / "libero-pro2.0-1680-v1"
                / "libero_object"
                / "02_dynamic"
            ).glob("D02__*.bddl")
        )
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=7)

        class Sim:
            def __init__(self):
                self.model = types.SimpleNamespace(
                    body_pos=np.array(
                        [
                            [0.01448, 0.25723, 0.9],
                            [0.01448, 0.25723, 0.9],
                        ]
                    ),
                    body_quat=np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)),
                )
                self.data = types.SimpleNamespace(
                    body_xpos=self.model.body_pos.copy(),
                    body_xquat=self.model.body_quat.copy(),
                )

            def forward(self):
                self.data.body_xpos[:] = self.model.body_pos
                self.data.body_xquat[:] = self.model.body_quat

        sim = Sim()
        env = types.SimpleNamespace(
            obj_body_id={"basket_1": 0, "alphabet_soup_1": 1},
            objects_dict={
                "basket_1": types.SimpleNamespace(joints=None),
                "alphabet_soup_1": types.SimpleNamespace(joints=None),
            },
            workspace_offset=np.array([0.0, 0.0, 0.9]),
            sim=sim,
        )
        runtime._dynamic_triggered = lambda env, step: True

        runtime.before_simulation_step(env, step=48)

        np.testing.assert_allclose(plan.params["offset_xy"], [-0.12, 0.09])
        np.testing.assert_allclose(
            runtime.events[-1]["delta_xy"], plan.params["offset_xy"]
        )
        self.assertAlmostEqual(
            np.linalg.norm(
                sim.data.body_xpos[0, :2] - sim.data.body_xpos[1, :2]
            ),
            0.15,
        )

    def test_safe_offset_pose_expands_search_when_primary_offsets_are_blocked(self):
        requested = np.array([-0.055, 0.035])
        primary_offsets = (
            requested,
            np.array([-requested[0], requested[1]]),
            np.array([requested[0], -requested[1]]),
            -requested,
            np.array([requested[1], requested[0]]),
            np.array([-requested[1], -requested[0]]),
        )

        class Sim:
            def __init__(self):
                positions = [np.array([0.0, 0.0, 0.9])]
                positions.extend(
                    np.array([offset[0], offset[1], 0.9])
                    for offset in primary_offsets
                )
                self.model = types.SimpleNamespace(
                    body_pos=np.asarray(positions),
                    body_quat=np.tile([1.0, 0.0, 0.0, 0.0], (7, 1)),
                )
                self.data = types.SimpleNamespace(
                    body_xpos=self.model.body_pos.copy(),
                    body_xquat=self.model.body_quat.copy(),
                )

            def forward(self):
                self.data.body_xpos[:] = self.model.body_pos
                self.data.body_xquat[:] = self.model.body_quat

        sim = Sim()
        names = ["moving"] + [f"blocker_{index}" for index in range(6)]
        env = types.SimpleNamespace(
            obj_body_id={name: index for index, name in enumerate(names)},
            objects_dict={name: types.SimpleNamespace(joints=None) for name in names},
            workspace_offset=np.array([0.0, 0.0, 0.9]),
            sim=sim,
        )

        before, after, applied = RUNTIME._safe_offset_pose(
            env, "moving", tuple(requested)
        )

        np.testing.assert_allclose(before, [0.0, 0.0, 0.9])
        self.assertGreater(np.linalg.norm(applied), np.linalg.norm(requested))
        self.assertTrue(
            RUNTIME._candidate_is_clear(
                env, "moving", after[:2], minimum_gap=0.08
            )
        )

    def test_d18_moves_a_carried_object_to_a_reachable_support_height(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_goal", "02_dynamic", "D18"), seed=7
        )
        target = runtime.plan.targets[0]

        class Sim:
            def __init__(self):
                self.model = types.SimpleNamespace(
                    body_pos=np.array([[0.0, 0.0, 0.9]]),
                    body_quat=np.array([[1.0, 0.0, 0.0, 0.0]]),
                )
                self.data = types.SimpleNamespace(
                    body_xpos=self.model.body_pos.copy(),
                    body_xquat=self.model.body_quat.copy(),
                    site_xpos=np.array([[0.0, 0.0, 1.15]]),
                )

            def forward(self):
                self.data.body_xpos[:] = self.model.body_pos
                self.data.body_xquat[:] = self.model.body_quat

        sim = Sim()
        env = types.SimpleNamespace(
            obj_body_id={target: 0},
            objects_dict={target: types.SimpleNamespace(joints=None)},
            workspace_offset=np.array([0.0, 0.0, 0.9]),
            sim=sim,
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        runtime.apply_static(env)
        runtime.previous_action = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
        sim.model.body_pos[0, 2] = 1.15
        sim.forward()

        runtime.before_simulation_step(env, step=2)

        self.assertAlmostEqual(sim.data.body_xpos[0, 2], 0.9)
        self.assertFalse(np.allclose(sim.data.body_xpos[0, :2], [0.0, 0.0]))

    def test_d18_does_not_use_a_time_fallback_before_transport(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_goal", "02_dynamic", "D18"), seed=7
        )
        target = runtime.plan.targets[0]
        env = types.SimpleNamespace(
            obj_body_id={target: 0},
            objects_dict={target: types.SimpleNamespace(joints=None)},
            object_sites_dict={},
            parsed_problem={"goal_state": []},
            sim=types.SimpleNamespace(
                data=types.SimpleNamespace(
                    body_xpos=np.array([[0.0, 0.0, 0.9]]),
                    body_xquat=np.array([[1.0, 0.0, 0.0, 0.0]]),
                    site_xpos=np.array([[0.0, 0.0, 1.0]]),
                )
            ),
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        runtime.apply_static(env)

        runtime.before_simulation_step(env, step=300)

        self.assertFalse(runtime.events)

    def test_d19_requires_transport_progress_and_receiver_approach(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_goal", "02_dynamic", "D19"), seed=7
        )
        target, receiver = runtime.plan.targets

        class Sim:
            def __init__(self):
                self.model = types.SimpleNamespace(
                    body_pos=np.array([[0.0, 0.0, 0.9], [0.30, 0.0, 0.9]]),
                    body_quat=np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)),
                )
                self.data = types.SimpleNamespace(
                    body_xpos=self.model.body_pos.copy(),
                    body_xquat=self.model.body_quat.copy(),
                    site_xpos=np.array([[0.30, 0.0, 0.98]]),
                )

            def forward(self):
                self.data.body_xpos[:] = self.model.body_pos
                self.data.body_xquat[:] = self.model.body_quat

            def get_site_xpos(self, name):
                return np.array([0.30, 0.0, 0.95])

        sim = Sim()
        site_name = "wine_rack_1_top_region"
        env = types.SimpleNamespace(
            obj_body_id={target: 0, receiver: 1},
            objects_dict={
                target: types.SimpleNamespace(joints=None),
                receiver: types.SimpleNamespace(joints=None),
            },
            object_sites_dict={site_name: types.SimpleNamespace(parent_name=receiver)},
            parsed_problem={"goal_state": [["on", target, site_name]]},
            workspace_offset=np.array([0.0, 0.0, 0.9]),
            sim=sim,
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        runtime.apply_static(env)

        runtime.before_simulation_step(env, step=200)
        self.assertFalse(runtime.events)

        sim.model.body_pos[0, :2] = np.array([0.25, 0.0])
        sim.model.body_pos[0, 2] += 0.08
        sim.forward()
        runtime.before_simulation_step(env, step=201)

        self.assertEqual(runtime.events[-1]["event"], "dynamic_state_change")
        self.assertEqual(runtime.events[-1]["target"], target)
        self.assertLess(sim.data.body_xpos[0, 0], 0.25)
        self.assertGreater(sim.data.body_xpos[0, 2], 0.98)

    def test_dynamic_schedule_can_restart_after_environment_settling(self):
        plan = RUNTIME.ExecutionPlan(
            case_id="D14",
            schedule="dynamic",
            operator="timing_or_action_fault",
            variant="command_drop_or_repeat",
            targets=("action",),
            references=(),
            mechanisms=("action_timing",),
            assets=(),
            trigger="task_phase",
        )
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=7)
        target = np.array([0.0, 0.0, 0.90])
        data = types.SimpleNamespace(
            body_xpos=np.array([target, [0.30, 0.0, 0.90]]),
            body_xquat=np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)),
            site_xpos=np.array([[0.0, 0.0, 1.0]]),
        )
        env = types.SimpleNamespace(
            obj_body_id={"goal_object": 0, "receiver": 1},
            object_sites_dict={},
            parsed_problem={"goal_state": [["on", "goal_object", "receiver"]]},
            sim=types.SimpleNamespace(data=data),
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        previous = np.array([0.1, 0, 0, 0, 0, 0, -1.0])
        current = np.array([0.8, 0, 0, 0, 0, 0, 1.0])
        runtime.transform_action(previous, step=9)
        runtime.before_simulation_step(env, step=10)
        np.testing.assert_array_equal(runtime.transform_action(current, step=10), previous)

        runtime.begin_rollout(env)

        np.testing.assert_array_equal(runtime.transform_action(current, step=10), current)

    def test_d05_resolves_a_direct_on_object_receiver_goal(self):
        plan = RUNTIME.ExecutionPlan(
            case_id="D05",
            schedule="dynamic",
            operator="occlusion_or_obstacle",
            variant="obstacle_enters_path",
            targets=("robot_future_path",),
            references=("plate_1",),
            mechanisms=("asset", "dynamic_pose"),
            assets=(),
        )
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=7)

        class Sim:
            def __init__(self):
                self.model = types.SimpleNamespace(
                    body_pos=np.array(
                        [[-0.2, 0.0, 0.9], [0.2, 0.0, 0.9], [0.0, 0.0, -5.0]]
                    ),
                    body_quat=np.tile([1.0, 0.0, 0.0, 0.0], (3, 1)),
                )
                self.data = types.SimpleNamespace(
                    body_xpos=self.model.body_pos.copy(),
                    body_xquat=self.model.body_quat.copy(),
                    site_xpos=np.array([[-0.2, 0.0, 1.0]]),
                )

            def forward(self):
                self.data.body_xpos[:] = self.model.body_pos
                self.data.body_xquat[:] = self.model.body_quat

        sim = Sim()
        env = types.SimpleNamespace(
            obj_body_id={
                "akita_black_bowl_1": 0,
                "plate_1": 1,
                "perturbation_d05_0": 2,
            },
            objects_dict={
                "akita_black_bowl_1": types.SimpleNamespace(joints=None),
                "plate_1": types.SimpleNamespace(joints=None),
                "perturbation_d05_0": types.SimpleNamespace(joints=None),
            },
            object_sites_dict={},
            parsed_problem={
                "goal_state": [["on", "akita_black_bowl_1", "plate_1"]]
            },
            workspace_offset=np.array([0.0, 0.0, 0.9]),
            sim=sim,
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        runtime.apply_static(env)
        runtime.previous_action = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
        sim.model.body_pos[0, 2] += 0.08
        sim.forward()
        runtime.before_simulation_step(env, step=37)

        self.assertNotEqual(sim.data.body_xpos[2, 2], -5.0)
        self.assertEqual(runtime.events[-1]["anchor"], "plate_1")

    def test_d05_ignores_early_target_motion_without_a_grasp(self):
        plan = RUNTIME.ExecutionPlan(
            case_id="D05",
            schedule="dynamic",
            operator="occlusion_or_obstacle",
            variant="obstacle_enters_path",
            targets=("robot_future_path",),
            references=("basket_1",),
            mechanisms=("asset", "dynamic_pose"),
            assets=(),
        )
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=7)

        class Sim:
            def __init__(self):
                self.model = types.SimpleNamespace(
                    body_pos=np.array(
                        [[0.0, 0.0, 0.9], [0.3, 0.0, 0.9], [0.0, 0.0, -5.0]]
                    ),
                    body_quat=np.tile([1.0, 0.0, 0.0, 0.0], (3, 1)),
                )
                self.data = types.SimpleNamespace(
                    body_xpos=self.model.body_pos.copy(),
                    body_xquat=self.model.body_quat.copy(),
                    site_xpos=np.array([[0.4, 0.4, 1.0]]),
                )

            def forward(self):
                self.data.body_xpos[:] = self.model.body_pos
                self.data.body_xquat[:] = self.model.body_quat

        sim = Sim()
        env = types.SimpleNamespace(
            obj_body_id={
                "alphabet_soup_1": 0,
                "basket_1": 1,
                "perturbation_d05_0": 2,
            },
            objects_dict={
                "alphabet_soup_1": types.SimpleNamespace(joints=None),
                "basket_1": types.SimpleNamespace(joints=None),
                "perturbation_d05_0": types.SimpleNamespace(joints=None),
            },
            object_sites_dict={},
            parsed_problem={
                "goal_state": [["in", "alphabet_soup_1", "basket_1"]]
            },
            workspace_offset=np.array([0.0, 0.0, 0.9]),
            sim=sim,
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )
        runtime.apply_static(env)
        runtime.begin_rollout(env)
        runtime.previous_action = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0])
        sim.model.body_pos[0, 2] += 0.03
        sim.forward()

        runtime.before_simulation_step(env, step=20)

        self.assertFalse(runtime.events)
        self.assertFalse(runtime._dynamic_applied)

    def test_s21_uses_the_audited_equivalent_instruction(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_object", "01_static", "S21"), seed=7
        )
        original = "Pick the alphabet soup and place it in the basket"

        changed = runtime.language_instruction(original, step=0)

        self.assertNotEqual(changed.lower(), original.lower())
        self.assertIn("basket", changed.lower())

    def test_d21_logs_the_event_when_the_runtime_trigger_fires(self):
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_goal", "02_dynamic", "D21"), seed=7
        )
        target = runtime.plan.references[0] if runtime.plan.references else "goal_object"
        data = types.SimpleNamespace(
            body_xpos=np.array([[0.0, 0.0, 0.90], [0.30, 0.0, 0.90]]),
            body_xquat=np.tile([1.0, 0.0, 0.0, 0.0], (2, 1)),
            site_xpos=np.array([[0.0, 0.0, 1.0]]),
        )
        env = types.SimpleNamespace(
            obj_body_id={target: 0, "receiver": 1},
            object_sites_dict={},
            parsed_problem={"goal_state": [["on", target, "receiver"]]},
            sim=types.SimpleNamespace(data=data),
            robots=[types.SimpleNamespace(eef_site_id=0)],
        )

        runtime.before_simulation_step(env, step=83)

        self.assertEqual(runtime.events[-1]["event"], "runtime_language_clarification")
        self.assertEqual(runtime.events[-1]["step"], 83)

    def test_prepare_reset_restores_model_changes_between_episodes(self):
        class Model:
            def __init__(self):
                self.body_pos = np.array([[0.0, 0.0, 0.2]])
                self.body_quat = np.array([[1.0, 0.0, 0.0, 0.0]])
                self.cam_pos = np.array([[1.0, 2.0, 3.0]])
                self.cam_quat = np.array([[1.0, 0.0, 0.0, 0.0]])
                self.cam_fovy = np.array([45.0])
                self.geom_rgba = np.array([[0.5, 0.6, 0.7, 1.0]])
                self.light_diffuse = np.array([[0.8, 0.8, 0.8]])
                self.light_ambient = np.array([[0.2, 0.2, 0.2]])

        model = Model()
        env = types.SimpleNamespace(sim=types.SimpleNamespace(model=model))
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_goal", "02_dynamic", "D07"), seed=7
        )
        runtime.prepare_reset(env)
        baseline = model.cam_pos.copy()

        model.body_pos[:] += 2.0
        model.cam_pos[:] += 1.0
        model.cam_fovy[:] *= 1.2
        model.geom_rgba[:] = 0.0
        model.light_diffuse[:] *= 0.5
        model.light_ambient[:] *= 0.5
        runtime.prepare_reset(env)

        np.testing.assert_array_equal(model.body_pos, [[0.0, 0.0, 0.2]])
        np.testing.assert_array_equal(model.cam_pos, baseline)
        np.testing.assert_array_equal(model.cam_fovy, [45.0])
        np.testing.assert_array_equal(model.geom_rgba, [[0.5, 0.6, 0.7, 1.0]])
        np.testing.assert_array_equal(model.light_diffuse, [[0.8, 0.8, 0.8]])
        np.testing.assert_array_equal(model.light_ambient, [[0.2, 0.2, 0.2]])

    def test_reset_baseline_is_recaptured_after_fixture_placement(self):
        class Model:
            def __init__(self):
                self.body_pos = np.zeros((1, 3), dtype=float)
                self.body_quat = np.array([[1.0, 0.0, 0.0, 0.0]])
                self.cam_pos = np.zeros((1, 3), dtype=float)
                self.cam_quat = np.array([[1.0, 0.0, 0.0, 0.0]])
                self.cam_fovy = np.array([45.0])
                self.geom_rgba = np.ones((1, 4), dtype=float)
                self.light_diffuse = np.ones((1, 3), dtype=float)
                self.light_ambient = np.ones((1, 3), dtype=float)

        model = Model()
        env = types.SimpleNamespace(sim=types.SimpleNamespace(model=model))
        runtime = RUNTIME.NonPhysicalPerturbationRuntime(
            self.plan("libero_goal", "00_base", "BASE"), seed=7
        )
        runtime.prepare_reset(env)

        placed_fixture_pose = np.array([[0.18, -0.27, 0.905]])
        model.body_pos[:] = placed_fixture_pose
        runtime.capture_model_baseline(env)
        model.body_pos[:] = np.array([[0.0, 0.0, -5.0]])

        runtime.prepare_reset(env)

        np.testing.assert_array_equal(model.body_pos, placed_fixture_pose)


if __name__ == "__main__":
    unittest.main()
