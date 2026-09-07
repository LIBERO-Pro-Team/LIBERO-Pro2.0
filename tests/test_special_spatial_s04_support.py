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


def test_spatial_task5_s04_opts_into_complete_support_group_swap_only() -> None:
    dataset = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1" / "libero_spatial"
    enabled = []
    for path in dataset.rglob("S04__*.bddl"):
        text = path.read_text(encoding="utf-8")
        if "(:swap_support_groups true)" in text:
            enabled.append(path.name)

    assert enabled == [
        "S04__pick_up_the_black_bowl_on_the_ramekin_and_place_it_on_the_plate.bddl"
    ]
    text = (dataset / "01_static" / enabled[0]).read_text(encoding="utf-8")
    assert "(:support_objects glazed_rim_porcelain_ramekin_1 cookies_1)" in text
    assert "(:support_ground_surface main_table)" in text
    assert "(:group_minimum_clearance_m 0.018)" in text
    assert "(:group_settle_steps 300)" in text


def test_support_group_swap_exchanges_supports_and_preserves_local_poses(monkeypatch) -> None:
    names = (
        "akita_black_bowl_1",
        "akita_black_bowl_2",
        "glazed_rim_porcelain_ramekin_1",
        "cookies_1",
    )
    identity = np.array([1.0, 0.0, 0.0, 0.0])
    poses = {
        "akita_black_bowl_1": (np.array([-0.21, 0.20, 0.94]), identity.copy()),
        "akita_black_bowl_2": (np.array([0.06, 0.04, 0.918]), identity.copy()),
        "glazed_rim_porcelain_ramekin_1": (
            np.array([-0.20, 0.20, 0.90]), identity.copy()
        ),
        "cookies_1": (np.array([0.06, 0.04, 0.91]), identity.copy()),
    }
    applied = {}

    monkeypatch.setattr(RUNTIME, "_entity_exists", lambda env, name: True)
    monkeypatch.setattr(RUNTIME, "_entity_pose", lambda env, name: poses[name])
    monkeypatch.setattr(
        RUNTIME,
        "_candidate_is_clear",
        lambda env, name, xy, minimum_gap, ignored=(): True,
    )
    monkeypatch.setattr(
        RUNTIME,
        "_grounded_entity_position",
        lambda env, name, xy, params, ignored=(): (
            np.array([xy[0], xy[1], 0.90]),
            "table_collision",
        ),
    )
    monkeypatch.setattr(
        RUNTIME,
        "_support_geom_belongs_to_entity",
        lambda env, geom, entity: entity == "main_table",
    )
    monkeypatch.setattr(RUNTIME, "_entity_deep_contacts", lambda env, name: [])
    monkeypatch.setattr(
        RUNTIME,
        "_set_entity_pose",
        lambda env, name, position, quaternion: applied.__setitem__(
            name, (np.asarray(position).copy(), np.asarray(quaternion).copy())
        ),
    )

    params = {
        "support_ground_surface": "main_table",
        "group_minimum_clearance_m": 0.018,
    }
    result = RUNTIME._support_group_swap_transform(
        object(),
        ("akita_black_bowl_1", "akita_black_bowl_2"),
        ("glazed_rim_porcelain_ramekin_1", "cookies_1"),
        (0.0, 0.0),
        params,
    )

    np.testing.assert_allclose(
        applied["glazed_rim_porcelain_ramekin_1"][0][:2], poses["cookies_1"][0][:2]
    )
    np.testing.assert_allclose(
        applied["cookies_1"][0][:2], poses["glazed_rim_porcelain_ramekin_1"][0][:2]
    )
    assert applied["glazed_rim_porcelain_ramekin_1"][0][2] == poses[
        "glazed_rim_porcelain_ramekin_1"
    ][0][2]
    assert applied["cookies_1"][0][2] == poses["cookies_1"][0][2]
    np.testing.assert_allclose(
        applied["akita_black_bowl_1"][0] - applied["glazed_rim_porcelain_ramekin_1"][0],
        poses["akita_black_bowl_1"][0] - poses["glazed_rim_porcelain_ramekin_1"][0],
    )
    np.testing.assert_allclose(
        applied["akita_black_bowl_2"][0] - applied["cookies_1"][0],
        poses["akita_black_bowl_2"][0] - poses["cookies_1"][0],
    )
    assert result["support_ground_surface"] == "main_table"
