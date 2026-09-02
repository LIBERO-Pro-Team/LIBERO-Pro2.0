"""Run a no-policy MuJoCo safety audit for every published task."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_ROOT = ROOT / "simulator-source"
if str(SIMULATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_ROOT))

from libero.libero.envs import OffScreenRenderEnv  # noqa: E402
from libero.libero.envs.nonphysical_perturbations import (  # noqa: E402
    _entity_deep_contacts,
    _entity_exists,
    _entity_pose,
    _entity_vertical_offsets,
    _support_height_at,
    _workspace_bounds,
)


MANIFEST = ROOT / "assets" / "task_manifest.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "all_task_safety_audit_20260824"
SUITES = ("libero_goal", "libero_object", "libero_spatial", "libero_10")
STATIC_ASSET_CASES = {"S03", "S05", "S10", "S11", "S12"}
SUPPORT_CHECK_CASES = {"S10", "S11"}


def _tasks() -> list[dict[str, Any]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return list(payload["tasks"])


def _entity_names(env: Any) -> tuple[str, ...]:
    return tuple(sorted(str(name) for name in getattr(env, "objects_dict", {})))


def _finite_scene(env: Any) -> tuple[bool, list[str]]:
    problems: list[str] = []
    model = env.sim.model
    data = env.sim.data
    for label, values in (
        ("qpos", np.asarray(data.qpos)),
        ("qvel", np.asarray(data.qvel)),
        ("body_xpos", np.asarray(data.body_xpos)),
    ):
        if not np.all(np.isfinite(values)):
            problems.append(f"nonfinite_{label}")
    if hasattr(model, "body_pos") and not np.all(np.isfinite(np.asarray(model.body_pos))):
        problems.append("nonfinite_model_body_pos")
    return not problems, problems


def _object_workspace_issues(env: Any, *, include_assets: bool) -> list[dict[str, Any]]:
    x_min, x_max, y_min, y_max = _workspace_bounds(env)
    issues = []
    for name in _entity_names(env):
        if name.startswith("perturbation_") and not include_assets:
            continue
        try:
            position, _ = _entity_pose(env, name)
        except Exception:
            continue
        if not all(np.isfinite(position)):
            continue
        if name.startswith("perturbation_") and position[2] < -1.0:
            # Dynamic assets are intentionally staged below the scene until an event.
            continue
        if not (x_min <= position[0] <= x_max and y_min <= position[1] <= y_max):
            issues.append(
                {
                    "entity": name,
                    "position": position.tolist(),
                    "bounds": [x_min, x_max, y_min, y_max],
                }
            )
    return issues


def _deep_contacts(env: Any, *, include_assets: bool) -> list[dict[str, Any]]:
    contacts: list[dict[str, Any]] = []
    for name in _entity_names(env):
        if name.startswith("perturbation_") and not include_assets:
            continue
        if name.startswith("perturbation_"):
            try:
                position, _ = _entity_pose(env, name)
            except Exception:
                continue
            if position[2] < -1.0:
                continue
        try:
            for contact in _entity_deep_contacts(env, name, tolerance=0.002):
                item = dict(contact)
                item["entity"] = name
                if item not in contacts:
                    contacts.append(item)
        except Exception:
            continue
    return contacts


def _static_assets(runtime: Any) -> list[str]:
    assets = []
    for event in runtime.events:
        if str(event.get("event", "")).startswith("static_asset_placed") and event.get("asset"):
            name = str(event["asset"])
            if name not in assets:
                assets.append(name)
    return assets


def _support_checks(env: Any, runtime: Any, case_id: str) -> list[dict[str, Any]]:
    if case_id not in SUPPORT_CHECK_CASES:
        return []
    params = dict(runtime.plan.params)
    checks = []
    for name in _static_assets(runtime):
        try:
            position, _ = _entity_pose(env, name)
            bottom_offset, _ = _entity_vertical_offsets(env, name)
            support = _support_height_at(env, position[:2], params, ignored=(name,))
            event = next(
                (
                    item
                    for item in runtime.events
                    if item.get("asset") == name
                    and str(item.get("event", "")).startswith("static_asset_placed")
                ),
                {},
            )
            if support is None:
                checks.append(
                    {
                        "asset": name,
                        "status": "REVIEW",
                        "reason": "no_support_surface_under_asset",
                        "event_support_geom": event.get("support_geom"),
                    }
                )
                continue
            bottom = float(position[2] + bottom_offset)
            gap = float(bottom - support[0])
            checks.append(
                {
                    "asset": name,
                    "support_geom": support[1],
                    "event_support_geom": event.get("support_geom"),
                    "bottom_gap_m": round(gap, 6),
                    "status": "PASS" if -0.002 <= gap <= 0.025 else "REVIEW",
                }
            )
        except Exception as exc:
            checks.append(
                {
                    "asset": name,
                    "status": "REVIEW",
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            )
    return checks


def _contact_key(contact: dict[str, Any]) -> tuple[str, str]:
    return str(contact.get("first", "")), str(contact.get("second", ""))


def _new_deep_contacts(
    current: list[dict[str, Any]], baseline: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    baseline_depths: dict[tuple[str, str], float] = {}
    current_worst: dict[tuple[str, str], dict[str, Any]] = {}
    for item in baseline:
        key = _contact_key(item)
        baseline_depths[key] = max(
            baseline_depths.get(key, 0.0), float(item.get("depth_m", 0.0))
        )
    for item in current:
        key = _contact_key(item)
        if float(item.get("depth_m", 0.0)) > float(
            current_worst.get(key, {}).get("depth_m", 0.0)
        ):
            current_worst[key] = item
    return [
        item
        for key, item in current_worst.items()
        if key not in baseline_depths
        or float(item.get("depth_m", 0.0)) > baseline_depths[key] + 0.002
    ]


def _audit_base(item: dict[str, Any], *, settle_steps: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Capture the corresponding unperturbed scene for contact comparisons."""

    suite = str(item["suite"])
    task_id = int(item["base_task_id"])
    bddl = ROOT / "assets" / str(item["bddl_path"])
    env_wrapper = None
    try:
        np.random.seed(143)
        env_wrapper = OffScreenRenderEnv(
            bddl_file_name=str(bddl),
            use_camera_obs=False,
            camera_heights=64,
            camera_widths=64,
            max_reset_attempts=50,
        )
        env_wrapper.seed(143)
        env_wrapper.reset()
        env = env_wrapper.env
        finite_before, finite_issues_before = _finite_scene(env)
        deep_before = _deep_contacts(env, include_assets=False)
        workspace_before = _object_workspace_issues(env, include_assets=False)
        for _ in range(int(settle_steps)):
            env.sim.step()
        env.sim.forward()
        finite_after, finite_issues_after = _finite_scene(env)
        deep_after = _deep_contacts(env, include_assets=False)
        workspace_after = _object_workspace_issues(env, include_assets=False)
        result = {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": "BASE",
            "bddl": str(bddl),
            "status": "PASS" if finite_before and finite_after and not workspace_before and not workspace_after else "RESET_ERROR",
            "failures": [] if finite_before and finite_after and not workspace_before and not workspace_after else ["base_scene_safety"],
            "reset_success": True,
            "task_success_at_reset": bool(env._check_success()),
            "runtime_event_count": 0,
            "runtime_events": [],
            "static_assets": [],
            "support_checks": [],
            "finite_issues_before": finite_issues_before,
            "finite_issues_after": finite_issues_after,
            "deep_contacts_before": deep_before,
            "deep_contacts_after": deep_after,
            "workspace_issues_before": workspace_before,
            "workspace_issues_after": workspace_after,
        }
        baseline = {
            "deep_contacts_before": deep_before,
            "deep_contacts_after": deep_after,
            "workspace_issues_before": workspace_before,
            "workspace_issues_after": workspace_after,
        }
        return result, baseline
    except Exception as exc:
        result = {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": "BASE",
            "bddl": str(bddl),
            "status": "RESET_ERROR",
            "failures": ["reset_exception"],
            "error": f"{type(exc).__name__}: {exc}",
        }
        return result, {"error": result["error"]}
    finally:
        if env_wrapper is not None:
            env_wrapper.close()


