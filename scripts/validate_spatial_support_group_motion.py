"""Validate Spatial task3/task5 S01/D01 rigid support-group motion at seed 143."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_ROOT = ROOT / "simulator-source"
MANIFEST = ROOT / "assets" / "task_manifest.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "spatial_support_group_seed143_20260902"
SEED = 143
CASES = ((3, "S01"), (3, "D01"), (5, "S01"), (5, "D01"))
SUPPORTS = {3: "cookies_1", 5: "glazed_rim_porcelain_ramekin_1"}
TARGET = "akita_black_bowl_1"

for path in (ROOT, SIMULATOR_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

os.environ.setdefault("LIBERO_PRO_ROOT", str(SIMULATOR_ROOT))
os.environ.setdefault("LIBERO_REMOTE_TASK_MANIFEST", str(MANIFEST))
os.environ.setdefault("MUJOCO_GL", "wgl")


def _configure_libero(output: Path) -> None:
    config_dir = output / "libero_config"
    config_dir.mkdir(parents=True, exist_ok=True)
    benchmark_root = SIMULATOR_ROOT / "libero" / "libero"
    (config_dir / "config.yaml").write_text(
        "\n".join(
            (
                "assets: {}".format(benchmark_root / "assets"),
                "bddl_files: {}".format(benchmark_root / "bddl_files"),
                "benchmark_root: {}".format(benchmark_root),
                "datasets: {}".format(SIMULATOR_ROOT / "libero" / "datasets"),
                "init_states: {}".format(benchmark_root / "init_files"),
                "",
            )
        ),
        encoding="utf-8",
    )
    os.environ["LIBERO_CONFIG_PATH"] = str(config_dir)


_configure_libero(DEFAULT_OUTPUT)

from libero.libero.envs.nonphysical_perturbations import (  # noqa: E402
    _entity_deep_contacts,
    _entity_has_support_contact,
    _entity_pose,
    _quaternion_conjugate,
    _quaternion_multiply,
    _quaternion_to_rotation_matrix,
)
from libero_remote.environment.libero import LiberoEnvironmentAdapter  # noqa: E402


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--settle-steps", type=int, default=200)
    parser.add_argument("--image-size", type=int, default=360)
    return parser.parse_args()


def _manifest_entry(task_id: int, case_id: str) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    matches = [
        item
        for item in manifest["tasks"]
        if item["suite"] == "libero_spatial"
        and int(item["base_task_id"]) == task_id
        and item["case_id"] == case_id
    ]
    if len(matches) != 1:
        raise RuntimeError("Expected one manifest entry for task{}/{}".format(task_id, case_id))
    return matches[0]


def _unwrap(wrapper: Any) -> Any:
    current = wrapper
    for _ in range(5):
        if hasattr(current, "obj_body_id") and hasattr(current, "sim"):
            return current
        current = getattr(current, "env", None)
    raise RuntimeError("Cannot resolve underlying LIBERO environment")


def _create(task_id: int, variant: str, bddl_path: Path, image_size: int) -> LiberoEnvironmentAdapter:
    adapter = LiberoEnvironmentAdapter()
    adapter.create(
        {
            "suite": "libero_spatial",
            "task_id": task_id,
            "variant": variant,
            "_bddl_path": str(bddl_path),
            "init_state_id": 0,
            "seed": SEED,
            "camera_names": ["agentview"],
            "camera_height": image_size,
            "camera_width": image_size,
            "max_steps": 500,
            "control_mode": "absolute",
        }
    )
    return adapter


def _frame(env: Any) -> np.ndarray:
    env._update_observables(force=True)
    frame = env._get_observations().get("agentview_image")
    if not isinstance(frame, np.ndarray) or frame.ndim != 3:
        raise RuntimeError("agentview_image is missing")
    return frame.copy()


def _save_frame(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame[::-1, :, ::-1]):
        raise RuntimeError("Failed to write {}".format(path))


def _relative_pose(env: Any, support: str) -> tuple[np.ndarray, np.ndarray]:
    support_pose = _entity_pose(env, support)
    target_pose = _entity_pose(env, TARGET)
    support_rotation = _quaternion_to_rotation_matrix(support_pose[1])
    relative_position = support_rotation.T @ (target_pose[0] - support_pose[0])
    relative_quaternion = _quaternion_multiply(
        _quaternion_conjugate(support_pose[1]), target_pose[1]
    )
    if relative_quaternion[0] < 0.0:
        relative_quaternion *= -1.0
    return relative_position, relative_quaternion


def _relative_error(
    reference: tuple[np.ndarray, np.ndarray], current: tuple[np.ndarray, np.ndarray]
) -> dict[str, float]:
    quaternion_delta = min(
        float(np.linalg.norm(current[1] - reference[1])),
        float(np.linalg.norm(current[1] + reference[1])),
    )
    return {
        "position_m": float(np.linalg.norm(current[0] - reference[0])),
        "quaternion_l2": quaternion_delta,
    }


def _positions(env: Any) -> dict[str, np.ndarray]:
    return {
        name: _entity_pose(env, name)[0]
        for name in sorted(getattr(env, "objects_dict", {}))
        if name in getattr(env, "obj_body_id", {})
    }


def _audit(task_id: int, case_id: str, output: Path, settle_steps: int, image_size: int) -> dict[str, Any]:
    entry = _manifest_entry(task_id, case_id)
    active_path = ROOT / "assets" / entry["bddl_path"]
    base_path = active_path.parent.parent / "00_base" / active_path.name.replace(case_id + "__", "BASE__")
    support = SUPPORTS[task_id]

    base_adapter = _create(task_id, "base", base_path, image_size)
    try:
        base_env = _unwrap(base_adapter._env)
        base_support_pose = _entity_pose(base_env, support)
        base_relative = _relative_pose(base_env, support)
        base_frame = _frame(base_env)
    finally:
        base_adapter.close()

    active_adapter = _create(task_id, case_id, active_path, image_size)
    try:
        env = _unwrap(active_adapter._env)
        runtime = env.perturbation_runtime
        pre_positions = _positions(env)
        pre_frame = _frame(env)
        if case_id == "D01":
            before_relative = _relative_pose(env, support)
            before_support_pose = _entity_pose(env, support)
            env.sim.data.site_xpos[int(env.robots[0].eef_site_id)] = _entity_pose(env, TARGET)[0]
            trigger_met = bool(runtime._dynamic_triggered(env, 1))
            runtime.before_simulation_step(env, 1)
        else:
            before_relative = base_relative
            before_support_pose = base_support_pose
            trigger_met = None

        immediate_relative = _relative_pose(env, support)
        immediate_support_pose = _entity_pose(env, support)
        immediate_frame = _frame(env)
        entry_positions = _positions(env)
        maxima = {name: 0.0 for name in entry_positions}
        maximum_z_rise = {name: 0.0 for name in entry_positions}
        finite = True
        deep_contacts: dict[str, list[dict[str, Any]]] = {}
        for _ in range(settle_steps):
            env.sim.step()
            finite = finite and all(
                np.isfinite(np.asarray(value)).all()
                for value in (env.sim.data.qpos, env.sim.data.qvel, env.sim.data.body_xpos)
            )
            for name, start in entry_positions.items():
                position = _entity_pose(env, name)[0]
                maxima[name] = max(maxima[name], float(np.linalg.norm(position - start)))
                maximum_z_rise[name] = max(maximum_z_rise[name], float(position[2] - start[2]))
                contacts = _entity_deep_contacts(env, name)
                if contacts:
                    deep_contacts[name] = contacts

        settled_relative = _relative_pose(env, support)
        settled_frame = _frame(env)
        immediate_error = _relative_error(before_relative, immediate_relative)
        settled_error = _relative_error(immediate_relative, settled_relative)
        support_delta = immediate_support_pose[0] - before_support_pose[0]
        expected_distance = float(np.linalg.norm(runtime.plan.params["offset_xy"]))
        actual_distance = float(np.linalg.norm(support_delta[:2]))
        non_group_motion = {
            name: value
            for name, value in maxima.items()
            if name not in {TARGET, support} and value > 0.02
        }
        jumpers = {name: value for name, value in maximum_z_rise.items() if value > 0.02}
        events = list(runtime.diagnostics()["events"])
        group_events = [event for event in events if event.get("event") == "support_group_transform"]
        failures = []
        if case_id == "D01" and not trigger_met:
            failures.append("trigger_not_met")
        if len(group_events) != 1:
            failures.append("support_group_event_count")
        if abs(actual_distance - expected_distance) > 0.0005:
            failures.append("support_displacement")
        if immediate_error["position_m"] > 1e-8 or immediate_error["quaternion_l2"] > 1e-8:
            failures.append("relative_pose_changed_during_transform")
        if settled_error["position_m"] > 0.015 or settled_error["quaternion_l2"] > 0.10:
            failures.append("relative_pose_unstable")
        target_support_contact = bool(
            env.check_contact(env.get_object(TARGET), env.get_object(support))
        )
        if not target_support_contact:
            failures.append("target_not_supported")
        if not _entity_has_support_contact(env, support):
            failures.append("support_not_grounded")
        if deep_contacts:
            failures.append("deep_penetration")
        if not finite:
            failures.append("nonfinite_scene")
        if non_group_motion:
            failures.append("non_group_object_motion")
        if jumpers:
            failures.append("object_jump")
        for label, frame in (("base", base_frame), ("pre", pre_frame), ("immediate", immediate_frame), ("settled", settled_frame)):
            if float(np.std(frame)) <= 1.0:
                failures.append(label + "_blank_render")
            _save_frame(output / "frames" / "task{}_{}_{}.png".format(task_id, case_id, label), frame)

        return {
            "task_id": task_id,
            "case_id": case_id,
            "seed": SEED,
            "init_state_id": 0,
            "python": sys.version,
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
            "trigger_met": trigger_met,
            "support_object": support,
            "support_delta_xyz": support_delta.tolist(),
            "expected_displacement_m": expected_distance,
            "actual_displacement_m": actual_distance,
            "immediate_relative_error": immediate_error,
            "settled_relative_error": settled_error,
            "support_contact": _entity_has_support_contact(env, support),
            "target_support_contact": target_support_contact,
            "deep_contacts": deep_contacts,
            "non_group_motion": non_group_motion,
            "jumpers": jumpers,
            "maximum_displacements_m": maxima,
            "events": group_events,
            "pre_positions": {name: value.tolist() for name, value in pre_positions.items()},
        }
    finally:
        active_adapter.close()


def main() -> None:
    args = _args()
    _configure_libero(args.output)
    results = []
    for task_id, case_id in CASES:
        print("[support-group] task{} {}".format(task_id, case_id), flush=True)
        try:
            result = _audit(task_id, case_id, args.output, args.settle_steps, args.image_size)
        except Exception as error:
            result = {
                "task_id": task_id,
                "case_id": case_id,
                "seed": SEED,
                "status": "ERROR",
                "error": "{}: {}".format(type(error).__name__, error),
            }
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    report = {
        "audit": "spatial_task3_task5_support_group_seed143",
        "results": results,
        "passed": sum(item["status"] == "PASS" for item in results),
        "total": len(results),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"passed": report["passed"], "total": report["total"]}), flush=True)
    if report["passed"] != report["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
