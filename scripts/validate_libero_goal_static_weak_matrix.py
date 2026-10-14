"""Validate every explicit static weak-effect fix against its BASE task.

The CSV feedback requested visually stronger perturbations, but image encoding
artifacts are deliberately out of scope.  This renderer loads each changed
``libero_goal`` BDDL in real MuJoCo, compares its initial frame to the matching
BASE scene, and rejects unstable or penetrating injected assets.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from libero.libero.envs import OffScreenRenderEnv
from libero.libero.envs.nonphysical_perturbations import (
    _entity_exists,
    _entity_has_penetrating_contact,
    _entity_pose,
)

from apply_libero_goal_weak_overrides import TASKS, WEAK_TASKS


ROOT = Path(__file__).resolve().parents[1]
BDDL_ROOT = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1" / "libero_goal"
OUT = ROOT / "outputs" / "libero_goal_targeted_20260820" / "static_weak_matrix"
STATIC_CASES = tuple(case_id for case_id in WEAK_TASKS if case_id.startswith("S"))


def _frame(env: Any) -> np.ndarray:
    env._update_observables(force=True)
    return np.asarray(env._get_observations()["agentview_image"]).copy()


def _save(frame: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), frame[::-1, :, ::-1])


def _asset_names(runtime: Any) -> list[str]:
    return sorted(
        {
            str(event["asset"])
            for event in runtime.events
            if event.get("asset")
        }
    )


def _settle(env: Any, names: list[str]) -> tuple[float, bool]:
    positions = {
        name: _entity_pose(env, name)[0]
        for name in names
        if _entity_exists(env, name)
    }
    for _ in range(80):
        env.sim.step()
    env.sim.forward()
    env._update_observables(force=True)
    displacement = max(
        (
            float(np.linalg.norm(_entity_pose(env, name)[0] - position))
            for name, position in positions.items()
        ),
        default=0.0,
    )
    return displacement, any(
        _entity_has_penetrating_contact(env, name)
        for name in names
        if _entity_exists(env, name)
    )


def _bddl(case_id: str, task_id: int) -> Path:
    return BDDL_ROOT / "01_static" / f"{case_id}__{TASKS[task_id]}.bddl"


def _base(task_id: int) -> Path:
    return BDDL_ROOT / "00_base" / f"BASE__{TASKS[task_id]}.bddl"


def _render(task_id: int, case_id: str) -> dict[str, Any]:
    case_dir = OUT / f"libero_goal_task{task_id}_{case_id}"
    base_env = None
    perturbation_env = None
    try:
        np.random.seed(142)
        base_env = OffScreenRenderEnv(
            bddl_file_name=str(_base(task_id)), camera_heights=256, camera_widths=256
        )
        base_env.reset()
        base_frame = _frame(base_env.env)
        _save(base_frame, case_dir / "base.png")

        np.random.seed(142)
        perturbation_env = OffScreenRenderEnv(
            bddl_file_name=str(_bddl(case_id, task_id)),
            camera_heights=256,
            camera_widths=256,
        )
        perturbation_env.reset()
        env = perturbation_env.env
        perturbation_frame = _frame(env)
        _save(perturbation_frame, case_dir / "perturbed.png")
        runtime = env.perturbation_runtime
        assets = _asset_names(runtime)
        safety_entities = list(assets)
        if case_id == "S08":
            safety_entities.extend(
                name
                for name in runtime.plan.targets
                if _entity_exists(env, name) and name not in safety_entities
            )
        displacement, penetration = _settle(env, safety_entities)
        settled_frame = _frame(env)
        _save(settled_frame, case_dir / "settled.png")
        frame_delta = float(
            np.mean(np.abs(perturbation_frame.astype(np.float64) - base_frame.astype(np.float64)))
        )
        changed_ratio = float(
            np.mean(np.max(np.abs(perturbation_frame.astype(np.int16) - base_frame.astype(np.int16)), axis=2) > 12)
        )
        status = "PASS" if runtime.events and not penetration and displacement <= 0.05 else "REVIEW"
        return {
            "base_task_id": task_id,
            "case_id": case_id,
            "event_count": len(runtime.events),
            "events": runtime.events,
            "assets": assets,
            "image_mean_abs_delta": round(frame_delta, 4),
            "image_changed_ratio": round(changed_ratio, 4),
            "settle_displacement_m": round(displacement, 6),
            "penetration": penetration,
            "status": status,
            "base_image": str(case_dir / "base.png"),
            "perturbed_image": str(case_dir / "perturbed.png"),
            "settled_image": str(case_dir / "settled.png"),
        }
    except Exception as exc:
        return {
            "base_task_id": task_id,
            "case_id": case_id,
            "status": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if base_env is not None:
            base_env.close()
        if perturbation_env is not None:
            perturbation_env.close()


def main() -> None:
    os.environ.pop("MUJOCO_GL", None)
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for case_id in STATIC_CASES:
        for task_id in WEAK_TASKS[case_id]:
            print(f"[static] libero_goal task{task_id} {case_id}", flush=True)
            results.append(_render(task_id, case_id))
    output = OUT / "render_results.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if any(result["status"] != "PASS" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
