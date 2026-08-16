from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from types import SimpleNamespace

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
