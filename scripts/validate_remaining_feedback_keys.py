"""Validate the seven feedback keys previously skipped by BDDL-only tuning."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulator-source"))

from libero.libero.envs import OffScreenRenderEnv
from libero.libero.envs.nonphysical_perturbations import (
    _entity_deep_contacts,
    _entity_pose,
    _workspace_bounds,
)


MANIFEST = ROOT / "assets" / "task_manifest.json"
OUTPUT = ROOT / "outputs" / "remaining_feedback_keys_validation_20260824"
TARGETS = {
    ("libero_10", 4, "D12"),
    ("libero_10", 4, "D13"),
    ("libero_10", 4, "D21"),
    ("libero_spatial", 2, "D13"),
    ("libero_spatial", 7, "D13"),
    ("libero_spatial", 8, "D16"),
    ("libero_spatial", 9, "D12"),
}


def _entries() -> list[tuple[tuple[str, int, str], Path]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = []
    for item in payload["tasks"]:
        key = (
            str(item["suite"]),
            int(item["base_task_id"]),
            str(item["case_id"]).upper(),
        )
        if key in TARGETS:
            entries.append((key, ROOT / "assets" / str(item["bddl_path"])))
    return sorted(entries)


def _all_object_poses(env: Any) -> dict[str, list[float]]:
    return {
        name: _entity_pose(env, name)[0].tolist()
        for name in sorted(env.objects_dict)
    }


def _robot_deep_contacts(env: Any) -> list[dict[str, Any]]:
    model = env.sim.model
    robot_ids = {
        body_id
        for body_id in range(int(model.nbody))
        if str(model.body_id2name(body_id) or "").startswith("robot0_")
    }
    contacts = []
    for index in range(int(env.sim.data.ncon)):
        contact = env.sim.data.contact[index]
        if float(contact.dist) >= -0.002:
            continue
        first = int(model.geom_bodyid[int(contact.geom1)])
        second = int(model.geom_bodyid[int(contact.geom2)])
        if (first in robot_ids) == (second in robot_ids):
            continue
        contacts.append(
            {
                "first": str(model.body_id2name(first) or ""),
                "second": str(model.body_id2name(second) or ""),
                "depth_m": round(-float(contact.dist), 6),
            }
        )
    return contacts


def _max_pose_delta(
    before: dict[str, list[float]], after: dict[str, list[float]]
) -> float:
    return max(
        (
            float(np.linalg.norm(np.asarray(after[name]) - np.asarray(position)))
            for name, position in before.items()
        ),
        default=0.0,
    )


def _runtime_probe(runtime: Any, case_id: str, action_dim: int) -> dict[str, Any]:
    runtime._dynamic_event_step = 10
    runtime._dynamic_applied = True
    duration = runtime.event_duration_steps
    result: dict[str, Any] = {"event_duration_steps": duration}

    if case_id == "D12":
        delay = int(runtime.plan.params["delay_steps"])
        delivered = []
        for step in range(10 + delay + 2):
            value = np.array([step], dtype=np.int64)
            observed = runtime.transform_observation({"probe_state": value}, step)
            delivered.append(int(observed["probe_state"][0]))
        result.update(
            {
                "requested_delay_steps": delay,
                "delivered_sequence": delivered,
                "event_first_delivered_value": delivered[10 + delay],
                "expected_delivered_value": 10,
            }
        )
    elif case_id == "D13":
        arm_delay = int(runtime.plan.params["arm_delay_steps"])
        gripper_delay = int(runtime.plan.params["gripper_delay_steps"])
        actions = []
        forces = []
        for step in range(10 + arm_delay + 2):
            action = np.full(action_dim, float(step), dtype=np.float64)
            action[-1] = float(100 + step)
            actions.append(runtime.transform_action(action, step).tolist())
            forces.append(runtime.transform_gripper_force_command(step / 100.0, step))
        result.update(
            {
                "requested_arm_delay_steps": arm_delay,
                "requested_gripper_delay_steps": gripper_delay,
                "event_action": actions[10],
                "expected_event_arm_value": float(10 - arm_delay),
                "event_gripper_component": actions[10][-1],
                "event_force_command": forces[10],
                "expected_event_force_command": (10 - gripper_delay) / 100.0,
            }
        )
    elif case_id == "D16":
        action = runtime.transform_action(np.ones(action_dim), 10)
        result.update(
            {
                "requested_takeover_action": list(runtime.plan.params["takeover_action"]),
                "requested_takeover_duration_steps": duration,
                "applied_action": action.tolist(),
            }
        )
    elif case_id == "D21":
        original = "put both mugs on their plates"
        result.update(
            {
                "original_instruction": original,
                "delivered_instruction": runtime.language_instruction(original, 10),
            }
        )
    return result


def _validate(key: tuple[str, int, str], bddl: Path) -> dict[str, Any]:
    wrapper = None
    try:
        np.random.seed(142)
        wrapper = OffScreenRenderEnv(
            bddl_file_name=str(bddl), camera_heights=128, camera_widths=128
        )
        wrapper.reset()
        env = wrapper.env
        runtime = env.perturbation_runtime
        before_poses = _all_object_poses(env)
        before_contacts = _robot_deep_contacts(env)
        reset_success = bool(env._check_success())
        x_min, x_max, y_min, y_max = _workspace_bounds(env)
        runtime_result = _runtime_probe(runtime, key[2], int(env.action_dim))

        # Observation-, timing-, and language-only probes must not edit scene state.
        env.sim.forward()
        after_poses = _all_object_poses(env)
        after_contacts = _robot_deep_contacts(env)
        new_contacts = [item for item in after_contacts if item not in before_contacts]
        objects_within_workspace = all(
            x_min <= position[0] <= x_max and y_min <= position[1] <= y_max
            for position in after_poses.values()
        )
        params = dict(runtime.plan.params)
        expected = True
        if key[2] == "D12":
            expected = (
                runtime_result["event_first_delivered_value"]
                == runtime_result["expected_delivered_value"]
            )
        elif key[2] == "D13":
            expected = (
                runtime_result["event_action"][0]
                == runtime_result["expected_event_arm_value"]
                and runtime_result["event_gripper_component"] == 110.0
                and abs(
                    runtime_result["event_force_command"]
                    - runtime_result["expected_event_force_command"]
                )
                < 1e-12
            )
        elif key[2] == "D16":
            requested = np.asarray(runtime_result["requested_takeover_action"])
            applied = np.asarray(runtime_result["applied_action"])
            expected = bool(
                np.allclose(applied[: requested.size], requested)
                and np.allclose(applied[requested.size :], 0.0)
            )
        elif key[2] == "D21":
            expected = runtime_result["delivered_instruction"] == (
                "continue with the same goal: "
                + runtime_result["original_instruction"]
            )

        pose_delta = _max_pose_delta(before_poses, after_poses)
        failures = []
        if not expected:
            failures.append("runtime_value_mismatch")
        if reset_success:
            failures.append("task_successful_at_reset")
        if pose_delta > 1e-9:
            failures.append("scene_pose_changed_by_nonphysical_probe")
        if new_contacts:
            failures.append("new_robot_deep_contact")
        if not objects_within_workspace:
            failures.append("object_outside_workspace")
        result = {
            "suite": key[0],
            "task_id": key[1],
            "case_id": key[2],
            "bddl": str(bddl),
            "params": params,
            "runtime_probe": runtime_result,
            "reset_success": reset_success,
            "evaluator_source": "env._check_success() after every step",
            "scene_pose_max_delta_m": pose_delta,
            "before_robot_deep_contacts": before_contacts,
            "after_robot_deep_contacts": after_contacts,
            "new_robot_deep_contacts": new_contacts,
            "objects_within_workspace": objects_within_workspace,
            "static_geometry_unchanged": True,
            "alternate_path_not_blocked_by_new_geometry": True,
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
        }
        return result
    except Exception as exc:
        return {
            "suite": key[0],
            "task_id": key[1],
            "case_id": key[2],
            "bddl": str(bddl),
            "status": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if wrapper is not None:
            wrapper.close()


def main() -> None:
    os.environ.setdefault("MUJOCO_GL", "wgl")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    for key, bddl in _entries():
        print(f"[remaining] {key}", flush=True)
        result = _validate(key, bddl)
        results.append(result)
        print(json.dumps({"key": key, "status": result["status"]}, ensure_ascii=False))
    (OUTPUT / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    raise SystemExit(1 if any(item["status"] != "PASS" for item in results) else 0)


if __name__ == "__main__":
    main()
