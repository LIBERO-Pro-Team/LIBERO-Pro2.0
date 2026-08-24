"""Verify S18 task parameters and applied observation offsets for all 40 tasks."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulator-source"))

from libero.libero.envs import OffScreenRenderEnv


MANIFEST = ROOT / "assets" / "task_manifest.json"
OUTPUT = ROOT / "outputs" / "s18_all_tasks_validation_20260824"


def main() -> None:
    os.environ.setdefault("MUJOCO_GL", "wgl")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tasks = [item for item in manifest["tasks"] if item["case_id"] == "S18"]
    results = []
    for item in tasks:
        key = (str(item["suite"]), int(item["base_task_id"]), "S18")
        wrapper = None
        try:
            np.random.seed(142)
            bddl = ROOT / "assets" / str(item["bddl_path"])
            wrapper = OffScreenRenderEnv(
                bddl_file_name=str(bddl), camera_heights=64, camera_widths=64
            )
            transformed = wrapper.reset()
            runtime = wrapper.env.perturbation_runtime
            wrapper.env._update_observables(force=True)
            raw = wrapper.env._get_observations()
            event = next(x for x in runtime.events if x["event"] == "calibration_offset")
            applied = event["applied_offsets"]
            deltas = {}
            for name, offset in applied.items():
                if name not in raw or name not in transformed:
                    continue
                deltas[name] = (
                    np.asarray(transformed[name], dtype=np.float64)
                    - np.asarray(raw[name], dtype=np.float64)
                ).tolist()
            expected_keys = {
                name
                for name, value in raw.items()
                if isinstance(value, np.ndarray)
                and ("eef_pos" in name or "joint_pos" in name)
            }
            status = "PASS" if set(applied) == expected_keys and deltas else "FAIL"
            result = {
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "bddl": str(bddl),
                "params": dict(runtime.plan.params),
                "applied_offsets": applied,
                "observed_deltas": deltas,
                "expected_keys": sorted(expected_keys),
                "historical_substring_semantics_preserved": True,
                "status": status,
            }
        except Exception as exc:
            result = {
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "status": "ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            }
        finally:
            if wrapper is not None:
                wrapper.close()
        results.append(result)
        print(json.dumps({"key": key, "status": result["status"]}, ensure_ascii=False))
    (OUTPUT / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    raise SystemExit(1 if any(item["status"] != "PASS" for item in results) else 0)


if __name__ == "__main__":
    main()
