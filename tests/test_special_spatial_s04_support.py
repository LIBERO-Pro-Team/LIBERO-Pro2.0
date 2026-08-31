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
SPEC = importlib.util.spec_from_file_location("_special_spatial_s04_runtime", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)


def test_declared_support_grounding_is_task_local(monkeypatch) -> None:
    first_before = np.array([0.02, -0.28, 1.13])
    second_before = np.array([-0.26, -0.15, 0.93])
    poses = {
        "first": (first_before, np.array([1.0, 0.0, 0.0, 0.0])),
        "second": (second_before, np.array([1.0, 0.0, 0.0, 0.0])),
    }
    grounded_calls = []
    clear_calls = []
    applied = {}

    monkeypatch.setattr(RUNTIME, "_entity_pose", lambda env, name: poses[name])
    monkeypatch.setattr(
        RUNTIME,
        "_support_entity_names",
        lambda params: ("wooden_cabinet_1", "flat_stove_1"),
    )

    def grounded_entity_position(env, name, xy, params, ignored=()):
        grounded_calls.append((name, tuple(ignored)))
        return np.array([xy[0], xy[1], 1.13 if name == "first" else 0.93]), name + "_support"

    monkeypatch.setattr(RUNTIME, "_grounded_entity_position", grounded_entity_position)
    monkeypatch.setattr(
        RUNTIME,
        "_candidate_is_clear",
        lambda env, name, xy, minimum_gap, ignored=(): clear_calls.append(
            (name, tuple(ignored)
        )
        )
        or True,
    )
    monkeypatch.setattr(
        RUNTIME,
        "_set_entity_pose",
        lambda env, name, position, quaternion: applied.__setitem__(
            name, np.asarray(position).copy()
        ),
    )
    monkeypatch.setattr(RUNTIME, "_entity_deep_contacts", lambda env, name: [])

    plan = RUNTIME.ExecutionPlan(
        case_id="S04",
        schedule="static",
        operator="pose_transform",
        variant="planar_object_position_swap",
        targets=("first", "second"),
        references=(),
        mechanisms=(),
        assets=(),
        trigger="reset",
        params={
            "grounded_swap": True,
            "strict_swap_xy": True,
            "swap_xy": (0.0, 0.0),
            "support_surface": ["wooden_cabinet_1", "flat_stove_1"],
            "ground_support_from_declared_surface": True,
        },
    )

    RUNTIME.NonPhysicalPerturbationRuntime(plan).apply_static(object())

    assert grounded_calls == [("first", ("first", "second")), ("second", ("first", "second"))]
    assert clear_calls == [
        ("first", ("first", "second", "wooden_cabinet_1", "flat_stove_1")),
        ("second", ("first", "second", "wooden_cabinet_1", "flat_stove_1")),
    ]
    np.testing.assert_array_equal(applied["first"][:2], second_before[:2])
    np.testing.assert_array_equal(applied["second"][:2], first_before[:2])


def test_grounded_spatial_s04_files_opt_in_to_declared_support_grounding() -> None:
    paths = {
        path.name: path.read_text(encoding="utf-8")
        for path in (
            ROOT
            / "assets"
            / "bddl"
            / "libero-pro2.0-1680-v1"
            / "libero_spatial"
            / "01_static"
        ).glob("S04__*.bddl")
    }

    opted_in = {
        name
        for name, text in paths.items()
        if "(:ground_support_from_declared_surface true)" in text
    }
    assert opted_in == {
        "S04__pick_up_the_black_bowl_between_the_plate_and_the_ramekin_and_place_it_on_the_plate.bddl",
        "S04__pick_up_the_black_bowl_from_table_center_and_place_it_on_the_plate.bddl",
        "S04__pick_up_the_black_bowl_in_the_top_drawer_of_the_wooden_cabinet_and_place_it_on_the_plate.bddl",
        "S04__pick_up_the_black_bowl_next_to_the_cookie_box_and_place_it_on_the_plate.bddl",
        "S04__pick_up_the_black_bowl_next_to_the_ramekin_and_place_it_on_the_plate.bddl",
        "S04__pick_up_the_black_bowl_on_the_cookie_box_and_place_it_on_the_plate.bddl",
        "S04__pick_up_the_black_bowl_on_the_ramekin_and_place_it_on_the_plate.bddl",
        "S04__pick_up_the_black_bowl_on_the_stove_and_place_it_on_the_plate.bddl",
        "S04__pick_up_the_black_bowl_on_the_wooden_cabinet_and_place_it_on_the_plate.bddl",
    }


def test_spatial_task4_d18_uses_the_stable_task_local_drop_state() -> None:
    path = next(
        (
            ROOT
            / "assets"
            / "bddl"
            / "libero-pro2.0-1680-v1"
            / "libero_spatial"
            / "02_dynamic"
        ).glob("D18__pick_up_the_black_bowl_in_the_top_drawer*.bddl")
    )
    text = path.read_text(encoding="utf-8")
    assert "(:offset_xy 0.04 -0.12)" in text
    assert "(:minimum_clearance_m 0.08)" in text
    assert "(:grounded_pose true)" in text


def test_spatial_task5_s04_preserves_the_two_stable_support_heights() -> None:
    path = next(
        (
            ROOT
            / "assets"
            / "bddl"
            / "libero-pro2.0-1680-v1"
            / "libero_spatial"
            / "01_static"
        ).glob("S04__pick_up_the_black_bowl_on_the_ramekin*.bddl")
    )

    text = path.read_text(encoding="utf-8")

    assert "(:preserve_swapped_support_heights true)" in text
