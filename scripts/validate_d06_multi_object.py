"""Render and physically audit every task-level D06 target list."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import cv2
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "simulator-source") not in sys.path:
    sys.path.insert(0, str(ROOT / "simulator-source"))

from libero.libero.envs import OffScreenRenderEnv
from libero.libero.envs.nonphysical_perturbations import (
    _entity_body_ids,
    _entity_deep_contacts,
    _entity_pose,
    _goal_interaction_targets,
)


MANIFEST = ROOT / "assets" / "task_manifest.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "d06_multi_object_render_20260823"


def _save_frame(env: Any, path: Path) -> None:
    env._update_observables(force=True)
    frame = np.asarray(env._get_observations()["agentview_image"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame[::-1, :, ::-1]):
        raise RuntimeError(f"Failed to write frame {path}")


def _support_gap(env: Any, name: str) -> tuple[float, str | None]:
    """Measure the vertical gap from an entity's bottom to the first surface."""
    model, data = env.sim.model, env.sim.data
    body_ids = set(_entity_body_ids(env, name))
    root_id = int(env.obj_body_id[name])
    bottoms: list[float] = []
    for geom_id, body_id in enumerate(model.geom_bodyid):
        if int(body_id) not in body_ids:
            continue
        if hasattr(model, "geom_group") and int(model.geom_group[geom_id]) != 0:
            continue
        aabb = np.asarray(model.geom_aabb[geom_id], dtype=np.float64)
        rotation = np.asarray(data.geom_xmat[geom_id], dtype=np.float64).reshape(3, 3)
        center = np.asarray(data.geom_xpos[geom_id], dtype=np.float64) + rotation @ aabb[:3]
        extent = float(np.abs(rotation[2]) @ aabb[3:])
        bottoms.append(float(center[2] - extent))
    if not bottoms:
        return float("inf"), None
    origin = np.array(
        [data.body_xpos[root_id, 0], data.body_xpos[root_id, 1], min(bottoms) + 0.002],
        dtype=np.float64,
    )
    geom_id = np.array([-1], dtype=np.int32)
    distance = float(
        mujoco.mj_ray(
            model._model,
            data._data,
            origin,
            np.array([0.0, 0.0, -1.0]),
            np.ones(6, dtype=np.uint8),
            1,
            root_id,
            geom_id,
        )
    )
    if distance < 0.0:
        return float("inf"), None
    support = model.geom_id2name(int(geom_id[0])) if geom_id[0] >= 0 else None
    return max(0.0, distance - 0.002), support


def _min_xy_gap(env: Any, first: str, others: list[str]) -> float:
    first_xy = _entity_pose(env, first)[0][:2]
    gaps = [
        float(np.linalg.norm(first_xy - _entity_pose(env, other)[0][:2]))
        for other in others
        if other in env.obj_body_id
    ]
    return min(gaps, default=float("inf"))


