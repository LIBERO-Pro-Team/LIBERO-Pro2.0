"""Render and audit the task5 Spatial S04 complete support-group swap."""

from __future__ import annotations

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
DEFAULT_OUTPUT = ROOT / "outputs" / "spatial_task5_s04_support_swap_seed143_20260907"
SEED = 143
INIT_STATE_ID = 0
TARGETS = ("akita_black_bowl_1", "akita_black_bowl_2")
SUPPORTS = ("glazed_rim_porcelain_ramekin_1", "cookies_1")
GROUP_ENTITIES = (*TARGETS, *SUPPORTS)

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
                f"assets: {benchmark_root / 'assets'}",
                f"bddl_files: {benchmark_root / 'bddl_files'}",
                f"benchmark_root: {benchmark_root}",
                f"datasets: {SIMULATOR_ROOT / 'libero' / 'datasets'}",
                f"init_states: {benchmark_root / 'init_files'}",
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
from libero.libero.envs.perturbation_config import (  # noqa: E402
    parse_bddl_perturbation_config,
)
from libero_remote.environment.libero import LiberoEnvironmentAdapter  # noqa: E402


def _unwrap(wrapper: Any) -> Any:
    current = wrapper
    for _ in range(6):
        if hasattr(current, "obj_body_id") and hasattr(current, "sim"):
            return current
        current = getattr(current, "env", None)
    raise RuntimeError("Cannot resolve underlying LIBERO environment")


def _create(path: Path, variant: str, image_size: int) -> LiberoEnvironmentAdapter:
    adapter = LiberoEnvironmentAdapter()
    adapter.create(
        {
            "suite": "libero_spatial",
            "task_id": 5,
            "variant": variant,
            "_bddl_path": str(path),
            "init_state_id": INIT_STATE_ID,
            "seed": SEED,
            "camera_names": ["agentview"],
            "camera_height": image_size,
            "camera_width": image_size,
            "max_steps": 220,
            "control_mode": "absolute",
        }
    )
    return adapter


def _positions(env: Any) -> dict[str, np.ndarray]:
    return {
        name: _entity_pose(env, name)[0]
        for name in getattr(env, "objects_dict", {})
        if name in getattr(env, "obj_body_id", {})
    }


def _relative_pose(env: Any, target: str, support: str) -> tuple[np.ndarray, np.ndarray]:
    support_position, support_quaternion = _entity_pose(env, support)
    target_position, target_quaternion = _entity_pose(env, target)
    support_rotation = _quaternion_to_rotation_matrix(support_quaternion)
    relative_position = support_rotation.T @ (target_position - support_position)
    relative_quaternion = _quaternion_multiply(
        _quaternion_conjugate(support_quaternion), target_quaternion
    )
    if relative_quaternion[0] < 0.0:
        relative_quaternion *= -1.0
    return relative_position, relative_quaternion


def _pair_contact(env: Any, first: str, second: str, tolerance: float = 0.004) -> bool:
    model = env.sim.model
    body_ids = {
        first: set(RUNTIME_ENTITY_BODY_IDS(env, first)),
        second: set(RUNTIME_ENTITY_BODY_IDS(env, second)),
    }
    geom_body_ids = np.asarray(model.geom_bodyid, dtype=int)
    for index in range(int(getattr(env.sim.data, "ncon", 0))):
        contact = env.sim.data.contact[index]
        body_one = int(geom_body_ids[int(contact.geom1)])
        body_two = int(geom_body_ids[int(contact.geom2)])
        if (
            (body_one in body_ids[first] and body_two in body_ids[second])
            or (body_two in body_ids[first] and body_one in body_ids[second])
        ) and float(contact.dist) <= tolerance:
            return True
    return False


def RUNTIME_ENTITY_BODY_IDS(env: Any, name: str) -> tuple[int, ...]:
    root = int(env.obj_body_id[name])
    model = env.sim.model
    if not hasattr(model, "nbody") or not hasattr(model, "body_parentid"):
        return (root,)
    ids = [root]
    changed = True
    while changed:
        changed = False
        for body_id in range(int(model.nbody)):
            if body_id in ids:
                continue
            if int(model.body_parentid[body_id]) in ids:
                ids.append(body_id)
                changed = True
    return tuple(ids)


def _frame(env: Any) -> np.ndarray:
    env._update_observables(force=True)
    frame = env._get_observations().get("agentview_image")
    if not isinstance(frame, np.ndarray) or frame.ndim != 3:
        raise RuntimeError("agentview_image is missing")
    return frame.copy()


def _save_frame(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame[::-1, :, ::-1]):
        raise RuntimeError(f"Failed to write {path}")


