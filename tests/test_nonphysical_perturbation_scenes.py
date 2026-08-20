from __future__ import annotations

import importlib.util
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "nonphysical_perturbations.py"
)
SPEC = importlib.util.spec_from_file_location("_nonphysical_perturbations", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PERTURBATIONS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PERTURBATIONS
SPEC.loader.exec_module(PERTURBATIONS)


def _plan(case_id: str, *, targets: tuple[str, ...], references: tuple[str, ...]):
    return PERTURBATIONS.ExecutionPlan(
        case_id=case_id,
        schedule="static",
        operator="test",
        variant="test",
        targets=targets,
        references=references,
        mechanisms=("asset",),
        assets=(
            PERTURBATIONS.AssetSpec(
                asset_id="test/asset",
                xml_path=Path("unused.xml"),
                staged=False,
                replacement=case_id == "S06",
            ),
        ),
    )


def test_scene_entity_names_include_arena_floor_support() -> None:
    class Model:
        def body_name2id(self, name: str) -> int:
            return {"table": 1, "floor": 2}[name]

    env = SimpleNamespace(
        obj_body_id={"target": 3},
        sim=SimpleNamespace(model=Model()),
    )

    assert PERTURBATIONS._scene_entity_names(env) == (
        "target",
        "main_table",
        "floor",
    )


def test_s06_replacement_uses_the_replacement_assets_upright_frame() -> None:
    original = SimpleNamespace(
        category_name="alphabet_soup",
        rotation=(math.pi / 2, math.pi / 2),
        rotation_axis="z",
        object_properties={"vis_site_names": {}},
    )
    replacement = SimpleNamespace()

    PERTURBATIONS.inject_plan_assets(
        {"alphabet_soup_1": original},
        _plan("S06", targets=("alphabet_soup_1",), references=()),
        lambda *_args, **_kwargs: replacement,
    )

    assert replacement.rotation == (0.0, 0.0)
    assert replacement.rotation_axis == "z"


def test_injected_asset_vector_scaling_separates_footprint_and_height() -> None:
    root = ET.fromstring(
        '<body><geom pos="0 0 0.025" size="0.1 0.1 0.025" />'
        '<site pos="0.141421356 0 0" /></body>'
    )
    obj = SimpleNamespace(worldbody=root, get_obj=lambda: root)

    PERTURBATIONS._scale_mujoco_object_vector(obj, (0.75, 0.75, 2.0))

    assert root.find("geom").get("size") == "0.07500000000000001 0.07500000000000001 0.05"
    assert root.find("geom").get("pos") == "0.0 0.0 0.05"
    assert root.find("site").get("pos") == "0.106066017 0.0 0.0"


def test_s06_reapplies_upright_quaternion_after_init_state_load() -> None:
    plan = _plan("S06", targets=("target",), references=())

    class Model:
        body_pos = np.array([[0.10, -0.05, 0.12]], dtype=float)
        body_quat = np.array([[0.0, 1.0, 0.0, 0.0]], dtype=float)

    class Data:
        def __init__(self, model):
            self.body_xpos = model.body_pos.copy()
            self.body_xquat = model.body_quat.copy()

    class Sim:
        def __init__(self):
            self.model = Model()
            self.data = Data(self.model)

        def forward(self):
            self.data.body_xpos[:] = self.model.body_pos
            self.data.body_xquat[:] = self.model.body_quat

    env = SimpleNamespace(
        sim=Sim(),
        obj_body_id={"target": 0},
        objects_dict={},
    )
    PERTURBATIONS.NonPhysicalPerturbationRuntime(plan).apply_static(env)

    np.testing.assert_allclose(env.sim.data.body_xpos[0], [0.10, -0.05, 0.12])
    np.testing.assert_allclose(env.sim.data.body_xquat[0], [1.0, 0.0, 0.0, 0.0])


def test_s04_articulation_uses_a_fixture_offset_instead_of_a_self_swap() -> None:
    plan = PERTURBATIONS.ExecutionPlan(
        case_id="S04",
        schedule="static",
        operator="pose_transform",
        variant="articulation_fixture_pose_offset",
        targets=("goal_fixture",),
        references=(),
        mechanisms=("pose",),
        assets=(),
        params={"interaction_mode": "articulation"},
    )
    model = _FakeModel()
    model.body_pos = np.array([[0.05, 0.10, 0.40]], dtype=float)
    model.body_quat = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=float)
    model.nbody = 1
    sim = _FakeSim()
    sim.model = model
    sim.data = _FakeData(model)
    env = SimpleNamespace(
        sim=sim,
        obj_body_id={"goal_fixture": 0},
        objects_dict={},
        workspace_offset=np.array([0.0, 0.0, 0.9]),
    )

    PERTURBATIONS.NonPhysicalPerturbationRuntime(plan).apply_static(env)

    assert not np.allclose(sim.data.body_xpos[0, :2], [0.05, 0.10])
    assert sim.data.body_xpos[0, 2] == 0.40
    assert PERTURBATIONS.NonPhysicalPerturbationRuntime(plan).plan.targets == (
        "goal_fixture",
    )


