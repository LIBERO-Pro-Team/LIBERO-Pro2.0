from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
ENVS = ROOT / "simulator-source" / "libero" / "libero" / "envs"
TASK_NAME = "pick_up_the_black_bowl_on_the_cookie_box_and_place_it_on_the_plate"
BDDL = (
    ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
    / "libero_spatial" / "01_static" / f"S04__{TASK_NAME}.bddl"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME = _load("_task3_cookie_swap_runtime", ENVS / "nonphysical_perturbations.py")
PARSER = _load("_task3_cookie_swap_parser", ENVS / "perturbation_config.py")


def _config(case_id: str = "S04"):
    config = PARSER.parse_bddl_perturbation_config(BDDL)
    config["active_cases"] = case_id
    config["case_id"] = case_id
    entry = next(e for e in config["perturbations"] if str(e[0]).upper() == case_id)
    params = next(field["params"] for field in entry[1:] if "params" in field)
    params.update(
        swap_single_support_group=True,
        support_object="cookies_1",
        support_ground_surface="wooden_cabinet_1",
        second_ground_surface="main_table",
        group_minimum_clearance_m=0.018,
    )
    return config, params


@pytest.mark.parametrize(
    "field,value,case_id",
    [
        ("source_suite", "libero_goal", "S04"),
        ("source_task", "pick_up_the_black_bowl_on_the_ramekin_and_place_it_on_the_plate", "S04"),
        ("source_suite", "libero_spatial", "S01"),
    ],
)
def test_cookie_swap_opt_in_rejects_other_tasks_before_execution(field, value, case_id):
    config, _ = _config(case_id)
    config[field] = value
    with pytest.raises(RUNTIME.PerturbationConfigurationError, match="task3/S04"):
        RUNTIME.build_execution_plan(config, RUNTIME.default_asset_root())


def test_cookie_swap_is_disabled_without_explicit_opt_in():
    config, params = _config()
    params.pop("swap_single_support_group")
    baseline = RUNTIME.build_execution_plan(config, RUNTIME.default_asset_root())
    disabled = copy.deepcopy(config)
    entry = next(e for e in disabled["perturbations"] if str(e[0]).upper() == "S04")
    next(field["params"] for field in entry[1:] if "params" in field)[
        "swap_single_support_group"
    ] = False
    plan = RUNTIME.build_execution_plan(disabled, RUNTIME.default_asset_root())
    assert plan.targets == baseline.targets
    assert plan.mechanisms == baseline.mechanisms
    assert not plan.params["swap_single_support_group"]


def _scene(monkeypatch, config):
    identity = np.array([1.0, 0.0, 0.0, 0.0])
    poses = {
        "akita_black_bowl_1": (np.array([0.07, 0.03, 0.94]), identity.copy()),
        "akita_black_bowl_2": (np.array([0.02, -0.28, 1.14]), identity.copy()),
        "cookies_1": (np.array([0.06, 0.03, 0.91]), identity.copy()),
        "wooden_cabinet_1": (np.array([0.02, -0.28, 0.90]), identity.copy()),
        "plate_1": (np.array([0.05, 0.20, 0.90]), identity.copy()),
        "main_table": (np.array([0.0, 0.0, 0.90]), identity.copy()),
    }
    before = copy.deepcopy(poses)
    touched = []
    env = SimpleNamespace(
        parsed_problem={"perturbation_config": config},
        sim=SimpleNamespace(data=SimpleNamespace(qvel=np.arange(18, dtype=float))),
    )
    env.sim.forward = lambda: None
    monkeypatch.setattr(RUNTIME, "_entity_exists", lambda env, name: name in poses)
    monkeypatch.setattr(RUNTIME, "_entity_pose", lambda env, name: copy.deepcopy(poses[name]))

    def set_pose(env, name, position, quaternion):
        touched.append(name)
        poses[name] = (position.copy(), quaternion.copy())

    def grounded(env, name, xy, params, ignored=()):
        surface = params["support_surface"]
        if isinstance(surface, list):
            surface = "wooden_cabinet_1" if xy[1] < 0 else "main_table"
        z = 1.14 if surface == "wooden_cabinet_1" else 0.90
        return np.array([xy[0], xy[1], z]), surface + "_support"

    monkeypatch.setattr(RUNTIME, "_set_entity_pose", set_pose)
    monkeypatch.setattr(RUNTIME, "_grounded_entity_position", grounded)
    monkeypatch.setattr(RUNTIME, "_candidate_is_clear", lambda *args, **kwargs: True)
    monkeypatch.setattr(RUNTIME, "_entity_deep_contacts", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        RUNTIME, "_support_geom_belongs_to_entity", lambda env, geom, name: geom == name + "_support"
    )
    monkeypatch.setattr(RUNTIME, "_zero_entity_free_joint_velocity", lambda env, name: None)
    return env, poses, before, touched


def test_cookie_swap_keeps_target_on_box_and_only_moves_three_objects(monkeypatch):
    config, _ = _config()
    plan = RUNTIME.build_execution_plan(config, RUNTIME.default_asset_root())
    env, poses, before, touched = _scene(monkeypatch, config)
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan)
    runtime.apply_static(env)

    first, second, box = "akita_black_bowl_1", "akita_black_bowl_2", "cookies_1"
    np.testing.assert_allclose(poses[first][0][:2], before[second][0][:2])
    np.testing.assert_allclose(poses[second][0][:2], before[first][0][:2])
    np.testing.assert_allclose(poses[first][0] - poses[box][0], before[first][0] - before[box][0])
    assert poses[box][0][2] == 1.14
    assert poses[second][0][2] == 0.90
    assert set(touched) == {first, second, box}
    for name in poses:
        np.testing.assert_array_equal(poses[name][1], before[name][1])
        if name not in {first, second, box}:
            np.testing.assert_array_equal(poses[name][0], before[name][0])
    assert runtime.diagnostics()["events"][0]["event"] == "single_support_group_swap"


