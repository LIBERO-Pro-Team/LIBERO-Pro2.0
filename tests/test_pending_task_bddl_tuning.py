from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location(
    "apply_pending_task_bddl_tuning",
    SCRIPTS / "apply_pending_task_bddl_tuning.py",
)
assert SPEC is not None and SPEC.loader is not None
TUNING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TUNING)


def test_tuning_plan_only_contains_feedback_tasks_supported_by_existing_runtime() -> None:
    rows = TUNING.review_rows()
    plan, skipped = TUNING.build_tuning_plan(rows)

    assert len(rows) == 233
    assert len(plan) == 218
    assert len(skipped) == 15
    assert ("libero_spatial", 0, "S15") not in plan
    assert ("libero_10", 4, "D12") in skipped
    assert ("libero_goal", 8, "D19") in skipped
    assert ("libero_spatial", 2, "D13") in skipped


def test_tuning_uses_current_runtime_field_names_and_task_specific_safety_values() -> None:
    plan, _ = TUNING.build_tuning_plan(TUNING.review_rows())

    assert plan[("libero_goal", 0, "S15")] == {
        "camera_offset_xyz": ("0.100", "-0.100", "0.070"),
        "camera_rotation_rpy": ("0.0", "0.0", "0.0"),
    }
    assert plan[("libero_object", 1, "D16")]["takeover_action"] == (
        "-0.18",
        "0.08",
    )
    assert plan[("libero_10", 6, "D19")] == {
        "misplace_offset_xy": ("0.035", "0.020"),
        "misplace_height_m": ("0.005",),
        "event_duration_steps": ("24",),
    }
    assert plan[("libero_goal", 2, "D19")]["misplace_offset_xy"] == (
        "0.070",
        "0.040",
    )
    assert plan[("libero_object", 0, "D19")] == {
        "misplace_offset_xy": ("0.120", "0.0"),
        "misplace_height_m": ("0.0",),
        "event_duration_steps": ("24",),
    }
    assert "camera_offset_m" not in {
        field for values in plan.values() for field in values
    }
    assert "observation_delay_steps" not in {
        field for values in plan.values() for field in values
    }


def test_user_requested_task_level_strength_values() -> None:
    plan, _ = TUNING.build_tuning_plan(TUNING.review_rows())

    assert plan[("libero_goal", 0, "S16")] == {
        "fov_scale": ("1.35",),
        "image_shift_xy": ("0.10", "-0.10"),
        "crop_ratio": ("0.04",),
        "distortion_strength": ("0.04",),
    }
    assert plan[("libero_goal", 0, "S17")]["joint_offset_rad"] == (
        "0.090", "-0.090", "0.090", "0.0", "0.0", "0.0", "0.0"
    )
    assert plan[("libero_10", 5, "S17")]["joint_offset_rad"] == (
        "-0.090", "0.090", "-0.090", "0.0", "0.0", "0.0", "0.0"
    )
    assert plan[("libero_goal", 0, "S18")]["joint_zero_offset_rad"] == (
        "0.050", "-0.040", "0.030"
    )
    assert plan[("libero_goal", 0, "S18")]["eef_offset_xyz"] == (
        "0.050", "-0.040", "0.030"
    )
    assert plan[("libero_goal", 0, "S20")]["delay_steps"] == ("7",)
    assert plan[("libero_goal", 0, "D07")]["camera_offset_xyz"] == (
        "0.100", "-0.100", "0.070"
    )
    assert plan[("libero_goal", 0, "D12")] == {
        "delay_steps": ("10",),
        "event_duration_steps": ("36",),
    }
    assert plan[("libero_goal", 0, "D13")] == {
        "arm_delay_steps": ("8",),
        "gripper_delay_steps": ("8",),
        "event_duration_steps": ("36",),
    }
    assert plan[("libero_goal", 0, "D14")]["repeat_count"] == ("8",)
    assert plan[("libero_goal", 0, "D14")]["event_duration_steps"] == ("8",)


def test_case_parameter_update_is_idempotent() -> None:
    source = """(define (problem sample)
  (:perturbation_config
    (:perturbations
      (S15
        (:operator camera_transform)
        (:params
          (:interaction_mode placement)
          (:camera_offset_xyz 0.045 -0.035 0.025)
          (:camera_rotation_rpy 0.0 0.0 0.0)
        )
      )
    )
  )
)
"""
    values = {
        "camera_offset_xyz": ("0.065", "-0.050", "0.035"),
        "camera_rotation_rpy": ("0.0", "0.0", "0.0"),
    }

    once = TUNING.apply_params(source, "S15", values)
    twice = TUNING.apply_params(once, "S15", values)

    assert once == twice
    assert "(:camera_offset_xyz 0.065 -0.050 0.035)" in once