class _FakeModel:
    def __init__(self) -> None:
        self.body_pos = np.array([[0.35, 0.0, 0.0], [0.0, 0.0, -5.0]])
        self.body_quat = np.array([[1.0, 0.0, 0.0, 0.0]] * 2)
        self.body_parentid = np.array([0, 0])
        self.nbody = 2
        self.cam_fovy = np.array([60.0])

    def body_name2id(self, name: str) -> int:
        raise KeyError(name)

    def camera_name2id(self, name: str) -> int:
        if name != "agentview":
            raise KeyError(name)
        return 0


class _FakeData:
    def __init__(self, model: _FakeModel) -> None:
        self.body_xpos = model.body_pos.copy()
        self.body_xquat = model.body_quat.copy()
        self.cam_xpos = np.array([[0.0, 0.0, 1.0]])
        self.cam_xmat = np.array(
            [[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]]
        )


class _FakeSim:
    def __init__(self) -> None:
        self.model = _FakeModel()
        self.data = _FakeData(self.model)

    def forward(self) -> None:
        self.data.body_xpos[:] = self.model.body_pos
        self.data.body_xquat[:] = self.model.body_quat


def test_s10_clutter_is_collision_clear_and_inside_agentview() -> None:
    env = SimpleNamespace(
        sim=_FakeSim(),
        obj_body_id={"reference": 0, "perturbation_s10_0": 1},
        objects_dict={
            "reference": SimpleNamespace(joints=[]),
            "perturbation_s10_0": SimpleNamespace(joints=[]),
        },
        workspace_offset=np.array([0.0, 0.0, 0.9]),
    )
    runtime = PERTURBATIONS.NonPhysicalPerturbationRuntime(
        _plan("S10", targets=("reference",), references=("reference",))
    )

    runtime.apply_static(env)

    position = env.sim.data.body_xpos[1]
    camera_relative = position - env.sim.data.cam_xpos[0]
    depth = -camera_relative[2]
    half_extent = depth * math.tan(math.radians(env.sim.model.cam_fovy[0]) / 2) * 0.8
    assert -0.42 <= position[0] <= 0.42
    assert -0.50 <= position[1] <= 0.50
    assert abs(camera_relative[0]) <= half_extent
    assert abs(camera_relative[1]) <= half_extent
    assert np.linalg.norm(position[:2] - env.sim.data.body_xpos[0, :2]) >= 0.10