def _manifest_path() -> Path:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    matches = [
        item
        for item in manifest["tasks"]
        if item["suite"] == "libero_spatial"
        and int(item["base_task_id"]) == 5
        and item["case_id"] == "S04"
    ]
    if len(matches) != 1:
        raise RuntimeError("Expected one Spatial task5/S04 manifest entry")
    return ROOT / "assets" / str(matches[0]["bddl_path"])


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--settle-steps", type=int, default=160)
    parser.add_argument("--image-size", type=int, default=360)
    args = parser.parse_args()
    _configure_libero(args.output)

    active_path = _manifest_path()
    base_path = active_path.parent.parent / "00_base" / active_path.name.replace("S04__", "BASE__")
    active_config = parse_bddl_perturbation_config(active_path)
    s04_entry = next(
        item
        for item in active_config["perturbations"]
        if str(item[0]).upper() == "S04"
    )
    s04_fields = {}
    for field in s04_entry[1:]:
        s04_fields.update(field)
    params = dict(s04_fields.get("params", {}))

    base_adapter = _create(base_path, "base", args.image_size)
    try:
        base_env = _unwrap(base_adapter._env)
        base_positions = _positions(base_env)
        base_relative = {
            target: _relative_pose(base_env, target, support)
            for target, support in zip(TARGETS, SUPPORTS)
        }
        base_frame = _frame(base_env)
    finally:
        base_adapter.close()

    active_adapter = _create(active_path, "S04", args.image_size)
    try:
        env = _unwrap(active_adapter._env)
        swap_events = [
            event
            for event in env.perturbation_runtime.diagnostics()["events"]
            if event.get("event") == "support_group_swap"
        ]
        if len(swap_events) != 1:
            raise RuntimeError("Expected exactly one support_group_swap diagnostic event")
        swap_event = swap_events[0]
        immediate_positions = _positions(env)
        immediate_relative = {
            target: _relative_pose(env, target, support)
            for target, support in zip(TARGETS, SUPPORTS)
        }
        immediate_frame = _frame(env)
        for _ in range(args.settle_steps):
            env.sim.step()
        settled_positions = _positions(env)
        settled_frame = _frame(env)
        finite = all(
            np.isfinite(np.asarray(value)).all()
            for value in (env.sim.data.qpos, env.sim.data.qvel, env.sim.data.body_xpos)
        )
        relative_position_errors = {
            target: float(np.linalg.norm(immediate_relative[target][0] - base_relative[target][0]))
            for target in TARGETS
        }
        relative_quaternion_errors = {
            target: min(
                float(np.linalg.norm(immediate_relative[target][1] - base_relative[target][1])),
                float(np.linalg.norm(immediate_relative[target][1] + base_relative[target][1])),
            )
            for target in TARGETS
        }
        expected_support_xy = {
            SUPPORTS[0]: np.asarray(swap_event["support_positions_before"][SUPPORTS[1]])[:2],
            SUPPORTS[1]: np.asarray(swap_event["support_positions_before"][SUPPORTS[0]])[:2],
        }
        support_xy_errors = {
            support: float(
                np.linalg.norm(immediate_positions[support][:2] - expected_support_xy[support])
            )
            for support in SUPPORTS
        }
        own_z_errors = {
            support: abs(float(immediate_positions[support][2] - base_positions[support][2]))
            for support in SUPPORTS
        }
        deep_contacts = {
            name: _entity_deep_contacts(env, name)
            for name in GROUP_ENTITIES
            if _entity_deep_contacts(env, name)
        }
        target_support_contacts = {
            target: _pair_contact(env, target, support)
            for target, support in zip(TARGETS, SUPPORTS)
        }
        support_ground_contacts = {
            support: _entity_has_support_contact(env, support) for support in SUPPORTS
        }
        unrelated_displacements = {
            name: float(np.linalg.norm(_entity_pose(env, name)[0] - base_positions[name]))
            for name in getattr(env, "objects_dict", {})
            if name not in GROUP_ENTITIES and name in getattr(env, "obj_body_id", {})
        }
        failures = []
        if params.get("swap_support_groups") is not True:
            failures.append("task_opt_in_missing")
        if tuple(params.get("support_objects", ())) != SUPPORTS:
            failures.append("support_objects_mismatch")
        if params.get("support_ground_surface") != "main_table":
            failures.append("ground_surface_mismatch")
        if max(support_xy_errors.values()) > 1e-5:
            failures.append("support_xy_exchange")
        if max(own_z_errors.values()) > 1e-5:
            failures.append("support_z_changed")
        if max(relative_position_errors.values()) > 1e-5:
            failures.append("relative_position_changed")
        if max(relative_quaternion_errors.values()) > 1e-4:
            failures.append("relative_quaternion_changed")
        if not all(target_support_contacts.values()):
            failures.append("target_support_contact_missing")
        if not all(support_ground_contacts.values()):
            failures.append("support_ground_contact_missing")
        if deep_contacts:
            failures.append("deep_penetration")
        if not finite:
            failures.append("nonfinite_scene")
        if any(value > 0.025 for value in unrelated_displacements.values()):
            failures.append("unrelated_object_motion")
        for label, frame in (
            ("base", base_frame),
            ("immediate", immediate_frame),
            ("settled", settled_frame),
        ):
            if float(np.std(frame)) <= 1.0:
                failures.append(label + "_blank_render")
            _save_frame(args.output / "frames" / f"{label}.png", frame)
        report = {
            "suite": "libero_spatial",
            "base_task_id": 5,
            "case_id": "S04",
            "seed": SEED,
            "init_state_id": INIT_STATE_ID,
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
            "params": params,
            "swap_event": swap_event,
            "support_xy_errors_m": support_xy_errors,
            "support_own_z_errors_m": own_z_errors,
            "relative_position_errors_m": relative_position_errors,
            "relative_quaternion_errors": relative_quaternion_errors,
            "target_support_contacts": target_support_contacts,
            "support_ground_contacts": support_ground_contacts,
            "deep_contacts": deep_contacts,
            "unrelated_displacements_m": unrelated_displacements,
            "immediate_positions": {
                name: position.tolist() for name, position in immediate_positions.items()
            },
            "settled_positions": {
                name: position.tolist() for name, position in settled_positions.items()
            },
        }
    finally:
        active_adapter.close()

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
