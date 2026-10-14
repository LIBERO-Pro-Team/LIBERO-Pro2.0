from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BDDL_ROOT = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
ASSET_ROOT = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "assets"
    / "perturbation_assets"
)
INJECTED_OBSTACLE_TASKS = {
    ("libero_10", 0),
    ("libero_10", 4),
    ("libero_10", 5),
    ("libero_10", 6),
    ("libero_10", 7),
    ("libero_10", 8),
    ("libero_10", 9),
    ("libero_goal", 1),
    ("libero_goal", 2),
    ("libero_goal", 3),
    ("libero_goal", 4),
    ("libero_goal", 5),
    ("libero_goal", 6),
    *(("libero_object", task_id) for task_id in range(10)),
    *(("libero_spatial", task_id) for task_id in range(10)),
}
TABLE_SUPPORTED_MICROWAVE_TASK = ("libero_10", 9)
CREAM_CHEESE_IN_BOWL_TASK = ("libero_goal", 6)
TABLE_SUPPORTED_WINE_RACK_TASK = ("libero_goal", 9)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PARSER = _load_module(
    "_all_d03_parser",
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "perturbation_config.py",
)
RUNTIME = _load_module(
    "_all_d03_runtime",
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "nonphysical_perturbations.py",
)


def _manifest_d03_entries() -> list[dict[str, object]]:
    manifest = json.loads(
        (ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8")
    )
    return [item for item in manifest["tasks"] if item["case_id"] == "D03"]


def _declared_objects(tree: list[object]) -> set[str]:
    group = next(
        item
        for item in tree
        if isinstance(item, list) and item and item[0] == ":objects"
    )
    objects: set[str] = set()
    pending: list[str] = []
    index = 1
    while index < len(group):
        token = group[index]
        if token == "-":
            objects.update(pending)
            pending.clear()
            index += 2
            continue
        pending.append(str(token))
        index += 1
    return objects


def _goal_objects(tree: list[object], objects: set[str]) -> set[str]:
    goal = next(
        item
        for item in tree
        if isinstance(item, list) and item and item[0] == ":goal"
    )
    found: set[str] = set()

    def visit(node: object) -> None:
        if not isinstance(node, list):
            return
        if len(node) >= 2 and str(node[0]).casefold() in {"on", "in"}:
            if str(node[1]) in objects:
                found.add(str(node[1]))
        for child in node:
            visit(child)

    visit(goal)
    return found


def _canonical_hash(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    ).hexdigest()


def test_all_published_d03_tasks_use_persistent_obstacles() -> None:
    entries = _manifest_d03_entries()

    assert len(entries) == 37
    assert Counter(str(item["suite"]) for item in entries) == {
        "libero_10": 10,
        "libero_goal": 7,
        "libero_object": 10,
        "libero_spatial": 10,
    }

    for item in entries:
        key = (str(item["suite"]), int(item["base_task_id"]))
        path = ROOT / "assets" / str(item["bddl_path"])
        plan = RUNTIME.build_execution_plan(
            PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
        )

        assert plan.case_id == "D03"
        assert plan.trigger == "preplace"
        assert plan.variant == "persistent_triggered_receiver_occupation"
        assert plan.params["receiver_trigger_distance_m"] >= 0.24
        assert plan.params["staging_position_xyz"] == [0.0, 0.0, -5.0]
        assert plan.params["asset_offset_xyz"] == [0.0, 0.0, 0.0] or len(
            plan.params["asset_offset_xyz"]
        ) == 3
        assert "support_surface" in plan.params
        assert "event_duration_steps" not in plan.params
        assert _canonical_hash(path) == item["bddl_sha256"]

        if key == TABLE_SUPPORTED_WINE_RACK_TASK:
            assert plan.params["support_surface"] == "main_table"
            assert plan.params["asset_offset_xyz"] == [0.14, 0.05, -0.22]
        elif key == TABLE_SUPPORTED_MICROWAVE_TASK:
            assert plan.params["asset_offset_xyz"] == [-0.04, -0.05, 0.0]
        elif key == CREAM_CHEESE_IN_BOWL_TASK:
            assert plan.params["asset_offset_xyz"] == [0.00835045, 0.00205392, 0.0]

        tree = PARSER.scan_tokens(filename=str(path))
        objects = _declared_objects(tree)
        goal_objects = _goal_objects(tree, objects)
        if key in INJECTED_OBSTACLE_TASKS:
            assert plan.params["persistent_movable_asset"] is True
            assert "persistent_existing_obstacle" not in plan.params
            assert plan.references == ()
            assert len(plan.assets) == 1
            if key == ("libero_10", 0):
                assert plan.assets[0].asset_id == "ycb/YcbFoamBrick"
                assert plan.assets[0].scale == 1.0
            elif key == ("libero_10", 5):
                assert plan.assets[0].asset_id == "ycb/YcbChipsCan"
                assert plan.assets[0].scale == 0.70
            elif key == ("libero_10", 4):
                assert plan.params["receiver_selection"] == "active_goal_path"
                assert plan.targets == ("plate_1", "plate_2")
                assert plan.params["support_surface"] == "living_room_table"
                assert plan.assets[0].asset_id == "ycb/YcbTomatoSoupCan"
                assert plan.assets[0].scale == 0.50
            elif key[0] == "libero_spatial":
                assert plan.targets == ("plate_1",)
                assert plan.params["support_surface"] == "plate_1"
                assert plan.params["asset_contact_margin_m"] == 0.0
                assert plan.assets[0].asset_id == "ycb/YcbFoamBrick"
                assert plan.assets[0].scale == 0.85
                assert "akita_black_bowl_2" not in plan.references
            elif key == ("libero_10", 8):
                assert plan.assets[0].asset_id == "prl/can"
                assert plan.assets[0].scale == 1.0
        else:
            assert plan.params["persistent_existing_obstacle"] is True
            assert "persistent_movable_asset" not in plan.params
            assert len(plan.references) == 1
            assert plan.references[0] in objects
            assert plan.references[0] not in goal_objects
            assert plan.assets == ()


def test_non_d03_tasks_do_not_enable_persistent_obstacle_runtime() -> None:
    path = next((BDDL_ROOT / "libero_goal" / "02_dynamic").glob("D04__*.bddl"))
    plan = RUNTIME.build_execution_plan(
        PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
    )

    assert plan.case_id == "D04"
    assert plan.variant != "persistent_triggered_receiver_occupation"
    assert "persistent_existing_obstacle" not in plan.params
    assert "persistent_movable_asset" not in plan.params
    assert len(plan.assets) == 1


def test_only_opted_in_d03_assets_are_free_joint_and_above_scene() -> None:
    class FakeAssetObject:
        def __init__(self, xml_path: str, name: str, joints: str | None):
            self.xml_path = Path(xml_path)
            self.name = name
            self.joints = joints
            self.root = ET.fromstring(
                '<body pos="0 0 0"><geom size="0.1 0.1 0.1" /></body>'
            )

        def get_obj(self):
            return self.root

    d03_path = next(
        (BDDL_ROOT / "libero_10" / "02_dynamic").glob(
            "D03__KITCHEN_SCENE8_*.bddl"
        )
    )
    d03_plan = RUNTIME.build_execution_plan(
        PARSER.parse_bddl_perturbation_config(d03_path), ASSET_ROOT
    )
    d03_objects: dict[str, object] = {}

    RUNTIME.inject_plan_assets(d03_objects, d03_plan, FakeAssetObject)

    d03_asset = d03_objects["perturbation_d03_0"]
    assert d03_asset.joints == "default"
    assert d03_asset.get_obj().get("pos") == "0 0 3"

    d04_path = next((BDDL_ROOT / "libero_goal" / "02_dynamic").glob("D04__*.bddl"))
    d04_plan = RUNTIME.build_execution_plan(
        PARSER.parse_bddl_perturbation_config(d04_path), ASSET_ROOT
    )
    d04_objects: dict[str, object] = {}

    RUNTIME.inject_plan_assets(d04_objects, d04_plan, FakeAssetObject)

    d04_asset = d04_objects["perturbation_d04_0"]
    assert d04_asset.joints is None
    assert d04_asset.get_obj().get("pos") == "0 0 -5"


def test_injected_d03_asset_disables_collision_before_underground_staging() -> None:
    path = next(
        (BDDL_ROOT / "libero_10" / "02_dynamic").glob(
            "D03__KITCHEN_SCENE8_*.bddl"
        )
    )
    plan = RUNTIME.build_execution_plan(
        PARSER.parse_bddl_perturbation_config(path), ASSET_ROOT
    )
    positions = np.array([[0.0, 0.0, 0.90], [0.0, 0.0, 3.0]], dtype=float)
    quaternions = np.tile([1.0, 0.0, 0.0, 0.0], (2, 1))
    qvel = np.full(6, 0.5, dtype=float)
    data = SimpleNamespace(
        body_xpos=positions,
        body_xquat=quaternions,
        qvel=qvel,
        ncon=0,
        contact=[],
    )
    data.set_joint_qpos = lambda _name, qpos: (
        positions.__setitem__(1, np.asarray(qpos[:3], dtype=float)),
        quaternions.__setitem__(1, np.asarray(qpos[3:7], dtype=float)),
    )
    data.set_joint_qvel = lambda _name, value: qvel.__setitem__(slice(0, 6), value)
    model = SimpleNamespace(
        nbody=2,
        ngeom=1,
        body_pos=positions,
        body_quat=quaternions,
        body_parentid=np.array([-1, 0], dtype=int),
        body_gravcomp=np.zeros(2, dtype=float),
        geom_bodyid=np.array([1], dtype=int),
        geom_contype=np.array([3], dtype=int),
        geom_conaffinity=np.array([5], dtype=int),
        jnt_type=np.array([0], dtype=int),
        jnt_dofadr=np.array([0], dtype=int),
    )
    model.joint_name2id = lambda _name: 0
    model.body_id2name = lambda body_id: (
        "flat_stove_1",
        "perturbation_d03_0",
    )[body_id]
    sim = SimpleNamespace(model=model, data=data, forward=lambda: None)
    env = SimpleNamespace(
        obj_body_id={"flat_stove_1": 0, "perturbation_d03_0": 1},
        objects_dict={
            "flat_stove_1": SimpleNamespace(joints=[]),
            "perturbation_d03_0": SimpleNamespace(joints=["obstacle_joint"]),
        },
        object_sites_dict={},
        object_states_dict={},
        parsed_problem={"goal_state": [], "regions": {}},
        sim=sim,
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=143)

    runtime.apply_static(env)

    np.testing.assert_allclose(positions[1], [0.0, 0.0, 3.0])
    assert model.geom_contype[0] == 3
    assert model.geom_conaffinity[0] == 5

    runtime.begin_rollout(env)

    np.testing.assert_allclose(positions[1], [0.0, 0.0, -5.0])
    np.testing.assert_allclose(qvel, 0.0)
    assert model.geom_contype[0] == 0
    assert model.geom_conaffinity[0] == 0


def test_existing_d03_obstacle_triggers_once_and_remains_movable() -> None:
    plan = RUNTIME.ExecutionPlan(
        case_id="D03",
        schedule="dynamic",
        operator="occlusion_or_obstacle",
        variant="persistent_triggered_receiver_occupation",
        targets=("flat_stove_1",),
        references=("cream_cheese_1",),
        mechanisms=("asset", "dynamic_pose"),
        assets=(),
        trigger="preplace",
        params={
            "persistent_existing_obstacle": True,
            "receiver_trigger_distance_m": 0.24,
            "receiver_anchor": "flat_stove_1_cook_region",
            "support_surface": "flat_stove_1",
            "asset_offset_xyz": [0.0, 0.0, 0.0],
            "staging_position_xyz": [0.0, 0.0, -5.0],
        },
    )
    positions = np.array(
        [[-0.41, 0.21, 0.91], [-0.20, -0.10, 0.93], [0.10, -0.20, 0.93]],
        dtype=float,
    )
    quaternions = np.tile([1.0, 0.0, 0.0, 0.0], (3, 1))
    qvel = np.full(12, 0.5, dtype=float)
    joint_ids = {"cream_cheese_joint": 0, "bowl_joint": 1}
    data = SimpleNamespace(
        body_xpos=positions,
        body_xquat=quaternions,
        qvel=qvel,
        ncon=0,
        contact=[],
        site_xpos=np.array([[0.5, -0.5, 1.0]], dtype=float),
    )

    def set_joint_qpos(name, qpos):
        body_id = joint_ids[name] + 1
        positions[body_id] = np.asarray(qpos[:3], dtype=float)
        quaternions[body_id] = np.asarray(qpos[3:7], dtype=float)

    data.set_joint_qpos = set_joint_qpos
    data.set_joint_qvel = lambda name, value: qvel.__setitem__(
        slice(6 * joint_ids[name], 6 * joint_ids[name] + 6), value
    )
    data.get_site_xpos = lambda _name: positions[0] + np.array([0.0, 0.0, 0.04])
    model = SimpleNamespace(
        nbody=3,
        ngeom=1,
        body_pos=positions,
        body_quat=quaternions,
        body_parentid=np.array([-1, 0, 0], dtype=int),
        body_gravcomp=np.zeros(3, dtype=float),
        geom_bodyid=np.array([1], dtype=int),
        geom_group=np.array([0], dtype=int),
        geom_contype=np.array([3], dtype=int),
        geom_conaffinity=np.array([5], dtype=int),
        jnt_type=np.array([0, 0], dtype=int),
        jnt_dofadr=np.array([0, 6], dtype=int),
    )
    model.joint_name2id = lambda name: joint_ids[name]
    model.body_id2name = lambda body_id: (
        "flat_stove_1",
        "cream_cheese_1",
        "akita_black_bowl_1",
    )[body_id]
    sim = SimpleNamespace(model=model, data=data, forward=lambda: None)
    env = SimpleNamespace(
        obj_body_id={
            "flat_stove_1": 0,
            "cream_cheese_1": 1,
            "akita_black_bowl_1": 2,
        },
        objects_dict={
            "flat_stove_1": SimpleNamespace(joints=[]),
            "cream_cheese_1": SimpleNamespace(joints=["cream_cheese_joint"]),
            "akita_black_bowl_1": SimpleNamespace(joints=["bowl_joint"]),
        },
        parsed_problem={
            "goal_state": [
                ["On", "akita_black_bowl_1", "flat_stove_1_cook_region"]
            ],
            "regions": {"flat_stove_1_cook_region": {"target": "flat_stove_1"}},
        },
        object_sites_dict={
            "flat_stove_1_cook_region": SimpleNamespace(parent_name="flat_stove_1")
        },
        object_states_dict={},
        robots=[SimpleNamespace(eef_site_id=0)],
        sim=sim,
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan, seed=143)

    runtime.begin_rollout(env)
    np.testing.assert_allclose(positions[1], [0.0, 0.0, -5.0])
    assert model.geom_contype[0] == 0
    assert model.geom_conaffinity[0] == 0

    positions[1] = [0.0, 0.0, -7.0]
    qvel[:6] = 2.0
    runtime.before_simulation_step(env, 1)
    np.testing.assert_allclose(positions[1], [0.0, 0.0, -5.0])
    np.testing.assert_allclose(qvel[:6], 0.0)

    positions[2] = positions[0] + np.array([0.15, 0.0, 0.08])
    data.site_xpos[0] = positions[0] + np.array([0.15, 0.0, 0.10])
    runtime.before_simulation_step(env, 2)

    assert np.linalg.norm(positions[1][:2] - positions[0][:2]) <= 0.06
    assert model.geom_contype[0] == 3
    assert model.geom_conaffinity[0] == 5
    assert [event["event"] for event in runtime.events] == [
        "persistent_dynamic_obstacle_entered"
    ]

    positions[1] = [-0.30, 0.12, 0.95]
    runtime.before_simulation_step(env, 500)
    np.testing.assert_allclose(positions[1], [-0.30, 0.12, 0.95])
    assert len(runtime.events) == 1

    runtime.begin_rollout(env)
    np.testing.assert_allclose(positions[1], [0.0, 0.0, -5.0])
    assert model.geom_contype[0] == 0
    assert model.geom_conaffinity[0] == 0
    assert runtime.events == []
