from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIXER_PATH = ROOT / "scripts" / "apply_feedback_task_fixes.py"
SPEC = importlib.util.spec_from_file_location("_feedback_task_fixes", FIXER_PATH)
assert SPEC is not None and SPEC.loader is not None
FIXER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FIXER
SPEC.loader.exec_module(FIXER)

RUNTIME_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "nonphysical_perturbations.py"
)
RUNTIME_SPEC = importlib.util.spec_from_file_location("_s04_runtime", RUNTIME_PATH)
assert RUNTIME_SPEC is not None and RUNTIME_SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(RUNTIME_SPEC)
sys.modules[RUNTIME_SPEC.name] = RUNTIME
RUNTIME_SPEC.loader.exec_module(RUNTIME)

TASK9_S04 = (
    ROOT
    / "assets"
    / "bddl"
    / "libero-pro2.0-1680-v1"
    / "libero_10"
    / "01_static"
    / "S04__KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it.bddl"
)


def test_task9_s04_publishes_a_strict_zero_offset_swap() -> None:
    text = TASK9_S04.read_text(encoding="utf-8")
    _, _, block = FIXER.case_slice(text, "S04")

    assert "(:grounded_swap true)" in block
    assert "(:swap_xy 0.0 0.0)" in block
    assert "(:strict_swap_xy true)" in block
    assert ":swap_cluster_radius_m" not in block


def test_task9_exception_does_not_change_other_s04_generation() -> None:
    task9, _ = FIXER.task_params("libero_10", 9, "S04")
    generic, _ = FIXER.task_params("libero_10", 7, "S04")
    task8, _ = FIXER.task_params("libero_10", 8, "S04")

    assert task9["grounded_swap"] == ("true",)
    assert task9["swap_xy"] == ("0.0", "0.0")
    assert task9["strict_swap_xy"] == ("true",)
    assert "swap_cluster_radius_m" not in task9

    assert generic["grounded_swap"] == ("true",)
    assert generic["swap_cluster_radius_m"] == ("0.18",)
    assert generic["swap_xy"] == ("0.0", "0.0")
    assert "strict_swap_xy" not in generic

    assert task8["grounded_swap"] == ("true",)
    assert task8["swap_cluster_radius_m"] == ("0.18",)
    assert task8["swap_xy"] == ("0.06", "0.0")
    assert "strict_swap_xy" not in task8


def test_grounded_strict_swap_uses_only_the_original_xy_coordinates(
    monkeypatch,
) -> None:
    first_before = np.array([-0.02, 0.00, 0.97])
    second_before = np.array([-0.12, -0.26, 0.97])
    poses = {
        "white_yellow_mug_1": (first_before, np.array([1.0, 0.0, 0.0, 0.0])),
        "porcelain_mug_1": (second_before, np.array([1.0, 0.0, 0.0, 0.0])),
    }
    grounded_calls = []
    applied = {}

    monkeypatch.setattr(RUNTIME, "_entity_pose", lambda env, name: poses[name])

    def grounded_entity_position(env, name, xy, params, ignored=()):
        grounded_calls.append((name, np.asarray(xy).copy(), ignored))
        return np.array([xy[0], xy[1], 0.90]), "table_collision"

    monkeypatch.setattr(
        RUNTIME, "_grounded_entity_position", grounded_entity_position
    )
    monkeypatch.setattr(
        RUNTIME,
        "_nearby_xy_candidates",
        lambda xy: (_ for _ in ()).throw(
            AssertionError("strict swap must not search shifted XY candidates")
        ),
    )

    def candidate_is_clear(env, name, xy, minimum_gap, ignored=()):
        return True

    monkeypatch.setattr(RUNTIME, "_candidate_is_clear", candidate_is_clear)
    monkeypatch.setattr(
        RUNTIME,
        "_set_entity_pose",
        lambda env, name, position, quaternion: applied.update(
            {name: np.asarray(position).copy()}
        ),
    )
    monkeypatch.setattr(RUNTIME, "_entity_deep_contacts", lambda env, name: [])

    plan = RUNTIME.ExecutionPlan(
        case_id="S04",
        schedule="static",
        operator="pose_transform",
        variant="planar_object_position_swap",
        targets=("white_yellow_mug_1", "porcelain_mug_1"),
        references=(),
        mechanisms=(),
        assets=(),
        params={
            "grounded_swap": True,
            "strict_swap_xy": True,
            "swap_xy": (0.0, 0.0),
            "support_surface": ["table"],
        },
    )
    runtime = RUNTIME.NonPhysicalPerturbationRuntime(plan)

    runtime.apply_static(object())

    np.testing.assert_array_equal(grounded_calls[0][1], second_before[:2])
    np.testing.assert_array_equal(grounded_calls[1][1], first_before[:2])
    np.testing.assert_array_equal(
        applied["white_yellow_mug_1"][:2], second_before[:2]
    )
    np.testing.assert_array_equal(
        applied["porcelain_mug_1"][:2], first_before[:2]
    )
