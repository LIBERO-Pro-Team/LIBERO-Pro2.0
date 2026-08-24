"""Re-render D19 feedback tasks that were previously skipped by the tuning pass."""

from __future__ import annotations

import json
import os
import sys
import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "simulator-source"))

import validate_pending_task_bddl_tuning as validator
from libero.libero.envs.nonphysical_perturbations import (
    _entity_deep_contacts,
    _entity_pose,
    _functional_anchor,
    _goal_articulation_targets,
    _workspace_bounds,
)


FEEDBACK_SOURCE = Path(r"C:\Users\racin\Desktop\待修改.md")
OUTPUT = ROOT / "outputs" / "d19_feedback_validation_20260824"
ALL_TASKS = False


def _feedback_targets() -> set[tuple[str, int]]:
    with FEEDBACK_SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            (str(row["suite"]), int(row["task_id"]))
            for row in csv.DictReader(handle, delimiter="\t")
            if str(row["扰动"]).upper() == "D19"
        }


def _specs() -> list[validator.ValidationSpec]:
    manifest = json.loads(validator.MANIFEST.read_text(encoding="utf-8"))
    feedback_targets = _feedback_targets()
    specs = []
    for item in manifest["tasks"]:
        key = (str(item["suite"]), int(item["base_task_id"]))
        if (
            str(item["case_id"]).upper() != "D19"
            or (not ALL_TASKS and key not in feedback_targets)
        ):
            continue
        specs.append(
            validator.ValidationSpec(
                suite=key[0],
                task_id=key[1],
                case_id="D19",
                bddl=ROOT / "assets" / str(item["bddl_path"]),
                fields={},
            )
        )
    return sorted(specs, key=lambda item: (item.suite, item.task_id))


