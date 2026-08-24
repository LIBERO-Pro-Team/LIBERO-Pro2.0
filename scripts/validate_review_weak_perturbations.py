"""Low-cost validation for one reviewed task per weak perturbation category."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from libero.libero.envs import OffScreenRenderEnv
from libero.libero.envs.nonphysical_perturbations import (
    _entity_body_ids,
    _entity_exists,
    _entity_has_penetrating_contact,
    _entity_pose,
    _goal_path_anchors,
    _set_entity_pose,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"
WEAK = ROOT / ".codex-workbook-audit-20260819" / "weak_rows.json"
OUT = ROOT / "outputs" / "review_feedback_current_20260820" / "weak_matrix"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Validate only the named representative case; repeat as needed.",
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def _tasks() -> dict[tuple[str, int, str], dict[str, Any]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        (str(item["suite"]), int(item["base_task_id"]), str(item["case_id"])): item
        for item in payload["tasks"]
    }


def _collision(env: Any, first: str, second: str) -> bool:
    if not (_entity_exists(env, first) and _entity_exists(env, second)):
        return False
    first_ids = set(_entity_body_ids(env, first))
    second_ids = set(_entity_body_ids(env, second))
    model, data = env.sim.model, env.sim.data
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        body_a = int(model.geom_bodyid[int(contact.geom1)])
        body_b = int(model.geom_bodyid[int(contact.geom2)])
        if ((body_a in first_ids and body_b in second_ids) or
                (body_a in second_ids and body_b in first_ids)) and float(contact.dist) < -1e-5:
            return True
    return False


def _frame(env: Any) -> np.ndarray:
    env._update_observables(force=True)
    return np.asarray(env._get_observations()["agentview_image"]).copy()


def _representatives() -> list[tuple[str, int, str]]:
    rows = json.loads(WEAK.read_text(encoding="utf-8"))
    selected: dict[str, tuple[str, int, str]] = {}
    for row in rows:
        case = str(row["扰动"])
        selected.setdefault(
            case,
            (str(row["套件"]), int(str(row["任务ID"]).removeprefix("task")), case),
        )
    return [selected[case] for case in sorted(selected)]


def _record(spec: tuple[str, int, str], task: dict[str, Any]) -> dict[str, Any]:
    suite, task_id, case_id = spec
    bddl = ROOT / "assets" / task["bddl_path"]
    case_dir = OUT / f"{suite}_task{task_id}_{case_id}"
    case_dir.mkdir(parents=True, exist_ok=True)
    env = None
    try:
        np.random.seed(142)
        env = OffScreenRenderEnv(
            bddl_file_name=str(bddl), camera_heights=256, camera_widths=256
        )
        env.reset()
        sim_env = env.env
        runtime = sim_env.perturbation_runtime
        before = _frame(sim_env)
        # Force the actual runtime operator once, while leaving the scene and
        # collision/safety implementation unchanged. This avoids model timing
        # and gives a deterministic smoke test for every weak case.
        if case_id == "D15":
            chunk_size, _ = runtime._d15_chunk_config()
            for index in range(chunk_size):
                runtime.action_queue.append(
                    np.array([0.01 * index, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
                )
        if case_id != "D05":
            runtime._dynamic_triggered = lambda _env, _step: True
        runtime.previous_action = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
        if case_id == "D05":
            eef = np.asarray(
                sim_env.sim.data.site_xpos[sim_env.robots[0].eef_site_id],
                dtype=np.float64,
            )
            target_name, _, _, _ = _goal_path_anchors(sim_env)
            _, quaternion = _entity_pose(sim_env, target_name)
            _set_entity_pose(
                sim_env,
                target_name,
                eef + np.array([0.0, 0.0, 0.02]),
                quaternion,
            )
            sim_env.sim.forward()
        runtime.before_simulation_step(sim_env, 0)
        observation = sim_env._get_observations()
        iterations = 1
        if case_id in {"D12", "S20"}:
            iterations = max(
                int(runtime.plan.params.get("observation_delay_steps", 1)),
                int(runtime.plan.params.get("action_delay_steps", 1)),
                int(runtime.plan.params.get("gripper_delay_steps", 1)),
            ) + 1
        for index in range(iterations):
            observation = runtime.transform_observation(observation, index)
            runtime.transform_action(
                np.array([0.01 * index, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]), index
            )
            runtime.transform_gripper_force_command(float(index % 2), index)
        after = _frame(sim_env)
        cv2.imwrite(str(case_dir / "entered.png"), after[::-1, :, ::-1])
        initial_diagnostics = runtime.diagnostics()
        active_assets = [
            event.get("asset")
            for event in initial_diagnostics["events"]
            if event.get("event") == "dynamic_asset_entered" and event.get("asset")
        ]
        stability_displacement_m = 0.0
        stability_penetration = False
        if case_id in {"D03", "D05"} and active_assets:
            positions_before = {
                asset: _entity_pose(sim_env, asset)[0] for asset in active_assets
            }
            for _ in range(80):
                sim_env.sim.step()
            sim_env.sim.forward()
            settled = _frame(sim_env)
            cv2.imwrite(str(case_dir / "settled.png"), settled[::-1, :, ::-1])
            stability_displacement_m = max(
                float(
                    np.linalg.norm(
                        _entity_pose(sim_env, asset)[0] - positions_before[asset]
                    )
                )
                for asset in active_assets
            )
            stability_penetration = any(
                _entity_has_penetrating_contact(sim_env, asset)
                for asset in active_assets
            )
        if case_id in {"D03", "D05"}:
            runtime.before_simulation_step(sim_env, runtime.event_duration_steps)
            restored = _frame(sim_env)
            cv2.imwrite(str(case_dir / "restored.png"), restored[::-1, :, ::-1])
        diagnostics = runtime.diagnostics()
        assets = [event.get("asset") for event in diagnostics["events"] if event.get("asset")]
        expected_contacts = {
            event.get("reference")
            for event in diagnostics["events"]
            if event.get("reference")
        } | {
            event.get("anchor")
            for event in diagnostics["events"]
            if event.get("anchor")
        }
        collisions = [
            (asset, target)
            for asset in assets
            for target in runtime.plan.targets
            if target not in expected_contacts
            if _collision(sim_env, asset, target)
        ]
        required_events = {
            "D03": {"dynamic_asset_entered", "dynamic_asset_restored"},
            "D05": {"dynamic_asset_entered", "dynamic_asset_restored"},
        }.get(case_id, set())
        observed_events = {str(event.get("event")) for event in diagnostics["events"]}
        complete = not required_events or required_events <= observed_events
        stable = (
            case_id not in {"D03", "D05"}
            or (stability_displacement_m <= 0.05 and not stability_penetration)
        )
        changed = float(np.mean(np.abs(after.astype(float) - before.astype(float))))
        result = {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": case_id,
            "bddl": str(bddl),
            "events": diagnostics["events"],
            "event_count": len(diagnostics["events"]),
            "image_mean_abs_delta": round(changed, 4),
            "collision_pairs": collisions,
            "stability_displacement_m": round(stability_displacement_m, 6),
            "stability_penetration": stability_penetration,
            "status": (
                "PASS"
                if diagnostics["events"] and not collisions and complete and stable
                else "REVIEW"
            ),
            "entered_image": str(case_dir / "entered.png"),
            "settled_image": str(case_dir / "settled.png"),
            "restored_image": str(case_dir / "restored.png"),
        }
        return result
    except Exception as exc:
        return {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": case_id,
            "status": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if env is not None:
            env.close()


def main() -> None:
    global OUT

    args = _parse_args()
    os.environ.pop("MUJOCO_GL", None)
    if args.output is not None:
        OUT = args.output.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = _tasks()
    results = []
    selected = {case_id.upper() for case_id in args.case_id}
    representatives = [
        spec for spec in _representatives() if not selected or spec[2] in selected
    ]
    if selected - {spec[2] for spec in representatives}:
        missing = ", ".join(sorted(selected - {spec[2] for spec in representatives}))
        raise SystemExit(f"No weak representative found for: {missing}")
    for spec in representatives:
        print(f"[weak] {spec[0]} task{spec[1]} {spec[2]}", flush=True)
        results.append(_record(spec, tasks[spec]))
    (OUT / "weak_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(1 if any(item["status"] != "PASS" for item in results) else 0)


if __name__ == "__main__":
    main()