def _task_rows() -> list[dict[str, Any]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return sorted(
        (row for row in payload["tasks"] if str(row["case_id"]).upper() == "D06"),
        key=lambda row: (str(row["suite"]), int(row["base_task_id"])),
    )


def _run(row: dict[str, Any], output: Path, seed: int, image_size: int, settle_steps: int) -> dict[str, Any]:
    suite = str(row["suite"])
    task_id = int(row["base_task_id"])
    bddl = ROOT / "assets" / str(row["bddl_path"])
    case_dir = output / f"{suite}_task{task_id}_D06"
    wrapper = None
    try:
        # Establish the scene's own settling behavior with the same seed. A
        # few LIBERO assets are not initially at their final resting height;
        # compare D06 against this control instead of calling that drift a
        # disturbance-induced failure.
        np.random.seed(seed)
        baseline_wrapper = OffScreenRenderEnv(
            bddl_file_name=str(bddl),
            camera_heights=image_size,
            camera_widths=image_size,
        )
        baseline_wrapper.reset()
        baseline_env = baseline_wrapper.env
        baseline_before = {
            name: _entity_pose(baseline_env, name)[0].copy()
            for name in baseline_env.objects_dict
            if name in baseline_env.obj_body_id
        }
        for _ in range(settle_steps):
            baseline_env.sim.step()
        baseline_env.sim.forward()
        baseline_settled = {
            name: _entity_pose(baseline_env, name)[0].copy()
            for name in baseline_before
        }
        baseline_wrapper.close()

        np.random.seed(seed)
        wrapper = OffScreenRenderEnv(
            bddl_file_name=str(bddl),
            camera_heights=image_size,
            camera_widths=image_size,
        )
        wrapper.reset()
        env = wrapper.env
        runtime = env.perturbation_runtime
        configured = list(runtime.plan.disturbance_targets or ())
        before = {
            name: _entity_pose(env, name)[0].copy()
            for name in env.objects_dict
            if name in env.obj_body_id
        }
        _save_frame(env, case_dir / "before.png")
        runtime._dynamic_triggered = lambda _env, _step: True
        runtime.before_simulation_step(env, 0)
        env.sim.forward()
        immediate = {
            name: _entity_pose(env, name)[0].copy()
            for name in before
        }
        _save_frame(env, case_dir / "immediate.png")
        for _ in range(settle_steps):
            env.sim.step()
        env.sim.forward()
        settled = {
            name: _entity_pose(env, name)[0].copy()
            for name in before
        }
        _save_frame(env, case_dir / "settled.png")

        target_rows = []
        failures: list[str] = []
        goal_targets = list(_goal_interaction_targets(env))
        for name in configured:
            immediate_distance = float(np.linalg.norm(immediate[name][:2] - before[name][:2]))
            settled_distance = float(np.linalg.norm(settled[name][:2] - before[name][:2]))
            deep_contacts = _entity_deep_contacts(env, name)
            support_gap, support_geom = _support_gap(env, name)
            goal_gap = _min_xy_gap(env, name, goal_targets)
            row_result = {
                "name": name,
                "immediate_displacement_m": round(immediate_distance, 6),
                "settled_displacement_m": round(settled_distance, 6),
                "deep_contacts": deep_contacts,
                "support_gap_m": round(support_gap, 6),
                "support_geom": support_geom,
                "goal_clearance_m": round(goal_gap, 6),
                "baseline_settled_xyz": baseline_settled[name].tolist(),
                "extra_settled_z_drift_m": round(
                    float(abs(settled[name][2] - baseline_settled[name][2])), 6
                ),
            }
            target_rows.append(row_result)
            if immediate_distance < 0.10 or settled_distance < 0.10:
                failures.append(f"{name}: displacement<0.10m")
            if deep_contacts:
                failures.append(f"{name}: deep_penetration")
            if row_result["extra_settled_z_drift_m"] > 0.05:
                failures.append(f"{name}: extra_settled_z_drift>0.05m")
            if goal_gap < 0.08:
                failures.append(f"{name}: goal_clearance<0.08m")
        collateral = {
            name: round(float(np.linalg.norm(settled[name][:2] - before[name][:2])), 6)
            for name in before
            if name not in configured
        }
        collateral_extra = {
            name: round(
                max(
                    0.0,
                    float(np.linalg.norm(settled[name][:2] - before[name][:2]))
                    - float(np.linalg.norm(baseline_settled[name][:2] - baseline_before[name][:2])),
                ),
                6,
            )
            for name in collateral
        }
        collateral_max = max(collateral_extra.values(), default=0.0)
        if collateral_max > 0.01:
            failures.append("unconfigured_extra_motion>0.01m")
        result = {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": "D06",
            "bddl": str(bddl),
            "configured_targets": configured,
            "events": list(runtime.events),
            "targets": target_rows,
            "collateral_displacements_m": collateral,
            "collateral_extra_displacements_m": collateral_extra,
            "collateral_max_displacement_m": collateral_max,
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
            "before_image": str(case_dir / "before.png"),
            "immediate_image": str(case_dir / "immediate.png"),
            "settled_image": str(case_dir / "settled.png"),
        }
    except Exception as exc:
        result = {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": "D06",
            "bddl": str(bddl),
            "status": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if wrapper is not None:
            wrapper.close()
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=142)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--settle-steps", type=int, default=120)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    os.environ.pop("MUJOCO_GL", None)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    rows = _task_rows()
    if len(rows) != 40:
        raise SystemExit(f"Expected 40 D06 rows, found {len(rows)}")
    if args.limit:
        rows = rows[: args.limit]
    results = []
    for row in rows:
        print(f"[d06] {row['suite']} task{row['base_task_id']}", flush=True)
        results.append(_run(row, output, args.seed, args.image_size, args.settle_steps))
    (output / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    counts = {status: sum(item["status"] == status for item in results) for status in ("PASS", "FAIL", "ERROR")}
    print(json.dumps({"counts": counts, "output": str(output)}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if counts["FAIL"] or counts["ERROR"] else 0)


if __name__ == "__main__":
    main()