def _audit(
    item: dict[str, Any],
    *,
    settle_steps: int,
    baseline: dict[str, Any],
) -> dict[str, Any]:
    suite = str(item["suite"])
    task_id = int(item["base_task_id"])
    case_id = str(item["case_id"]).upper()
    bddl = ROOT / "assets" / str(item["bddl_path"])
    env_wrapper = None
    try:
        np.random.seed(143)
        env_wrapper = OffScreenRenderEnv(
            bddl_file_name=str(bddl),
            use_camera_obs=False,
            camera_heights=64,
            camera_widths=64,
            max_reset_attempts=50,
        )
        env_wrapper.seed(143)
        env_wrapper.reset()
        env = env_wrapper.env
        runtime = env.perturbation_runtime
        finite_before, finite_issues_before = _finite_scene(env)
        include_assets = case_id.startswith("S")
        deep_before = _deep_contacts(env, include_assets=include_assets)
        workspace_before = _object_workspace_issues(env, include_assets=include_assets)
        task_success = bool(env._check_success())
        static_assets = _static_assets(runtime)
        support_checks = _support_checks(env, runtime, case_id)
        positions_before = {
            name: _entity_pose(env, name)[0]
            for name in _entity_names(env)
            if not name.startswith("perturbation_") or include_assets
        }

        for _ in range(int(settle_steps)):
            env.sim.step()
        env.sim.forward()

        finite_after, finite_issues_after = _finite_scene(env)
        deep_after = _deep_contacts(env, include_assets=include_assets)
        workspace_after = _object_workspace_issues(env, include_assets=include_assets)
        displacements = {}
        for name, before in positions_before.items():
            if not _entity_exists(env, name):
                continue
            after, _ = _entity_pose(env, name)
            displacements[name] = float(np.linalg.norm(after - before))

        failures: list[str] = []
        if not finite_before or not finite_after:
            failures.append("nonfinite_scene_state")
        if task_success and case_id != "BASE":
            failures.append("task_successful_at_reset")
        if workspace_before or workspace_after:
            failures.append("object_outside_workspace")
        new_deep_before = _new_deep_contacts(
            deep_before, baseline.get("deep_contacts_before", [])
        )
        new_deep_after = _new_deep_contacts(
            deep_after, baseline.get("deep_contacts_after", [])
        )
        if new_deep_before or new_deep_after:
            failures.append("deep_penetration")
        path_review = case_id in {"S05", "D05"}
        limitations = []
        if path_review:
            limitations.append("alternate_path_requires_trajectory_or_geometric_planner_probe")
        if case_id.startswith("D"):
            limitations.append("dynamic_trigger_not_forced_in_no_rollout_audit")

        status = "PASS"
        if failures:
            status = "RESET_ERROR"
        elif any(check["status"] != "PASS" for check in support_checks):
            status = "PHYSICS_REVIEW"
        elif limitations:
            status = "VALIDATOR_LIMITATION"

        return {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": case_id,
            "bddl": str(bddl),
            "status": status,
            "failures": failures,
            "limitations": limitations,
            "reset_success": True,
            "task_success_at_reset": task_success,
            "runtime_event_count": len(runtime.events),
            "runtime_events": runtime.events,
            "static_assets": static_assets,
            "support_checks": support_checks,
            "finite_issues_before": finite_issues_before,
            "finite_issues_after": finite_issues_after,
            "deep_contacts_before": deep_before,
            "deep_contacts_after": deep_after,
            "new_deep_contacts_before": new_deep_before,
            "new_deep_contacts_after": new_deep_after,
            "workspace_issues_before": workspace_before,
            "workspace_issues_after": workspace_after,
            "max_object_displacement_after_settle_m": round(max(displacements.values(), default=0.0), 6),
            "object_displacements_m": {
                name: round(value, 6) for name, value in displacements.items() if value > 0.005
            },
        }
    except Exception as exc:
        return {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": case_id,
            "bddl": str(bddl),
            "status": "RESET_ERROR",
            "failures": ["reset_exception"],
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if env_wrapper is not None:
            env_wrapper.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--settle-steps", type=int, default=80)
    parser.add_argument("--suite", action="append", choices=SUITES)
    parser.add_argument("--case-id", action="append")
    args = parser.parse_args()
    if args.settle_steps < 0:
        raise SystemExit("--settle-steps must be non-negative")

    os.environ.setdefault("MUJOCO_GL", "wgl")
    selected_suites = set(args.suite or SUITES)
    selected_cases = {str(value).upper() for value in (args.case_id or [])}
    all_items = _tasks()
    items = [
        item
        for item in all_items
        if str(item["suite"]) in selected_suites
        and (not selected_cases or str(item["case_id"]).upper() in selected_cases)
    ]
    results = []
    baselines: dict[tuple[str, int], dict[str, Any]] = {}
    base_items = {
        (str(item["suite"]), int(item["base_task_id"])): item
        for item in all_items
        if str(item["case_id"]).upper() == "BASE"
        and str(item["suite"]) in selected_suites
    }
    for key, item in sorted(base_items.items()):
        print(f"[physics-base] {key}", flush=True)
        base_result, baseline = _audit_base(item, settle_steps=args.settle_steps)
        baselines[key] = baseline
        results.append(base_result)

    non_base_items = [
        item for item in items if str(item["case_id"]).upper() != "BASE"
    ]
    for index, item in enumerate(non_base_items, start=1):
        key = (item["suite"], item["base_task_id"], item["case_id"])
        print(f"[physics] {index}/{len(non_base_items)} {key}", flush=True)
        result = _audit(
            item,
            settle_steps=args.settle_steps,
            baseline=baselines.get(
                (str(item["suite"]), int(item["base_task_id"])), {}
            ),
        )
        results.append(result)
        if result["status"] != "PASS":
            print(json.dumps(result, ensure_ascii=False), flush=True)

    status_counts: dict[str, int] = {}
    failure_counts: dict[str, int] = {}
    limitation_counts: dict[str, int] = {}
    for result in results:
        status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1
        for failure in result.get("failures", []):
            failure_counts[failure] = failure_counts.get(failure, 0) + 1
        for limitation in result.get("limitations", []):
            limitation_counts[limitation] = limitation_counts.get(limitation, 0) + 1
    report = {
        "audit_type": "no_policy_mujoco_reset_and_settle",
        "seed": 143,
        "settle_steps": args.settle_steps,
        "task_count": len(results),
        "summary": {
            "status_counts": dict(sorted(status_counts.items())),
            "failure_counts": dict(sorted(failure_counts.items())),
            "limitation_counts": dict(sorted(limitation_counts.items())),
        },
        "results": results,
    }
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "physics_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False), flush=True)
    print(f"Report: {report_path}", flush=True)
    raise SystemExit(1 if status_counts.get("RESET_ERROR") else 0)


if __name__ == "__main__":
    main()