def test_s05_barrier_keeps_transport_corridor_clear() -> None:
    """S05 must not put the barrier through the carried-object corridor."""

    class Model(_FakeModel):
        def __init__(self) -> None:
            super().__init__()
            self.body_pos = np.array(
                [
                    [0.05, -0.10, 0.04],  # target object
                    [0.00, 0.26, 0.04],  # receiver
                    [-0.15, -0.265, 0.04],  # reference object
                    [0.00, 0.00, -5.00],  # injected barrier
                ],
                dtype=float,
            )
            self.body_quat = np.array([[1.0, 0.0, 0.0, 0.0]] * 4)
            self.body_parentid = np.array([0, 0, 0, 0])
            self.nbody = 4

    class Data(_FakeData):
        def __init__(self, model: Model) -> None:
            super().__init__(model)
            self.ncon = 0
            self.contact = []

    class Sim(_FakeSim):
        def __init__(self) -> None:
            self.model = Model()
            self.data = Data(self.model)

    target = "cream_cheese_1"
    receiver = "basket_1"
    reference = "alphabet_soup_1"
    injected = "perturbation_s05_0"
    env = SimpleNamespace(
        sim=Sim(),
        obj_body_id={target: 0, receiver: 1, reference: 2, injected: 3},
        objects_dict={
            target: SimpleNamespace(joints=[]),
            receiver: SimpleNamespace(joints=[]),
            reference: SimpleNamespace(joints=[]),
            injected: SimpleNamespace(joints=[]),
        },
        object_sites_dict={},
        parsed_problem={"goal_state": [], "regions": {}},
        workspace_offset=np.array([0.0, 0.0, 0.9]),
    )
    plan = _plan("S05", targets=(target, receiver), references=(reference,))
    PERTURBATIONS.NonPhysicalPerturbationRuntime(plan).apply_static(env)

    start = env.sim.data.body_xpos[0, :2]
    end = env.sim.data.body_xpos[1, :2]
    barrier = env.sim.data.body_xpos[3, :2]
    direction = (end - start) / np.linalg.norm(end - start)
    lateral_clearance = abs(
        np.cross(np.r_[direction, 0.0], np.r_[barrier - start, 0.0])[-1]
    )
    assert lateral_clearance >= 0.14


def test_s05_detour_ignores_the_carried_object_on_every_segment() -> None:
    carried = "wine_bottle_1"
    barrier = "perturbation_s05_0"
    target_position = np.array([0.00, 0.00, 0.90])
    receiver_position = np.array([0.14, 0.00, 0.90])
    env = SimpleNamespace(objects_dict={carried: SimpleNamespace(joints=["free_joint"])})

    with (
        mock.patch.object(PERTURBATIONS, "_entity_xy_radius", return_value=0.05),
        mock.patch.object(
            PERTURBATIONS,
            "_entity_pose",
            return_value=(
                np.array([0.00, 0.00, -5.00]),
                np.array([1.00, 0.00, 0.00, 0.00]),
            ),
        ),
        mock.patch.object(PERTURBATIONS, "_candidate_is_clear", return_value=True),
        mock.patch.object(
            PERTURBATIONS, "_candidate_is_clear_of_objects", return_value=True
        ),
        mock.patch.object(
            PERTURBATIONS, "_candidate_is_clear_of_eef", return_value=True
        ),
        mock.patch.object(
            PERTURBATIONS,
            "_ground_entity_on_support",
            side_effect=lambda _env, _name, candidate, _quaternion: (
                candidate,
                "main_table",
            ),
        ),
        mock.patch.object(
            PERTURBATIONS, "_entity_has_penetrating_contact", return_value=False
        ),
        mock.patch.object(
            PERTURBATIONS, "_scene_entity_names", return_value=(carried, barrier)
        ),
        mock.patch.object(PERTURBATIONS, "_entity_is_movable", return_value=True),
        mock.patch.object(
            PERTURBATIONS, "_transport_detour_exists", return_value=True
        ) as detour_exists,
    ):
        PERTURBATIONS._safe_transport_barrier_pose(
            env,
            barrier,
            target_position,
            receiver_position,
            requested_lateral_offset=0.15,
            carried_object_name=carried,
        )

    assert carried in detour_exists.call_args.kwargs["ignored_entities"]


def test_s09_duplicate_target_receiver_keeps_the_stronger_geometry_factor() -> None:
    target = SimpleNamespace(
        worldbody=ET.fromstring('<body><geom size="1 1 1" /></body>')
    )
    plan = PERTURBATIONS.ExecutionPlan(
        case_id="S09",
        schedule="static",
        operator="geometry",
        variant="test",
        targets=("plate_1", "plate_1"),
        references=(),
        mechanisms=("geometry",),
        assets=(),
        params={
            "target_geometry_factors": (1.25, 1.25, 1.25),
            "receiver_geometry_factors": (0.80, 0.80, 0.80),
        },
    )

    changed = PERTURBATIONS.apply_precompile_geometry(
        {"plate_1": target}, {}, plan
    )

    assert changed == ("plate_1",)
    assert target.worldbody.find("geom").get("size") == "1.25 1.25 1.25"