def _run_articulation(spec: validator.ValidationSpec, api: dict) -> dict[str, object]:
    case_dir = validator._case_directory(OUTPUT, spec)
    wrapper = None
    control_wrapper = None
    try:
        wrapper, observation = validator._reset_environment(
            spec.bddl, seed=142, image_size=256, api=api
        )
        env = wrapper.env
        runtime = env.perturbation_runtime
        targets = _goal_articulation_targets(env)
        if not targets:
            raise RuntimeError("D19 articulation task has no goal fixture")
        target = targets[0][0]
        before_position, _ = _entity_pose(env, target)
        before_contacts = _entity_deep_contacts(env, target)
        before_objects = {
            name: _entity_pose(env, name)[0]
            for name in sorted(env.objects_dict)
            if name != target
        }
        before_frame = np.asarray(observation["agentview_image"]).copy()

        control_wrapper, _ = validator._reset_environment(
            spec.bddl, seed=142, image_size=256, api=api
        )
        control_env = control_wrapper.env
        neutral_action = np.zeros(int(control_env.action_dim), dtype=np.float64)
        for _ in range(100):
            control_wrapper.step(neutral_action)
        control_positions = {
            name: _entity_pose(control_env, name)[0]
            for name in before_objects
        }

        runtime._dynamic_triggered = lambda _env, _step: True
        runtime.before_simulation_step(env, 0)
        after_position, _ = _entity_pose(env, target)
        after_contacts = _entity_deep_contacts(env, target)
        env._update_observables(force=True)
        after_frame = np.asarray(env._get_observations()["agentview_image"]).copy()

        neutral_action = np.zeros(int(env.action_dim), dtype=np.float64)
        for _ in range(100):
            wrapper.step(neutral_action)
        env.sim.forward()
        settled_position, _ = _entity_pose(env, target)
        settled_contacts = _entity_deep_contacts(env, target)
        anchor, anchor_name = _functional_anchor(env, target)
        eef = np.asarray(
            env.sim.data.site_xpos[env.robots[0].eef_site_id], dtype=np.float64
        )
        x_min, x_max, y_min, y_max = _workspace_bounds(env)
        within_workspace = bool(
            x_min <= settled_position[0] <= x_max
            and y_min <= settled_position[1] <= y_max
        )
        unrelated = {
            name: float(np.linalg.norm(_entity_pose(env, name)[0] - control_positions[name]))
            for name, before in before_objects.items()
        }
        before_pairs = {
            (item["first"], item["second"]) for item in before_contacts
        }
        new_contacts = [
            item
            for item in after_contacts + settled_contacts
            if (item["first"], item["second"]) not in before_pairs
        ]
        displacement = float(np.linalg.norm(settled_position[:2] - before_position[:2]))
        eef_anchor_distance = float(np.linalg.norm(eef - anchor))
        task_success = bool(env._check_success())
        reasons = []
        if new_contacts:
            reasons.append("new_deep_penetration")
        if not within_workspace:
            reasons.append("outside_workspace")
        if not 0.02 <= displacement <= 0.18:
            reasons.append("fixture_displacement_out_of_range")
        if eef_anchor_distance > 0.80:
            reasons.append("articulation_anchor_unreachable")
        if max(unrelated.values(), default=0.0) > 0.01:
            reasons.append("collateral_motion")
        if task_success:
            reasons.append("task_already_successful")
        validator._write_frame(before_frame, case_dir / "before.png", api)
        validator._write_frame(after_frame, case_dir / "after.png", api)
        current = {
            "target": target,
            "anchor": anchor_name,
            "before_xyz": before_position.tolist(),
            "after_xyz": after_position.tolist(),
            "settled_xyz": settled_position.tolist(),
            "displacement_xy_m": round(displacement, 6),
            "eef_anchor_distance_m": round(eef_anchor_distance, 6),
            "within_workspace": within_workspace,
            "new_deep_contacts": new_contacts,
            "unrelated_displacements_m": {
                name: round(value, 6) for name, value in unrelated.items()
            },
            "control_settled_xyz": {
                name: value.tolist() for name, value in control_positions.items()
            },
            "task_success_after_settle": task_success,
            "events": list(runtime.events),
            "safety": {"status": "PASS" if not reasons else "FAIL", "reasons": reasons},
        }
        result = {
            "suite": spec.suite,
            "task_id": spec.task_id,
            "case_id": spec.case_id,
            "bddl": str(spec.bddl),
            "current": current,
            "status": current["safety"]["status"],
            "before_image": str(case_dir / "before.png"),
            "after_image": str(case_dir / "after.png"),
        }
        (case_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
    finally:
        if wrapper is not None:
            wrapper.close()
        if control_wrapper is not None:
            control_wrapper.close()


def _run_placement(
    spec: validator.ValidationSpec, api: dict
) -> dict[str, object]:
    case_dir = validator._case_directory(OUTPUT, spec)
    control = validator._run_d19_variant(
        spec.bddl,
        seed=142,
        image_size=256,
        api=api,
        apply_event=False,
        hold_target=True,
    )
    current = validator._run_d19_variant(
        spec.bddl,
        seed=142,
        image_size=256,
        api=api,
        apply_event=True,
        hold_target=False,
    )
    validator._apply_d19_control_comparison(current, control)
    validator._write_frame(current.pop("preplace_frame"), case_dir / "preplace.png", api)
    validator._write_frame(current.pop("entered_frame"), case_dir / "entered.png", api)
    validator._write_frame(current.pop("settled_frame"), case_dir / "settled.png", api)
    control.pop("preplace_frame")
    control.pop("entered_frame")
    control.pop("settled_frame")
    control.pop("unrelated_settled_xyz")
    result = {
        "suite": spec.suite,
        "task_id": spec.task_id,
        "case_id": spec.case_id,
        "bddl": str(spec.bddl),
        "control": control,
        "current": current,
        "status": current["safety"]["status"],
        "preplace_image": str(case_dir / "preplace.png"),
        "entered_image": str(case_dir / "entered.png"),
        "settled_image": str(case_dir / "settled.png"),
    }
    (case_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def main() -> None:
    global ALL_TASKS, OUTPUT

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Validate all 40 D19 tasks.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    ALL_TASKS = bool(args.all)
    OUTPUT = args.output.resolve()
    os.environ.setdefault("MUJOCO_GL", "wgl")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    api = validator._runtime_api()
    results = []
    for spec in _specs():
        print(f"[d19] {spec.suite} task{spec.task_id}", flush=True)
        try:
            result = (
                _run_articulation(spec, api)
                if spec.suite == "libero_goal" and spec.task_id in {0, 7}
                else _run_placement(spec, api)
            )
        except Exception as exc:
            result = {
                "suite": spec.suite,
                "task_id": spec.task_id,
                "case_id": spec.case_id,
                "bddl": str(spec.bddl),
                "status": "ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            }
        results.append(result)
        tuned = result.get("current", {})
        print(
            json.dumps(
                {
                    "key": [spec.suite, spec.task_id],
                    "status": result["status"],
                    "target": tuned.get("target"),
                    "receiver": tuned.get("receiver"),
                    "events": tuned.get("events"),
                    "safety": tuned.get("safety"),
                    "support_gap_m": tuned.get("support_gap_m"),
                    "receiver_distance_xy_m": tuned.get("receiver_distance_xy_m"),
                    "within_workspace": tuned.get("within_workspace"),
                    "task_success_after_settle": tuned.get("task_success_after_settle"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    report = OUTPUT / "render_results.json"
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1 if any(item["status"] != "PASS" for item in results) else 0)


if __name__ == "__main__":
    main()
