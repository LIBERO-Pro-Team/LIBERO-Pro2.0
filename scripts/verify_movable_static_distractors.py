"""Audit all movable S10/S11 object distractors with seed 143 and init0."""

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
DEFAULT_OUTPUT = ROOT / "outputs" / "movable_static_distractors_seed143_20260901"
SEED = 143
CASES = ("S10", "S11")
SUITES = ("libero_10", "libero_goal", "libero_object", "libero_spatial")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SIMULATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_ROOT))

os.environ.setdefault("LIBERO_PRO_ROOT", str(SIMULATOR_ROOT))
os.environ.setdefault("LIBERO_REMOTE_TASK_MANIFEST", str(MANIFEST))
os.environ.setdefault("MUJOCO_GL", "wgl")
if "LIBERO_CONFIG_PATH" not in os.environ:
    config_dir = DEFAULT_OUTPUT / "libero_config"
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

from libero.libero.envs.nonphysical_perturbations import (  # noqa: E402
    _entity_body_ids,
    _entity_deep_contacts,
    _entity_has_support_contact,
    _entity_pose,
    _entity_vertical_offsets,
    _support_height_at,
    _workspace_bounds,
)
from libero_remote.environment.libero import LiberoEnvironmentAdapter  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--motion-steps", type=int, default=300)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--save-video", action="store_true")
    parser.add_argument("--probe-mobility", action="store_true")
    parser.add_argument("--suite", action="append", choices=SUITES)
    parser.add_argument("--case-id", action="append", choices=CASES)
    parser.add_argument("--task-id", action="append", type=int)
    return parser.parse_args()


def _tasks(
    suites: set[str], case_ids: set[str], task_ids: set[int]
) -> list[dict[str, Any]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return sorted(
        (
            item
            for item in manifest["tasks"]
            if str(item["suite"]) in suites
            and str(item["case_id"]) in case_ids
            and (not task_ids or int(item["base_task_id"]) in task_ids)
        ),
        key=lambda item: (
            SUITES.index(str(item["suite"])),
            CASES.index(str(item["case_id"])),
            int(item["base_task_id"]),
        ),
    )


def _unwrap_environment(wrapper: Any) -> Any:
    current = wrapper
    for _ in range(5):
        if hasattr(current, "obj_body_id") and hasattr(current, "sim"):
            return current
        current = getattr(current, "env", None)
        if current is None:
            break
    raise RuntimeError("Cannot resolve the underlying LIBERO environment")


def _frame(env: Any) -> np.ndarray:
    env._update_observables(force=True)
    frame = env._get_observations().get("agentview_image")
    if not isinstance(frame, np.ndarray) or frame.ndim != 3:
        raise RuntimeError("agentview_image is missing")
    return frame.copy()


def _write_frame(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), np.asarray(frame)[::-1, :, ::-1]):
        raise RuntimeError(f"Failed to write image: {path}")


def _nonblank(frame: np.ndarray) -> bool:
    values = np.asarray(frame, dtype=np.float64)
    return bool(np.std(values) > 1.0 and np.max(values) > np.min(values))


def _compiled_joint_types(env: Any, entity: str) -> list[int]:
    result = []
    scene_object = env.objects_dict[entity]
    for joint in list(getattr(scene_object, "joints", []) or []):
        try:
            joint_id = int(env.sim.model.joint_name2id(joint))
        except Exception:
            continue
        result.append(int(env.sim.model.jnt_type[joint_id]))
    return result


def _free_joint_entities(env: Any) -> tuple[str, ...]:
    return tuple(
        name
        for name in sorted(getattr(env, "objects_dict", {}))
        if 0 in _compiled_joint_types(env, name)
    )


def _collision_masks(env: Any, entity: str) -> list[dict[str, int]]:
    body_ids = set(_entity_body_ids(env, entity))
    model = env.sim.model
    return [
        {
            "geom_id": geom_id,
            "contype": int(model.geom_contype[geom_id]),
            "conaffinity": int(model.geom_conaffinity[geom_id]),
        }
        for geom_id in range(int(model.ngeom))
        if int(model.geom_bodyid[geom_id]) in body_ids
        and int(model.geom_group[geom_id]) == 0
    ]


def _entity_mass(env: Any, entity: str) -> float:
    body_ids = set(_entity_body_ids(env, entity))
    return float(sum(float(env.sim.model.body_mass[body_id]) for body_id in body_ids))


def _finite_scene(env: Any) -> bool:
    return all(
        np.isfinite(np.asarray(values, dtype=np.float64)).all()
        for values in (env.sim.data.qpos, env.sim.data.qvel, env.sim.data.body_xpos)
    )


