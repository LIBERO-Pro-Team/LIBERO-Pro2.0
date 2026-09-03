from __future__ import annotations

import copy
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = (
    ROOT / "simulator-source" / "libero" / "libero" / "envs" / "nonphysical_perturbations.py"
)
SPEC = importlib.util.spec_from_file_location("_task9_s09_runtime", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)

S09_PATH = (
    ROOT
    / "assets"
    / "bddl"
    / "libero-pro2.0-1680-v1"
    / "libero_10"
    / "01_static"
    / "S09__KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it.bddl"
)


class FakeObject:
    def __init__(self) -> None:
        self.asset = ET.fromstring("<asset><mesh scale='1 1 1'/></asset>")
        self.worldbody = ET.fromstring(
            """
            <worldbody>
              <body>
                <site name="bottom_site" pos="0 0 -1" size="0.1"/>
                <body name="object">
                  <geom pos="1 2 3" size="1 2 3"/>
                  <site name="heating_region" pos="2 3 4" size="3 4 5"/>
                  <body name="door" pos="4 5 6">
                    <joint name="hinge" pos="7 8 9" range="-2.094 0"/>
                    <geom pos="10 11 12" size="4 5 6"/>
                  </body>
                </body>
              </body>
            </worldbody>
            """
        )
        self._obj = copy.deepcopy(self.worldbody.find("./body/body[@name='object']"))

    def get_obj(self):
        return self._obj


def _plan(*, scale_compiled_geometry: bool) -> object:
    params = {
        "target_geometry_factors": (1.2, 1.2, 1.2),
        "receiver_geometry_factors": (1.2, 1.2, 1.2),
    }
    if scale_compiled_geometry:
        params["scale_compiled_geometry"] = True
    return RUNTIME.ExecutionPlan(
        case_id="S09",
        schedule="static",
        operator="geometry_variant",
        variant="container_opening_clearance_and_pose_coupling",
        targets=("white_yellow_mug_1", "microwave_1"),
        references=(),
        mechanisms=(),
        assets=(),
        trigger="reset",
        params=params,
    )


def _values(element: ET.Element, attribute: str) -> list[float]:
    return [float(value) for value in element.get(attribute, "").split()]


def test_opt_in_scales_the_bodies_consumed_by_model_compilation() -> None:
    cup = FakeObject()
    microwave = FakeObject()

    changed = RUNTIME.apply_precompile_geometry(
        {"white_yellow_mug_1": cup},
        {"microwave_1": microwave},
        _plan(scale_compiled_geometry=True),
    )

    assert changed == ("microwave_1", "white_yellow_mug_1")
    assert np.allclose(_values(cup.get_obj().find("geom"), "pos"), [1.2, 2.4, 3.6])
    assert np.allclose(_values(cup.get_obj().find("geom"), "size"), [1.2, 2.4, 3.6])
    assert np.allclose(
        _values(microwave.get_obj().find("body[@name='door']"), "pos"),
        [
            4.8,
            6.0,
            7.2,
        ],
    )
    joint = microwave.get_obj().find("body[@name='door']/joint")
    assert np.allclose(_values(joint, "pos"), [8.4, 9.6, 10.8])
    assert np.allclose(_values(joint, "range"), [-2.094, 0.0])
    receiver_site = microwave.get_obj().find("site[@name='heating_region']")
    assert np.allclose(_values(receiver_site, "pos"), [2.4, 3.6, 4.8])
    assert np.allclose(_values(receiver_site, "size"), [3.6, 4.8, 6.0])
    assert np.allclose(_values(microwave.asset.find("mesh"), "scale"), [1.2] * 3)


def test_compiled_body_scaling_is_disabled_without_the_explicit_opt_in() -> None:
    cup = FakeObject()

    RUNTIME.apply_precompile_geometry(
        {"white_yellow_mug_1": cup},
        {},
        RUNTIME.ExecutionPlan(
            **{
                **_plan(scale_compiled_geometry=False).__dict__,
                "targets": ("white_yellow_mug_1",),
            }
        ),
    )

    assert np.allclose(_values(cup.get_obj().find("geom"), "pos"), [1.0, 2.0, 3.0])
    assert np.allclose(_values(cup.get_obj().find("geom"), "size"), [1.0, 2.0, 3.0])
    assert np.allclose(_values(cup.worldbody.find(".//geom"), "size"), [1.2, 2.4, 3.6])
    assert np.allclose(_values(cup.asset.find("mesh"), "scale"), [1.2] * 3)


def test_only_libero10_task9_s09_opts_into_compiled_geometry_scaling() -> None:
    text = S09_PATH.read_text(encoding="utf-8")

    assert "(:target_geometry_factors 1.20 1.20 1.20)" in text
    assert "(:receiver_geometry_factors 1.20 1.20 1.20)" in text
    assert "(:scale_compiled_geometry true)" in text

    dataset_root = S09_PATH.parents[2]
    opted_in = [
        path
        for path in dataset_root.rglob("*.bddl")
        if "(:scale_compiled_geometry true)" in path.read_text(encoding="utf-8")
    ]
    assert opted_in == [S09_PATH]
