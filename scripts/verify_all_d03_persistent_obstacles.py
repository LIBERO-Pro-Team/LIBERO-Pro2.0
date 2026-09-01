"""Render and audit all persistent movable D03 obstacles with seed 143."""

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
DEFAULT_OUTPUT = ROOT / "outputs" / "all_d03_persistent_obstacles_seed143_20260901"
SEED = 143
SUITES = ("libero_10", "libero_goal", "libero_object", "libero_spatial")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SIMULATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_ROOT))

os.environ.setdefault("LIBERO_PRO_ROOT", str(SIMULATOR_ROOT))
os.environ.setdefault("LIBERO_REMOTE_TASK_MANIFEST", str(MANIFEST))
os.environ.setdefault("MUJOCO_GL", "wgl")
if "LIBERO_CONFIG_PATH" not in os.environ:
    audit_config = DEFAULT_OUTPUT / "libero_config"
    audit_config.mkdir(parents=True, exist_ok=True)
    benchmark_root = SIMULATOR_ROOT / "libero" / "libero"
    (audit_config / "config.yaml").write_text(
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
    os.environ["LIBERO_CONFIG_PATH"] = str(audit_config)

from libero.libero.envs.nonphysical_perturbations import (  # noqa: E402
    _entity_body_ids,
    _entity_deep_contacts,
    _entity_has_support_contact,
    _entity_pose,
    _entity_vertical_offsets,
    _goal_articulation_targets,
    _goal_path_anchor_candidates,
    _set_entity_pose,
    _support_height_at,
    _workspace_bounds,
    _zero_entity_free_joint_velocity,
)
from libero_remote.environment.libero import LiberoEnvironmentAdapter  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--settle-steps", type=int, default=80)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--suite", action="append", choices=SUITES)
    parser.add_argument("--task-id", action="append", type=int)
    return parser.parse_args()


