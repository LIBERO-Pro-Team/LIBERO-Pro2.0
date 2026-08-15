from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "libero" / "libero" / "envs" / "objects" / "site_object.py"


def load_site_object_class(monkeypatch):
    robosuite = types.ModuleType("robosuite")
    utils = types.ModuleType("robosuite.utils")
    mjcf_utils = types.ModuleType("robosuite.utils.mjcf_utils")
    transform_utils = types.ModuleType("robosuite.utils.transform_utils")
    mjcf_utils.string_to_array = lambda value: np.fromstring(value, sep=" ")
    transform_utils.mat2quat = lambda value: value
    monkeypatch.setitem(sys.modules, "robosuite", robosuite)
    monkeypatch.setitem(sys.modules, "robosuite.utils", utils)
    monkeypatch.setitem(sys.modules, "robosuite.utils.mjcf_utils", mjcf_utils)
    monkeypatch.setitem(sys.modules, "robosuite.utils.transform_utils", transform_utils)
    spec = importlib.util.spec_from_file_location("libero_pro_site_object", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.SiteObject


def test_under_uses_inverse_site_rotation_for_world_point(monkeypatch) -> None:
    site = load_site_object_class(monkeypatch)(
        name="rotated_receiver",
        size="0.10 0.02 0.01",
    )
    world_from_site = np.array(
        [
            [0.0, -1.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    local_point = np.array([0.08, 0.01, 0.03])
    world_point = world_from_site @ local_point

    assert site.under(np.zeros(3), world_from_site, world_point)


def test_in_box_rejects_point_only_inside_rotated_axis_aligned_bounds(monkeypatch) -> None:
    site = load_site_object_class(monkeypatch)(
        name="rotated_container",
        size="0.10 0.02 0.04",
    )
    angle = np.pi / 4
    world_from_site = np.array(
        [
            [np.cos(angle), -np.sin(angle), 0.0],
            [np.sin(angle), np.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    false_positive_for_aabb = np.array([0.075, 0.075, 0.0])
    valid_local_point = np.array([0.08, 0.01, 0.0])

    assert not site.in_box(
        np.zeros(3), world_from_site, false_positive_for_aabb
    )
    assert site.in_box(
        np.zeros(3), world_from_site, world_from_site @ valid_local_point
    )