@pytest.mark.parametrize("failure", ["penetration", "velocity_reset"])
def test_cookie_swap_restores_poses_and_velocities_on_failure(monkeypatch, failure):
    config, _ = _config()
    plan = RUNTIME.build_execution_plan(config, RUNTIME.default_asset_root())
    env, poses, before, touched = _scene(monkeypatch, config)
    before_qvel = env.sim.data.qvel.copy()

    def contacts(env, name):
        if failure == "penetration" and touched:
            return [{"first": name, "second": "cabinet", "depth_m": 0.01}]
        return []

    def reset_velocity(env, name):
        env.sim.data.qvel[:] = 0.0
        raise RUNTIME.PerturbationValidationError("velocity reset failed")

    monkeypatch.setattr(RUNTIME, "_entity_deep_contacts", contacts)
    if failure == "velocity_reset":
        monkeypatch.setattr(RUNTIME, "_zero_entity_free_joint_velocity", reset_velocity)
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan)
    with pytest.raises(RUNTIME.PerturbationValidationError):
        runtime.apply_static(env)
    for name in poses:
        np.testing.assert_array_equal(poses[name][0], before[name][0])
        np.testing.assert_array_equal(poses[name][1], before[name][1])
    np.testing.assert_array_equal(env.sim.data.qvel, before_qvel)
    assert not runtime.diagnostics()["events"]


def test_cookie_swap_checks_source_again_when_executed_directly(monkeypatch):
    config, _ = _config()
    plan = RUNTIME.build_execution_plan(config, RUNTIME.default_asset_root())
    env, _, _, touched = _scene(monkeypatch, config)
    env.parsed_problem["perturbation_config"]["source_suite"] = "libero_10"
    with pytest.raises(RUNTIME.PerturbationConfigurationError, match="task3/S04"):
        RUNTIME.NonPhysicalPerturbationRuntime(plan).apply_static(env)
    assert not touched


@pytest.mark.parametrize(
    "field,value",
    [
        ("support_object", "wooden_cabinet_1"),
        ("support_ground_surface", "main_table"),
        ("second_ground_surface", "wooden_cabinet_1"),
        ("swap_support_groups", True),
    ],
)
def test_cookie_swap_rejects_changed_roles_and_conflicting_mode(field, value):
    config, params = _config()
    params[field] = value
    with pytest.raises(RUNTIME.PerturbationConfigurationError):
        RUNTIME.build_execution_plan(config, RUNTIME.default_asset_root())


def test_disabled_cookie_swap_keeps_the_original_bare_bowl_swap(monkeypatch):
    config, params = _config()
    params["swap_single_support_group"] = False
    plan = RUNTIME.build_execution_plan(config, RUNTIME.default_asset_root())
    env, poses, before, touched = _scene(monkeypatch, config)
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan)
    runtime.apply_static(env)
    assert set(touched) == {"akita_black_bowl_1", "akita_black_bowl_2"}
    np.testing.assert_array_equal(poses["cookies_1"][0], before["cookies_1"][0])
    assert runtime.diagnostics()["events"][0]["event"] == "grounded_planar_object_position_swap"


def test_only_published_task3_s04_enables_cookie_swap_and_keeps_base_semantics():
    manifest = json.loads((ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8"))
    enabled = []
    for item in manifest["tasks"]:
        path = ROOT / "assets" / item["bddl_path"]
        if "(:swap_single_support_group true)" not in path.read_text(encoding="utf-8"):
            continue
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), RUNTIME.default_asset_root()
        )
        assert plan.params["swap_single_support_group"] is True
        enabled.append((item["suite"], item["base_task_id"], item["case_id"]))
    assert enabled == [("libero_spatial", 3, "S04")]

    base = BDDL.parent.parent / "00_base" / BDDL.name.replace("S04__", "BASE__")
    original = PARSER.scan_tokens(filename=str(base))
    modified = PARSER.scan_tokens(filename=str(BDDL))
    for label in (":language", ":init", ":goal", ":objects", ":fixtures", ":regions"):
        assert next(g for g in original if g[0] == label) == next(
            g for g in modified if g[0] == label
        )


def test_generation_only_enables_cookie_swap_for_task3_s04():
    from scripts import apply_goal_review_finalization as finalizer

    enabled = []
    for suite in finalizer.SUITES:
        for task_id in range(10):
            for case in finalizer.PUBLISHED_CASES:
                params, _ = finalizer.case_updates(suite, task_id, case)
                if params.get("swap_single_support_group") == ("true",):
                    enabled.append((suite, task_id, case))
    assert enabled == [("libero_spatial", 3, "S04")]
