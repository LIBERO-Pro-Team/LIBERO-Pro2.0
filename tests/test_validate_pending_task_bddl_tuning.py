from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_pending_task_bddl_tuning.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_pending_task_bddl_tuning", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_validation_specs_select_only_recorded_bddl_tuning_tasks(tmp_path: Path) -> None:
    report = tmp_path / "change_report.json"
    changes = [
        {"suite": "libero_goal", "task_id": 0, "case_id": "S15", "bddl": "a.bddl", "fields": {}},
        {"suite": "libero_goal", "task_id": 1, "case_id": "D19", "bddl": "b.bddl", "fields": {}},
    ]
    report.write_text(json.dumps({"changes": changes}), encoding="utf-8")
    specs = VALIDATOR.load_validation_specs(report_path=report)
    d19_specs = VALIDATOR.load_validation_specs(case_ids={"D19"}, report_path=report)

    assert len(specs) == 2
    assert len(d19_specs) == 1
    assert {spec.case_id for spec in d19_specs} == {"D19"}
    assert ("libero_10", 0, "D19") not in {
        (spec.suite, spec.task_id, spec.case_id) for spec in specs
    }


def test_previous_bddl_comes_from_recorded_old_field_values() -> None:
    source = """(define (problem sample)
  (:perturbation_config
    (:perturbations
      (S15
        (:params
          (:camera_offset_xyz 0.065 -0.050 0.035)
          (:camera_rotation_rpy 0.0 0.0 0.0)
        )
      )
    )
  )
)
"""
    spec = VALIDATOR.ValidationSpec(
        suite="libero_goal",
        task_id=0,
        case_id="S15",
        bddl=Path("sample.bddl"),
        fields={
            "camera_offset_xyz": {
                "old": ["0.045", "-0.035", "0.025"],
                "new": ["0.065", "-0.050", "0.035"],
            }
        },
    )

    previous = VALIDATOR.previous_bddl_text(source, spec)

    assert "(:camera_offset_xyz 0.045 -0.035 0.025)" in previous
    assert "(:camera_offset_xyz 0.065 -0.050 0.035)" not in previous


def test_d19_safety_rejects_penetration_instability_and_collateral_motion() -> None:
    safe = VALIDATOR.evaluate_d19_safety(
        target_penetrating=False,
        support_gap_m=0.004,
        target_speed_m_s=0.02,
        receiver_distance_m=0.11,
        unrelated_max_displacement_m=0.003,
    )
    unsafe = VALIDATOR.evaluate_d19_safety(
        target_penetrating=True,
        support_gap_m=0.02,
        target_speed_m_s=0.4,
        receiver_distance_m=0.24,
        unrelated_max_displacement_m=0.03,
        task_success_after_settle=True,
    )

    assert safe == {"status": "PASS", "reasons": []}
    assert unsafe["status"] == "FAIL"
    assert set(unsafe["reasons"]) == {
        "target_penetration",
        "unsupported_target",
        "unstable_target",
        "receiver_too_far",
        "collateral_motion",
        "task_already_successful",
    }


def test_visual_metrics_compare_previous_and_tuned_frames_to_the_same_base() -> None:
    base = np.zeros((4, 4, 3), dtype=np.uint8)
    previous = base.copy()
    previous[:, :1] = 20
    tuned = base.copy()
    tuned[:, :2] = 30

    metrics = VALIDATOR.visual_metrics(base, previous, tuned)

    assert metrics["previous_mean_abs_delta"] == 5.0
    assert metrics["tuned_mean_abs_delta"] == 15.0
    assert metrics["tuned_vs_previous_mean_abs_delta"] == 10.0
    assert metrics["previous_changed_ratio"] == 0.25
    assert metrics["tuned_changed_ratio"] == 0.5
