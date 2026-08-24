"""Render the three editable D09 feedback tasks and record exact light evidence."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "simulator-source") not in sys.path:
    sys.path.insert(0, str(ROOT / "simulator-source"))

from libero.libero.envs import OffScreenRenderEnv


MANIFEST = ROOT / "assets" / "task_manifest.json"
OUTPUT = ROOT / "outputs" / "d09_feedback_validation_20260824"
TARGETS = {("libero_goal", 0), ("libero_goal", 1), ("libero_goal", 2)}


def _write_frame(frame: np.ndarray, path: Path, cv2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), np.asarray(frame)[::-1, :, ::-1]):
        raise RuntimeError(f"Could not write {path}")


def _image_metrics(before: np.ndarray, during: np.ndarray, restored: np.ndarray) -> dict[str, float]:
    before_f = np.asarray(before, dtype=np.float64)
    during_f = np.asarray(during, dtype=np.float64)
    restored_f = np.asarray(restored, dtype=np.float64)
    delta = np.max(np.abs(before_f - during_f), axis=2)
    return {
        "before_mean": round(float(np.mean(before_f)), 6),
        "during_mean": round(float(np.mean(during_f)), 6),
        "restored_mean": round(float(np.mean(restored_f)), 6),
        "during_mean_abs_delta": round(float(np.mean(np.abs(before_f - during_f))), 6),
        "restored_mean_abs_delta": round(float(np.mean(np.abs(before_f - restored_f))), 6),
        "during_changed_ratio": round(float(np.mean(delta > 12.0)), 6),
    }


def _array_payload(value: np.ndarray) -> list[list[float]]:
    return np.asarray(value, dtype=np.float64).tolist()


def _array_max_delta(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.max(np.abs(np.asarray(first) - np.asarray(second))))


def _run(suite: str, task_id: int, bddl: Path, cv2) -> dict[str, object]:
    output_dir = OUTPUT / f"{suite}_task{task_id}_D09"
    env = None
    try:
        np.random.seed(142)
        env = OffScreenRenderEnv(
            bddl_file_name=str(bddl), camera_heights=256, camera_widths=256
        )
        observation = env.reset()
        runtime = env.env.perturbation_runtime
        sim = env.env.sim
        baseline_diffuse = np.asarray(sim.model.light_diffuse).copy()
        baseline_ambient = np.asarray(sim.model.light_ambient).copy()
        baseline_poses = {
            name: np.asarray(env.env.objects_dict[name].get_obj_pos()).copy()
            for name in sorted(env.env.objects_dict)
            if hasattr(env.env.objects_dict[name], "get_obj_pos")
        }
        before = np.asarray(observation["agentview_image"]).copy()

        runtime._dynamic_triggered = lambda _env, _step: True
        runtime.before_simulation_step(env.env, 0)
        raw_during = env.env._get_observations()
        during = runtime.transform_observation(raw_during, 0)["agentview_image"]
        applied_diffuse = np.asarray(sim.model.light_diffuse).copy()
        applied_ambient = np.asarray(sim.model.light_ambient).copy()

        duration = runtime.event_duration_steps
        runtime.before_simulation_step(env.env, duration)
        restored = np.asarray(env.env._get_observations()["agentview_image"]).copy()
        restored_diffuse = np.asarray(sim.model.light_diffuse).copy()
        restored_ambient = np.asarray(sim.model.light_ambient).copy()
        restored_poses = {
            name: np.asarray(env.env.objects_dict[name].get_obj_pos()).copy()
            for name in baseline_poses
        }

        events = list(runtime.events)
        dynamic_event = next(item for item in events if item["event"] == "dynamic_lighting_change")
        exposure_event = next(item for item in events if item["event"] == "exposure_change")
        restore_event = next(item for item in events if item["event"] == "dynamic_lighting_restored")
        _write_frame(before, output_dir / "before.png", cv2)
        _write_frame(during, output_dir / "during.png", cv2)
        _write_frame(restored, output_dir / "restored.png", cv2)

        pose_delta = max(
            (_array_max_delta(baseline_poses[name], restored_poses[name]) for name in baseline_poses),
            default=0.0,
        )
        result = {
            "suite": suite,
            "task_id": task_id,
            "case_id": "D09",
            "bddl": str(bddl),
            "event_duration_steps": duration,
            "events": events,
            "lighting": {
                "requested_factor": dynamic_event["requested_value"]["lighting_factor"],
                "baseline_diffuse": _array_payload(baseline_diffuse),
                "baseline_ambient": _array_payload(baseline_ambient),
                "applied_diffuse": _array_payload(applied_diffuse),
                "applied_ambient": _array_payload(applied_ambient),
                "restored_diffuse": _array_payload(restored_diffuse),
                "restored_ambient": _array_payload(restored_ambient),
                "applied_diffuse_max_error": _array_max_delta(
                    applied_diffuse, baseline_diffuse * dynamic_event["requested_value"]["lighting_factor"]
                ),
                "applied_ambient_max_error": _array_max_delta(
                    applied_ambient, baseline_ambient * dynamic_event["requested_value"]["lighting_factor"]
                ),
                "restore_diffuse_max_error": _array_max_delta(restored_diffuse, baseline_diffuse),
                "restore_ambient_max_error": _array_max_delta(restored_ambient, baseline_ambient),
            },
            "exposure": exposure_event["applied_value"],
            "image_metrics": _image_metrics(before, during, restored),
            "object_pose_restore_max_error_m": pose_delta,
            "status": "PASS"
            if duration == 50
            and dynamic_event["requested_value"]["lighting_factor"] == 0.38
            and _array_max_delta(applied_diffuse, baseline_diffuse * 0.38) < 1e-12
            and _array_max_delta(applied_ambient, baseline_ambient * 0.38) < 1e-12
            and _array_max_delta(restored_diffuse, baseline_diffuse) < 1e-12
            and _array_max_delta(restored_ambient, baseline_ambient) < 1e-12
            and pose_delta < 1e-9
            and _image_metrics(before, during, restored)["during_changed_ratio"] > 0.90
            else "FAIL",
        }
        (output_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
    finally:
        if env is not None:
            env.close()


def main() -> None:
    os.environ.setdefault("MUJOCO_GL", "wgl")
    import cv2

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results = []
    for item in manifest["tasks"]:
        key = (str(item["suite"]), int(item["base_task_id"]))
        if key not in TARGETS or str(item["case_id"]).upper() != "D09":
            continue
        result = _run(key[0], key[1], ROOT / "assets" / item["bddl_path"], cv2)
        results.append(result)
        print(json.dumps({"key": key, "status": result["status"], "image_metrics": result["image_metrics"]}, ensure_ascii=False), flush=True)
    report = OUTPUT / "results.json"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(1 if any(item["status"] != "PASS" for item in results) else 0)


if __name__ == "__main__":
    main()