def _free_velocity(env: Any, entity: str) -> np.ndarray:
    for joint in env.objects_dict[entity].joints:
        joint_id = int(env.sim.model.joint_name2id(joint))
        if int(env.sim.model.jnt_type[joint_id]) == 0:
            dof = int(env.sim.model.jnt_dofadr[joint_id])
            return np.asarray(env.sim.data.qvel[dof : dof + 6]).copy()
    return np.zeros(6)


def _support(env: Any, entity: str, params: dict[str, Any]) -> dict[str, Any]:
    position, _ = _entity_pose(env, entity)
    bottom_offset, _ = _entity_vertical_offsets(env, entity)
    support = _support_height_at(env, position[:2], params, ignored=(entity,))
    bottom_gap = None if support is None else float(position[2] + bottom_offset - support[0])
    contact = bool(_entity_has_support_contact(env, entity))
    return {
        "support_geom": None if support is None else support[1],
        "bottom_gap_m": bottom_gap,
        "support_contact": contact,
        "supported": bool(
            contact or (bottom_gap is not None and -0.004 <= bottom_gap <= 0.03)
        ),
    }


def _audit_task(
    item: dict[str, Any], *, output: Path, motion_steps: int, image_size: int,
    save_video: bool = False,
    probe_mobility: bool = False,
) -> dict[str, Any]:
    suite = str(item["suite"])
    task_id = int(item["base_task_id"])
    case_id = str(item["case_id"])
    adapter = LiberoEnvironmentAdapter()
    video = None
    try:
        adapter.create(
            {
                "suite": suite,
                "task_id": task_id,
                "variant": case_id,
                "_bddl_path": str(ROOT / "assets" / str(item["bddl_path"])),
                "init_state_id": 0,
                "seed": SEED,
                "camera_names": ["agentview"],
                "camera_height": image_size,
                "camera_width": image_size,
                "max_steps": motion_steps + 20,
                "control_mode": "relative",
            }
        )
        env = _unwrap_environment(adapter._env)
        runtime = env.perturbation_runtime
        injection = env.perturbation_asset_injection
        assets = tuple(getattr(injection, "injected_names", ()) or ())
        if not assets:
            raise RuntimeError(f"{case_id} has no injected distractor assets")

        initial_frame = _frame(env)
        initial_path = output / "frames" / f"{suite}_task{task_id}_{case_id}_initial.png"
        _write_frame(initial_path, initial_frame)
        tracked = _free_joint_entities(env)
        entry_positions = {name: _entity_pose(env, name)[0] for name in tracked}
        initial_velocities = {name: _free_velocity(env, name).tolist() for name in assets}
        video_path = output / "videos" / f"{suite}_task{task_id}_{case_id}_seed143_init0.mp4"
        video_stride = max(1, round(1.0 / (20 * env.sim.model.opt.timestep)))
        if save_video:
            video_path.parent.mkdir(parents=True, exist_ok=True)
            video = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 20,
                                    (image_size, image_size))
            if not video.isOpened():
                raise RuntimeError(f"Failed to open video: {video_path}")
            video.write(initial_frame[::-1, :, ::-1])
        motion = {
            name: {
                "minimum_z_m": float(position[2]),
                "maximum_z_m": float(position[2]),
                "maximum_displacement_m": 0.0,
                "maximum_abs_vz_mps": 0.0,
            }
            for name, position in entry_positions.items()
        }
        finite_throughout = _finite_scene(env)
        asset_deep_contacts: dict[str, list[dict[str, Any]]] = {}
        tail_positions = {name: [] for name in assets}
        hold_action = np.array([0., 0., 0., 0., 0., 0., -1.])
        control_stride = max(1, round(env.control_timestep / env.model_timestep))
        for step in range(motion_steps):
            env.sim.forward()
            env._pre_action(hold_action, policy_step=(step % control_stride == 0))
            env.sim.step()
            if video is not None and (step + 1) % video_stride == 0:
                video.write(_frame(env)[::-1, :, ::-1])
            if step >= motion_steps * 3 // 4:
                for name in assets:
                    tail_positions[name].append(_entity_pose(env, name)[0])
            finite_throughout = finite_throughout and _finite_scene(env)
            for name, initial in entry_positions.items():
                position, _ = _entity_pose(env, name)
                values = motion[name]
                values["minimum_z_m"] = min(values["minimum_z_m"], float(position[2]))
                values["maximum_z_m"] = max(values["maximum_z_m"], float(position[2]))
                values["maximum_displacement_m"] = max(
                    values["maximum_displacement_m"],
                    float(np.linalg.norm(position - initial)),
                )
                scene_object = env.objects_dict[name]
                for joint in list(getattr(scene_object, "joints", []) or []):
                    try:
                        joint_id = int(env.sim.model.joint_name2id(joint))
                    except Exception:
                        continue
                    if int(env.sim.model.jnt_type[joint_id]) == 0:
                        dof = int(env.sim.model.jnt_dofadr[joint_id])
                        values["maximum_abs_vz_mps"] = max(
                            values["maximum_abs_vz_mps"],
                            abs(float(env.sim.data.qvel[dof + 2])),
                        )
                        break
            for asset in assets:
                contacts = _entity_deep_contacts(env, asset, tolerance=0.002)
                if contacts:
                    asset_deep_contacts[asset] = contacts
        env.sim.forward()

        final_frame = _frame(env)
        final_path = output / "frames" / f"{suite}_task{task_id}_{case_id}_settled.png"
        _write_frame(final_path, final_frame)
        x_min, x_max, y_min, y_max = _workspace_bounds(env)
        asset_results = {}
        for asset in assets:
            position, _ = _entity_pose(env, asset)
            masks = _collision_masks(env, asset)
            support = _support(env, asset, runtime.plan.params)
            joint_types = _compiled_joint_types(env, asset)
            asset_results[asset] = {
                "position": position.tolist(),
                "free_joint_types": joint_types,
                "mass_kg": _entity_mass(env, asset),
                "collision_masks": masks,
                "collision_enabled": bool(
                    masks
                    and all(mask["contype"] > 0 and mask["conaffinity"] > 0 for mask in masks)
                ),
                "support": support,
                "in_workspace": bool(
                    x_min <= position[0] <= x_max
                    and y_min <= position[1] <= y_max
                    and -0.5 <= position[2] <= 2.5
                ),
                "deep_contacts": asset_deep_contacts.get(asset, []),
                "initial_velocity": initial_velocities[asset],
                "final_velocity": _free_velocity(env, asset).tolist(),
                "tail_position_span_m": float(np.linalg.norm(
                    np.ptp(np.asarray(tail_positions[asset]), axis=0)
                )),
            }

        jumpers = {
            name: values["maximum_z_m"] - entry_positions[name][2]
            for name, values in motion.items()
            if values["maximum_z_m"] - entry_positions[name][2] > 0.02
        }
        drifters = {
            name: values["maximum_displacement_m"]
            for name, values in motion.items()
            if values["maximum_displacement_m"] > 0.05
        }
        multi_entity_motion = sum(
            values["maximum_displacement_m"] > 0.02 for values in motion.values()
        ) > 1
        failures = []
        if not finite_throughout:
            failures.append("nonfinite_scene")
        if bool(env._check_success()):
            failures.append("task_successful_at_reset")
        if jumpers:
            failures.append("object_jump")
        if drifters:
            failures.append("object_drift")
        if multi_entity_motion:
            failures.append("coordinated_scene_motion")
        if not _nonblank(initial_frame) or not _nonblank(final_frame):
            failures.append("blank_render")
        for asset, values in asset_results.items():
            if 0 not in values["free_joint_types"]:
                failures.append(f"{asset}:missing_free_joint")
            if values["mass_kg"] <= 0.0:
                failures.append(f"{asset}:nonpositive_mass")
            if not values["collision_enabled"]:
                failures.append(f"{asset}:collision_disabled")
            if not values["support"]["supported"]:
                failures.append(f"{asset}:unsupported")
            if not values["in_workspace"]:
                failures.append(f"{asset}:outside_workspace")
            if values["deep_contacts"]:
                failures.append(f"{asset}:deep_penetration")
            if runtime.plan.params.get("zero_initial_asset_velocity"):
                if np.any(np.asarray(values["initial_velocity"]) != 0):
                    failures.append(f"{asset}:nonzero_initial_velocity")
                if values["tail_position_span_m"] > 0.001:
                    failures.append(f"{asset}:persistent_jitter")

        events = [
            event
            for event in runtime.diagnostics()["events"]
            if str(event.get("event", "")).startswith("static_asset_placed")
        ]
        if len(events) != len(assets):
            failures.append("static_asset_event_count")
        mobility = {}
        if probe_mobility:
            state = env.sim.get_state()
            forces = env.sim.data.xfrc_applied.copy()
            try:
                for asset in assets:
                    env.sim.set_state(state)
                    env.sim.forward()
                    initial, _ = _entity_pose(env, asset)
                    body = env.obj_body_id[asset]
                    env.sim.data.xfrc_applied[:] = forces
                    force_n = 2.0 * _entity_mass(env, asset) * abs(env.sim.model.opt.gravity[2])
                    env.sim.data.xfrc_applied[body, 2] = force_n
                    for step in range(50):
                        env.sim.forward()
                        env._pre_action(hold_action, policy_step=(step % control_stride == 0))
                        env.sim.step()
                    env.sim.forward()
                    final, _ = _entity_pose(env, asset)
                    rise = float(final[2] - initial[2])
                    mobility[asset] = {"upward_force_n": force_n, "rise_m": rise}
                    if rise <= 0.01:
                        failures.append(f"{asset}:not_movable_under_force")
            finally:
                env.sim.data.xfrc_applied[:] = forces
                env.sim.set_state(state)
                env.sim.forward()
        return {
            "suite": suite,
            "task_id": task_id,
            "case_id": case_id,
            "seed": SEED,
            "init_state_id": 0,
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
            "assets": asset_results,
            "asset_count": len(assets),
            "tracked_free_joint_entities": len(tracked),
            "finite_throughout": finite_throughout,
            "jumpers": jumpers,
            "drifters": drifters,
            "multi_entity_motion": multi_entity_motion,
            "motion": motion,
            "events": events,
            "images": {"initial": str(initial_path), "settled": str(final_path)},
            "video": str(video_path) if save_video else None,
            "mobility_probe": mobility,
        }
    except Exception as exc:
        return {
            "suite": suite,
            "task_id": task_id,
            "case_id": case_id,
            "seed": SEED,
            "init_state_id": 0,
            "status": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if video is not None:
            video.release()
        adapter.close()


def _contact_sheet(
    results: list[dict[str, Any]], suite: str, case_id: str, output: Path
) -> Path:
    rows = []
    for result in results:
        if result["suite"] != suite or result["case_id"] != case_id or "images" not in result:
            continue
        images = [
            cv2.imread(result["images"]["initial"]),
            cv2.imread(result["images"]["settled"]),
        ]
        if any(image is None for image in images):
            continue
        header = np.zeros((30, images[0].shape[1] * 2, 3), dtype=np.uint8)
        cv2.putText(
            header,
            f"task{result['task_id']} initial | settled {result['status']}",
            (8, 21),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        rows.append(np.vstack([header, np.hstack(images)]))
    if not rows:
        raise RuntimeError(f"No rendered rows for {suite}/{case_id}")
    path = output / "contact_sheets" / f"{suite}_{case_id}_seed143.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 92]):
        raise RuntimeError(f"Failed to write contact sheet: {path}")
    return path


def main() -> None:
    args = _parse_args()
    if args.motion_steps < 1:
        raise SystemExit("--motion-steps must be positive")
    suites = set(args.suite or SUITES)
    case_ids = {str(case_id).upper() for case_id in (args.case_id or CASES)}
    task_ids = set(args.task_id or [])
    tasks = _tasks(suites, case_ids, task_ids)
    results = []
    for index, item in enumerate(tasks, start=1):
        key = (item["suite"], item["base_task_id"], item["case_id"])
        print(f"[static-object] {index}/{len(tasks)} {key}", flush=True)
        result = _audit_task(
            item,
            output=args.output,
            motion_steps=args.motion_steps,
            image_size=args.image_size,
            save_video=args.save_video,
            probe_mobility=args.probe_mobility,
        )
        results.append(result)
        if result["status"] != "PASS":
            print(json.dumps(result, ensure_ascii=False), flush=True)

    sheets = {}
    for suite in SUITES:
        for case_id in CASES:
            if suite not in suites or case_id not in case_ids:
                continue
            try:
                sheets[f"{suite}/{case_id}"] = str(
                    _contact_sheet(results, suite, case_id, args.output)
                )
            except RuntimeError:
                continue
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    report = {
        "audit_type": "S10_S11_seed143_init0_movable_physics_scene_motion_and_render",
        "seed": SEED,
        "init_state_id": 0,
        "motion_steps": args.motion_steps,
        "thresholds": {"jump_height_m": 0.02, "drift_limit_m": 0.05},
        "task_count": len(results),
        "status_counts": dict(sorted(counts.items())),
        "contact_sheets": sheets,
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / "report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["status_counts"], ensure_ascii=False), flush=True)
    print(f"Report: {report_path.resolve()}", flush=True)
    raise SystemExit(0 if counts == {"PASS": len(results)} else 1)


if __name__ == "__main__":
    main()
