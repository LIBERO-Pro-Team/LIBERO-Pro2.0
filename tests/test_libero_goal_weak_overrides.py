"""Regression coverage for the reviewed LIBERO-goal weak-perturbation ledger."""

from scripts.apply_libero_goal_weak_overrides import (
    HARD_SAFETY_TASKS,
    WEAK_TASKS,
    dynamic_validation_cases,
    overrides,
    update_case,
)


def test_all_explicitly_weak_or_untriggered_cases_are_covered() -> None:
    assert {"D01", "D06", "D17", "S04"} <= set(WEAK_TASKS)
    assert WEAK_TASKS["D01"] == (0, 9)
    assert WEAK_TASKS["D06"] == tuple(range(10))
    assert WEAK_TASKS["D17"] == (2, 7)
    assert WEAK_TASKS["S04"] == (0, 7)


def test_dynamic_renderer_covers_every_reviewed_weak_and_safety_case() -> None:
    rendered = set(dynamic_validation_cases())
    expected = {
        (task_id, case_id)
        for ledger in (WEAK_TASKS, HARD_SAFETY_TASKS)
        for case_id, task_ids in ledger.items()
        if case_id.startswith("D")
        for task_id in task_ids
    }
    assert expected <= rendered
    assert len(rendered) == len(dynamic_validation_cases())


def test_scene_safety_fixes_keep_the_requested_smaller_geometry_and_detour() -> None:
    assert HARD_SAFETY_TASKS == {"D05": (1, 2, 3, 4, 8)}
    assert overrides(8, "D03") == {}
    assert overrides(3, "D05")["lateral_offset_m"] == ("0.08",)
    assert overrides(3, "D05")["physical_collision"] == ("true",)


def test_weak_task_phase_events_use_a_model_agnostic_proximity_trigger() -> None:
    for case_id in ("D04", "D06", "D07", "D12", "D14", "D15", "D16"):
        assert overrides(0, case_id)["trigger_distance_m"] == ("0.22",)


def test_task4_s06_uses_a_same_geometry_visible_bowl_variant() -> None:
    assert overrides(4, "S06")["asset_id"] == (
        "libero/red_akita_black_bowl",
    )
    assert overrides(4, "S06")["asset_scale"] == ("1.0",)


def test_update_case_keeps_inserted_params_on_their_own_lines() -> None:
    source = """(S03
  (:params
    (:interaction_mode placement)
  )
)"""

    updated = update_case(source, "S03", {"height_delta_m": ("0.10",)})

    assert "(:height_delta_m 0.10)\n        )" in updated
    assert "\n        \n" not in updated
