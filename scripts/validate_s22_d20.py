"""Validate S22 and D20 in real LIBERO / MuJoCo environments."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_ROOT = ROOT / "simulator-source"
if str(SIMULATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_ROOT))

from libero.libero.envs import OffScreenRenderEnv  # noqa: E402
from libero.libero.envs.nonphysical_perturbations import (  # noqa: E402
    _model_named_id,
    _robot_contacts,
    _workspace_visual_geom_ids,
)


SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")


def _files(dataset_root: Path, suite: str, case_id: str) -> list[Path]:
    folder = "01_static" if case_id.startswith("S") else "02_dynamic"
    return sorted((dataset_root / suite / folder).glob(f"{case_id}__*.bddl"))


def _base_path(dataset_root: Path, suite: str, case_path: Path) -> Path:
    task_name = case_path.name.split("__", 1)[1]
    return dataset_root / suite / "00_base" / f"BASE__{task_name}"


def _make_env(path: Path, seed: int, image_size: int) -> tuple[Any, dict[str, Any]]:
    env = OffScreenRenderEnv(
        bddl_file_name=str(path),
        use_camera_obs=True,
        camera_names=["agentview", "robot0_eye_in_hand"],
        camera_heights=image_size,
        camera_widths=image_size,
        max_reset_attempts=50,
    )
    env.seed(seed)
    observation = env.reset()
    observation = env.begin_perturbation_rollout()
    return env, observation


def _agent_image(observation: dict[str, Any]) -> np.ndarray:
    image = np.asarray(observation["agentview_image"])
    if image.ndim != 3 or image.shape[-1] != 3:
        raise RuntimeError(f"Unexpected agentview image shape: {image.shape}")
    return image.copy()


def _object_positions(env: Any) -> dict[str, list[float]]:
    return {
        name: np.asarray(env.env.sim.data.body_xpos[int(body_id)], dtype=float).tolist()
        for name, body_id in env.env.obj_body_id.items()
        if not name.startswith("perturbation_")
    }


def _save_pair(path: Path, before: np.ndarray, after: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pair = np.concatenate([before, after], axis=1)
    cv2.imwrite(str(path), pair[::-1, :, ::-1])


def _validate_s22(
    path: Path,
    *,
    seed: int,
    image_size: int,
) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    env, observation = _make_env(path, seed, image_size)
    runtime = env.env.perturbation_runtime
    model = env.env.sim.model
    geom_ids = _workspace_visual_geom_ids(env.env)
    material_id = _model_named_id(model, "mat", "s22_table_texture")
    events = [
        event
        for event in runtime.events
        if event["event"] == "workspace_texture_replaced"
    ]
    if len(events) != 1:
        raise RuntimeError(f"S22 expected one texture event, got {events}")
    if not geom_ids or any(int(model.geom_matid[index]) != material_id for index in geom_ids):
        raise RuntimeError("S22 work-surface material was not applied")
    if env.env.workspace_name != "floor" and any(
        int(model.geom_contype[index]) != 0 for index in geom_ids
    ):
        raise RuntimeError("S22 selected a collision geom instead of a visual geom")
    return (
        {
            "path": str(path),
            "ok": True,
            "workspace": str(env.env.workspace_name),
            "visual_geom_ids": list(geom_ids),
            "material_id": material_id,
            "events": events,
        },
        env,
        {
            "image": _agent_image(observation),
            "objects": _object_positions(env),
        },
    )


def _compare_base(
    dataset_root: Path,
    suite: str,
    s22_path: Path,
    s22_snapshot: dict[str, Any],
    *,
    seed: int,
    image_size: int,
    output_dir: Path,
    workspace: str,
) -> dict[str, Any]:
    base_env = None
    try:
        base_env, observation = _make_env(
            _base_path(dataset_root, suite, s22_path), seed, image_size
        )
        base_image = _agent_image(observation)
        base_objects = _object_positions(base_env)
        common = sorted(set(base_objects) & set(s22_snapshot["objects"]))
        max_object_delta = max(
            (
                float(
                    np.linalg.norm(
                        np.asarray(base_objects[name])
                        - np.asarray(s22_snapshot["objects"][name])
                    )
                )
                for name in common
            ),
            default=0.0,
        )
        mean_pixel_delta = float(
            np.mean(
                np.abs(
                    base_image.astype(np.float32)
                    - s22_snapshot["image"].astype(np.float32)
                )
            )
        )
        if max_object_delta > 1e-5:
            raise RuntimeError(
                f"S22 changed object placement by {max_object_delta:.6f} m"
            )
        if mean_pixel_delta < 2.0:
            raise RuntimeError(
                f"S22 visual change is too weak: mean pixel delta {mean_pixel_delta:.3f}"
            )
        image_path = output_dir / f"s22_{workspace}_base_vs_texture.png"
        _save_pair(image_path, base_image, s22_snapshot["image"])
        return {
            "workspace": workspace,
            "base_path": str(_base_path(dataset_root, suite, s22_path)),
            "s22_path": str(s22_path),
            "mean_pixel_delta": mean_pixel_delta,
            "max_object_position_delta_m": max_object_delta,
            "image": str(image_path),
        }
    finally:
        if base_env is not None:
            base_env.close()


def _joint_limits_ok(env: Any) -> bool:
    model = env.env.sim.model
    data = env.env.sim.data
    indices = [int(index) for index in env.env.robots[0]._ref_joint_pos_indexes]
    qpos = np.asarray(data.qpos[indices], dtype=float)
    address_to_joint = {
        int(address): joint_id
        for joint_id, address in enumerate(np.asarray(model.jnt_qposadr, dtype=int))
    }
    for value, qpos_index in zip(qpos, indices):
        joint_id = address_to_joint.get(qpos_index)
        if joint_id is None or not bool(model.jnt_limited[joint_id]):
            continue
        low, high = model.jnt_range[joint_id]
        if not float(low) <= float(value) <= float(high):
            return False
    return bool(np.all(np.isfinite(qpos)))


def _validate_d20(
    path: Path,
    *,
    seed: int,
    image_size: int,
    max_motion_steps: int,
    save_image: Path | None,
) -> dict[str, Any]:
    env = None
    try:
        env, observation = _make_env(path, seed, image_size)
        before_image = _agent_image(observation)
        runtime = env.env.perturbation_runtime
        action = np.zeros(env.env.action_dim, dtype=np.float64)
        action[0] = 0.55
        action[-1] = -1.0
        event = None
        for _ in range(max_motion_steps):
            observation, _, _, _ = env.step(action)
            event = next(
                (
                    item
                    for item in runtime.events
                    if item["event"] == "robot_collision_displacement"
                ),
                None,
            )
            if event is not None:
                break
        if event is None:
            raise RuntimeError(
                f"D20 did not trigger after {max_motion_steps} commanded motion steps"
            )
        if float(event["eef_displacement_m"]) < 0.035:
            raise RuntimeError(f"D20 displacement is too small: {event}")
        if not _joint_limits_ok(env):
            raise RuntimeError("D20 left an arm joint outside its limit")
        penetrating = {
            str(pair): distance
            for pair, distance in _robot_contacts(env.env).items()
            if distance < -0.001
        }
        if penetrating:
            raise RuntimeError(f"D20 left penetrating robot contacts: {penetrating}")
        initial_event_count = sum(
            item["event"] == "robot_collision_displacement" for item in runtime.events
        )
        noop = np.zeros(env.env.action_dim, dtype=np.float64)
        noop[-1] = -1.0
        for _ in range(3):
            observation, _, _, _ = env.step(noop)
        final_event_count = sum(
            item["event"] == "robot_collision_displacement" for item in runtime.events
        )
        if initial_event_count != 1 or final_event_count != 1:
            raise RuntimeError("D20 triggered more than once")
        if save_image is not None:
            _save_pair(save_image, before_image, _agent_image(observation))
        return {
            "path": str(path),
            "ok": True,
            "workspace": str(env.env.workspace_name),
            "trigger_step": int(event["step"]),
            "eef_displacement_m": float(event["eef_displacement_m"]),
            "candidate_index": int(event["candidate_index"]),
            "penetrating_contacts": penetrating,
            "event_count": final_event_count,
            "image": str(save_image) if save_image is not None else None,
        }
    finally:
        if env is not None:
            env.close()


def _error(path: Path, exc: Exception) -> dict[str, Any]:
    return {
        "path": str(path),
        "ok": False,
        "error": repr(exc),
        "traceback": traceback.format_exc(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "outputs" / "s22_d20_validation"
    )
    parser.add_argument("--tasks-per-suite", type=int, default=0)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--image-size", type=int, default=128)
    parser.add_argument("--max-motion-steps", type=int, default=30)
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "dataset_root": str(dataset_root),
        "seed": args.seed,
        "s22": [],
        "s22_base_comparisons": [],
        "d20": [],
    }
    compared_workspaces: set[str] = set()
    saved_d20_suites: set[str] = set()

    for suite in SUITES:
        s22_files = _files(dataset_root, suite, "S22")
        d20_files = _files(dataset_root, suite, "D20")
        if args.tasks_per_suite > 0:
            s22_files = s22_files[: args.tasks_per_suite]
            d20_files = d20_files[: args.tasks_per_suite]
        for path in s22_files:
            env = None
            try:
                result, env, snapshot = _validate_s22(
                    path, seed=args.seed, image_size=args.image_size
                )
                report["s22"].append(result)
                workspace = result["workspace"]
                if workspace not in compared_workspaces:
                    report["s22_base_comparisons"].append(
                        _compare_base(
                            dataset_root,
                            suite,
                            path,
                            snapshot,
                            seed=args.seed,
                            image_size=args.image_size,
                            output_dir=output_dir,
                            workspace=workspace,
                        )
                    )
                    compared_workspaces.add(workspace)
                print(f"S22 OK {suite} {path.name}", flush=True)
            except Exception as exc:
                report["s22"].append(_error(path, exc))
                print(f"S22 FAIL {suite} {path.name}: {exc}", flush=True)
            finally:
                if env is not None:
                    env.close()

        for path in d20_files:
            image_path = None
            if suite not in saved_d20_suites:
                image_path = output_dir / f"d20_{suite}_before_vs_after.png"
            try:
                result = _validate_d20(
                    path,
                    seed=args.seed,
                    image_size=args.image_size,
                    max_motion_steps=args.max_motion_steps,
                    save_image=image_path,
                )
                report["d20"].append(result)
                saved_d20_suites.add(suite)
                print(f"D20 OK {suite} {path.name}", flush=True)
            except Exception as exc:
                report["d20"].append(_error(path, exc))
                print(f"D20 FAIL {suite} {path.name}: {exc}", flush=True)

    failures = [
        item
        for section in ("s22", "d20")
        for item in report[section]
        if not item["ok"]
    ]
    report["summary"] = {
        "s22_checked": len(report["s22"]),
        "s22_passed": sum(item["ok"] for item in report["s22"]),
        "d20_checked": len(report["d20"]),
        "d20_passed": sum(item["ok"] for item in report["d20"]),
        "workspace_comparisons": len(report["s22_base_comparisons"]),
        "failures": len(failures),
    }
    report_path = output_dir / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], ensure_ascii=False), flush=True)
    print(f"Report: {report_path}", flush=True)
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