def _tasks(suites: set[str], task_ids: set[int]) -> list[dict[str, Any]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return sorted(
        (
            item
            for item in manifest["tasks"]
            if item["case_id"] == "D03"
            and str(item["suite"]) in suites
            and (not task_ids or int(item["base_task_id"]) in task_ids)
        ),
        key=lambda item: (SUITES.index(str(item["suite"])), int(item["base_task_id"])),
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


def _image_metrics(frame: np.ndarray) -> dict[str, Any]:
    values = np.asarray(frame, dtype=np.float64)
    return {
        "shape": list(frame.shape),
        "min": int(np.min(frame)),
        "max": int(np.max(frame)),
        "mean": round(float(np.mean(values)), 6),
        "std": round(float(np.std(values)), 6),
        "nonblank": bool(np.std(values) > 1.0 and np.max(frame) > np.min(frame)),
    }


def _collision_masks(env: Any, obstacle: str) -> list[dict[str, int]]:
    body_ids = set(_entity_body_ids(env, obstacle))
    model = env.sim.model
    return [
        {
            "geom_id": geom_id,
            "contype": int(model.geom_contype[geom_id]),
            "conaffinity": int(model.geom_conaffinity[geom_id]),
        }
        for geom_id in range(int(model.ngeom))
        if int(model.geom_bodyid[geom_id]) in body_ids
    ]


def _free_joint_types(env: Any, obstacle: str) -> list[int]:
    joints = list(getattr(env.objects_dict[obstacle], "joints", []) or [])
    return [
        int(env.sim.model.jnt_type[env.sim.model.joint_name2id(joint)])
        for joint in joints
    ]


def _finite_scene(env: Any) -> tuple[bool, dict[str, float]]:
    arrays = {
        "qpos": np.asarray(env.sim.data.qpos, dtype=np.float64),
        "qvel": np.asarray(env.sim.data.qvel, dtype=np.float64),
        "body_xpos": np.asarray(env.sim.data.body_xpos, dtype=np.float64),
    }
    finite = all(np.isfinite(values).all() for values in arrays.values())
    maxima = {
        name: float(np.max(np.abs(values))) if values.size else 0.0
        for name, values in arrays.items()
    }
    return finite, maxima


def _support_gap(env: Any, obstacle: str, params: dict[str, Any]) -> dict[str, Any]:
    position, _ = _entity_pose(env, obstacle)
    bottom_offset, _ = _entity_vertical_offsets(env, obstacle)
    support = _support_height_at(
        env,
        position[:2],
        params,
        ignored=(obstacle,),
    )
    if support is None:
        return {"support_geom": None, "bottom_gap_m": None}
    return {
        "support_geom": support[1],
        "bottom_gap_m": float(position[2] + bottom_offset - support[0]),
    }


def _force_trigger_condition(runtime: Any, env: Any) -> dict[str, Any]:
    eef_site_id = int(env.robots[0].eef_site_id)
    if runtime._interaction_mode() == "articulation":
        targets = _goal_articulation_targets(env)
        if not targets:
            raise RuntimeError("D03 articulation task has no goal fixture")
        target, _ = targets[0]
        receiver = runtime._articulation_anchor(env, target)
        env.sim.data.site_xpos[eef_site_id] = receiver
        return {
            "interaction_mode": "articulation",
            "goal_target": target,
            "receiver_position": receiver.tolist(),
            "transported_displacement_m": None,
        }

    candidates = _goal_path_anchor_candidates(env)
    if not candidates:
        raise RuntimeError("D03 placement task has no goal path anchor")
    target, position, anchor_name, receiver = candidates[0]
    _, quaternion = _entity_pose(env, target)
    transported = position + np.array([0.0, 0.0, 0.06], dtype=np.float64)
    _set_entity_pose(env, target, transported, quaternion)
    _zero_entity_free_joint_velocity(env, target)
    env.sim.data.site_xpos[eef_site_id] = receiver
    return {
        "interaction_mode": "placement",
        "goal_target": target,
        "receiver_anchor": anchor_name,
        "receiver_position": receiver.tolist(),
        "transported_displacement_m": float(np.linalg.norm(transported - position)),
    }


def _audit_task(
    item: dict[str, Any], *, output: Path, settle_steps: int, image_size: int
) -> dict[str, Any]:
    suite = str(item["suite"])
    task_id = int(item["base_task_id"])
    case_dir = output / suite / f"task{task_id:02d}"
    adapter = LiberoEnvironmentAdapter()
    try:
        first = adapter.create(
            {
                "suite": suite,
                "task_id": task_id,
                "variant": "D03",
                "_bddl_path": str(ROOT / "assets" / str(item["bddl_path"])),
                "init_state_id": 0,
                "seed": SEED,
                "camera_names": ["agentview"],
                "camera_height": image_size,
                "camera_width": image_size,
                "max_steps": settle_steps + 10,
                "control_mode": "relative",
            }
        )
        env = _unwrap_environment(adapter._env)
        runtime = env.perturbation_runtime
        obstacle = runtime._persistent_d03_obstacle_name()
        if obstacle is None:
            raise RuntimeError("D03 task did not resolve a persistent obstacle")
        staged_state = runtime._staged_persistent_obstacle
        if staged_state is None:
            raise RuntimeError("D03 obstacle was not staged before the rollout")
        original_masks = [
            {
                "geom_id": int(geom_id),
                "contype": int(contype),
                "conaffinity": int(conaffinity),
            }
            for geom_id, contype, conaffinity in staged_state[2]
        ]
        staged_position, _ = _entity_pose(env, obstacle)
        staged_masks = _collision_masks(env, obstacle)
        pre_frame = _frame(env)
        pre_path = case_dir / "pretrigger_seed143.png"
        _write_frame(pre_path, pre_frame)
        pre_finite, pre_maxima = _finite_scene(env)
        pre_deep = _entity_deep_contacts(env, obstacle)

        trigger = _force_trigger_condition(runtime, env)
        trigger["condition_met"] = bool(runtime._dynamic_triggered(env, 1))
        if not trigger["condition_met"]:
            raise RuntimeError("Scripted receiver approach did not satisfy D03 trigger")
        runtime._enter_persistent_obstacle(env, 1)

        entered_position, _ = _entity_pose(env, obstacle)
        entered_masks = _collision_masks(env, obstacle)
        entered_deep = _entity_deep_contacts(env, obstacle)
        entered_frame = _frame(env)
        entered_path = case_dir / "triggered_seed143.png"
        _write_frame(entered_path, entered_frame)

        for step in range(2, settle_steps + 2):
            runtime.before_simulation_step(env, step)
            env.sim.step()
        env.sim.forward()

        settled_position, _ = _entity_pose(env, obstacle)
        settled_masks = _collision_masks(env, obstacle)
        settled_deep = _entity_deep_contacts(env, obstacle)
        settled_frame = _frame(env)
        settled_path = case_dir / "settled_seed143.png"
        _write_frame(settled_path, settled_frame)
        settled_finite, settled_maxima = _finite_scene(env)
        support_gap = _support_gap(env, obstacle, runtime.plan.params)
        support_contact = bool(_entity_has_support_contact(env, obstacle))
        x_min, x_max, y_min, y_max = _workspace_bounds(env)
        in_workspace = bool(
            x_min <= settled_position[0] <= x_max
            and y_min <= settled_position[1] <= y_max
            and -0.5 <= settled_position[2] <= 2.5
        )
        events = list(runtime.diagnostics()["events"])
        entered_event_count = sum(
            event.get("event") == "persistent_dynamic_obstacle_entered"
            for event in events
        )
        restored_event_present = any(
            event.get("event") == "dynamic_asset_restored" for event in events
        )
        free_joint_types = _free_joint_types(env, obstacle)
        nonblank = all(
            _image_metrics(frame)["nonblank"]
            for frame in (pre_frame, entered_frame, settled_frame)
        )
        bottom_gap = support_gap["bottom_gap_m"]
        supported = bool(
            support_contact
            or (bottom_gap is not None and -0.004 <= bottom_gap <= 0.03)
        )
        passed = bool(
            0 in free_joint_types
            and staged_position[2] < -4.9
            and staged_masks
            and all(mask["contype"] == 0 for mask in staged_masks)
            and all(mask["conaffinity"] == 0 for mask in staged_masks)
            and not pre_deep
            and pre_finite
            and trigger["condition_met"]
            and entered_masks == original_masks
            and settled_masks == original_masks
            and not entered_deep
            and not settled_deep
            and settled_finite
            and settled_maxima["qvel"] < 50.0
            and settled_maxima["body_xpos"] < 10.0
            and in_workspace
            and supported
            and entered_event_count == 1
            and not restored_event_present
            and nonblank
        )
        return {
            "suite": suite,
            "task_id": task_id,
            "seed": SEED,
            "init_state_id": 0,
            "status": "PASS" if passed else "FAIL",
            "bddl": str(ROOT / "assets" / str(item["bddl_path"])),
            "obstacle": obstacle,
            "persistent_mode": (
                "movable_asset"
                if runtime.plan.params.get("persistent_movable_asset")
                else "existing_object"
            ),
            "free_joint_types": free_joint_types,
            "staged_position": staged_position.tolist(),
            "staged_collision_masks": staged_masks,
            "original_collision_masks": original_masks,
            "pretrigger_deep_contacts": pre_deep,
            "pretrigger_finite": pre_finite,
            "pretrigger_maxima": pre_maxima,
            "trigger": trigger,
            "entered_position": entered_position.tolist(),
            "entered_collision_masks": entered_masks,
            "entered_deep_contacts": entered_deep,
            "settled_steps": settle_steps,
            "settled_position": settled_position.tolist(),
            "settled_displacement_from_entry_m": float(
                np.linalg.norm(settled_position - entered_position)
            ),
            "settled_collision_masks": settled_masks,
            "settled_deep_contacts": settled_deep,
            "settled_finite": settled_finite,
            "settled_maxima": settled_maxima,
            "support_contact": support_contact,
            "support": support_gap,
            "supported": supported,
            "in_workspace": in_workspace,
            "entered_event_count": entered_event_count,
            "restored_event_present": restored_event_present,
            "events": events,
            "render_nonblank": nonblank,
            "images": {
                "pretrigger": str(pre_path),
                "triggered": str(entered_path),
                "settled": str(settled_path),
            },
        }
    except Exception as exc:
        return {
            "suite": suite,
            "task_id": task_id,
            "seed": SEED,
            "init_state_id": 0,
            "status": "ERROR",
            "bddl": str(ROOT / "assets" / str(item["bddl_path"])),
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        adapter.close()


def _contact_sheet(results: list[dict[str, Any]], suite: str, output: Path) -> Path:
    suite_results = [item for item in results if item["suite"] == suite]
    rows: list[np.ndarray] = []
    for result in suite_results:
        if "images" not in result:
            continue
        images = [
            cv2.imread(result["images"]["pretrigger"]),
            cv2.imread(result["images"]["settled"]),
        ]
        if any(image is None for image in images):
            continue
        header = np.zeros((30, images[0].shape[1] * 2, 3), dtype=np.uint8)
        label = f"task{result['task_id']}  pretrigger | settled  {result['status']}"
        cv2.putText(
            header,
            label,
            (8, 21),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        rows.append(np.vstack([header, np.hstack(images)]))
    if not rows:
        raise RuntimeError(f"No rendered rows for {suite}")
    sheet = np.vstack(rows)
    path = output / "contact_sheets" / f"{suite}_D03_seed143.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92]):
        raise RuntimeError(f"Failed to write contact sheet: {path}")
    return path


def main() -> None:
    args = _parse_args()
    if args.settle_steps < 1:
        raise SystemExit("--settle-steps must be positive")
    suites = set(args.suite or SUITES)
    task_ids = set(args.task_id or [])
    tasks = _tasks(suites, task_ids)
    results: list[dict[str, Any]] = []
    for index, item in enumerate(tasks, start=1):
        key = (item["suite"], item["base_task_id"], item["case_id"])
        print(f"[D03] {index}/{len(tasks)} {key}", flush=True)
        result = _audit_task(
            item,
            output=args.output,
            settle_steps=args.settle_steps,
            image_size=args.image_size,
        )
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)

    sheets = {}
    for suite in SUITES:
        if suite not in suites or not any(item["suite"] == suite for item in results):
            continue
        try:
            sheets[suite] = str(_contact_sheet(results, suite, args.output))
        except RuntimeError:
            continue
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    report = {
        "audit_type": "D03_seed143_synthetic_trigger_real_mujoco_safety_and_render",
        "seed": SEED,
        "init_state_id": 0,
        "settle_steps": args.settle_steps,
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
