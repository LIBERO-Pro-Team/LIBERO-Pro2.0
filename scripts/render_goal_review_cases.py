"""Render and audit every visible libero-goal case changed by the Goal review."""

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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SIMULATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_ROOT))

from libero.libero.envs import OffScreenRenderEnv  # noqa: E402
from libero.libero.envs.nonphysical_perturbations import (  # noqa: E402
    _entity_body_ids,
    _entity_exists,
    _entity_pose,
    _workspace_bounds,
)
from scripts.audit_all_task_physics import (  # noqa: E402
    _deep_contacts,
    _finite_scene,
    _new_deep_contacts,
    _object_workspace_issues,
    _static_assets,
    _support_checks,
)


MANIFEST = ROOT / "assets" / "task_manifest.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "goal_review_seed143_render_20260829"
VISIBLE_CASES = (
    "S02",
    "S03",
    "S04",
    "S05",
    "S06",
    "S07",
    "S08",
    "S09",
    "S10",
    "S11",
    "S12",
    "S13",
)
SEED = 143


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--settle-steps", type=int, default=80)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--case-id", action="append", default=[])
    return parser.parse_args()


def _manifest_tasks() -> list[dict[str, Any]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return list(payload["tasks"])


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
    image = np.asarray(frame, dtype=np.float64)
    return {
        "shape": list(frame.shape),
        "min": int(np.min(frame)),
        "max": int(np.max(frame)),
        "mean": round(float(np.mean(image)), 6),
        "std": round(float(np.std(image)), 6),
        "nonblank": bool(np.std(image) > 1.0 and np.max(frame) > np.min(frame)),
    }


def _difference_metrics(first: np.ndarray, second: np.ndarray) -> dict[str, float]:
    delta = np.abs(
        np.asarray(first, dtype=np.float64) - np.asarray(second, dtype=np.float64)
    )
    return {
        "mean_abs_delta": round(float(np.mean(delta)), 6),
        "changed_pixel_ratio_gt12": round(
            float(np.mean(np.max(delta, axis=2) > 12.0)), 6
        ),
    }


def _positions(env: Any, *, include_assets: bool) -> dict[str, np.ndarray]:
    values: dict[str, np.ndarray] = {}
    for name in sorted(getattr(env, "objects_dict", {})):
        if name.startswith("perturbation_") and not include_assets:
            continue
        if not _entity_exists(env, name):
            continue
        try:
            position, _ = _entity_pose(env, name)
        except Exception:
            continue
        values[name] = np.asarray(position, dtype=np.float64)
    return values


def _displacements(
    before: dict[str, np.ndarray], after: dict[str, np.ndarray]
) -> dict[str, float]:
    return {
        name: float(np.linalg.norm(after[name] - position))
        for name, position in before.items()
        if name in after
    }


def _entity_xy_bounds(env: Any, name: str) -> tuple[float, float, float, float] | None:
    body_ids = set(_entity_body_ids(env, name))
    bounds: list[tuple[float, float, float, float]] = []
    for geom_id, body_id in enumerate(env.sim.model.geom_bodyid):
        if int(body_id) not in body_ids:
            continue
        if (
            hasattr(env.sim.model, "geom_group")
            and int(env.sim.model.geom_group[geom_id]) != 0
        ):
            continue
        aabb = np.asarray(env.sim.model.geom_aabb[geom_id], dtype=np.float64)
        rotation = np.asarray(
            env.sim.data.geom_xmat[geom_id], dtype=np.float64
        ).reshape(3, 3)
        center = (
            np.asarray(env.sim.data.geom_xpos[geom_id], dtype=np.float64)
            + rotation @ aabb[:3]
        )
        extent = np.abs(rotation) @ aabb[3:]
        bounds.append(
            (
                float(center[0] - extent[0]),
                float(center[0] + extent[0]),
                float(center[1] - extent[1]),
                float(center[1] + extent[1]),
            )
        )
    if not bounds:
        return None
    return (
        min(value[0] for value in bounds),
        max(value[1] for value in bounds),
        min(value[2] for value in bounds),
        max(value[3] for value in bounds),
    )


def _s05_path_review(env: Any, runtime: Any) -> dict[str, Any]:
    workspace = _workspace_bounds(env)
    assets = _static_assets(runtime)
    asset_reviews = []
    for name in assets:
        bounds = _entity_xy_bounds(env, name)
        if bounds is None:
            asset_reviews.append(
                {"asset": name, "status": "REVIEW", "reason": "missing_xy_bounds"}
            )
            continue
        x_min, x_max, y_min, y_max = bounds
        wx_min, wx_max, wy_min, wy_max = workspace
        gaps = {
            "left_m": max(0.0, x_min - wx_min),
            "right_m": max(0.0, wx_max - x_max),
            "front_m": max(0.0, y_min - wy_min),
            "back_m": max(0.0, wy_max - y_max),
        }
        max_gap = max(gaps.values())
        asset_reviews.append(
            {
                "asset": name,
                "bounds_xy": [round(value, 6) for value in bounds],
                "workspace_xy": [round(value, 6) for value in workspace],
                "side_gaps_m": {
                    key: round(value, 6) for key, value in gaps.items()
                },
                "maximum_side_gap_m": round(max_gap, 6),
                "status": "PASS" if max_gap >= 0.08 else "REVIEW",
            }
        )
    return {
        "assets": asset_reviews,
        "status": (
            "PASS"
            if asset_reviews and all(item["status"] == "PASS" for item in asset_reviews)
            else "REVIEW"
        ),
        "limitation": "geometric_side_gap_does_not_prove_policy_trajectory_success",
    }


def _open_environment(bddl: Path, image_size: int) -> Any:
    np.random.seed(SEED)
    wrapper = OffScreenRenderEnv(
        bddl_file_name=str(bddl),
        camera_heights=image_size,
        camera_widths=image_size,
        max_reset_attempts=50,
    )
    wrapper.seed(SEED)
    wrapper.reset()
    return wrapper


def _render_base(
    item: dict[str, Any], *, output: Path, image_size: int, settle_steps: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    task_id = int(item["base_task_id"])
    bddl = ROOT / "assets" / str(item["bddl_path"])
    case_dir = output / "base" / f"task{task_id}"
    wrapper = None
    try:
        wrapper = _open_environment(bddl, image_size)
        env = wrapper.env
        first = _frame(env)
        first_path = case_dir / "BASE_seed143_first.png"
        _write_frame(first_path, first)
        positions_before = _positions(env, include_assets=False)
        deep_before = _deep_contacts(env, include_assets=False)
        workspace_before = _object_workspace_issues(env, include_assets=False)
        finite_before, finite_issues_before = _finite_scene(env)
        success_before = bool(env._check_success())
        for _ in range(settle_steps):
            env.sim.step()
        env.sim.forward()
        settled = _frame(env)
        settled_path = case_dir / "BASE_seed143_settled.png"
        _write_frame(settled_path, settled)
        positions_after = _positions(env, include_assets=False)
        deep_after = _deep_contacts(env, include_assets=False)
        workspace_after = _object_workspace_issues(env, include_assets=False)
        finite_after, finite_issues_after = _finite_scene(env)
        success_after = bool(env._check_success())
        moves = _displacements(positions_before, positions_after)
        failures = []
        if not finite_before or not finite_after:
            failures.append("nonfinite_scene_state")
        if workspace_before or workspace_after:
            failures.append("object_outside_workspace")
        if success_before or success_after:
            failures.append("base_task_successful_without_policy")
        result = {
            "suite": "libero_goal",
            "base_task_id": task_id,
            "case_id": "BASE",
            "seed": SEED,
            "bddl": str(bddl),
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
            "finite_issues_before": finite_issues_before,
            "finite_issues_after": finite_issues_after,
            "workspace_issues_before": workspace_before,
            "workspace_issues_after": workspace_after,
            "task_success_before": success_before,
            "task_success_after": success_after,
            "max_object_displacement_m": round(max(moves.values(), default=0.0), 6),
            "image_first": str(first_path),
            "image_settled": str(settled_path),
            "image_metrics_first": _image_metrics(first),
            "image_metrics_settled": _image_metrics(settled),
        }
        baseline = {
            "first_frame": first,
            "settled_frame": settled,
            "deep_contacts_before": deep_before,
            "deep_contacts_after": deep_after,
            "object_displacements": moves,
        }
        return result, baseline
    except Exception as exc:
        return (
            {
                "suite": "libero_goal",
                "base_task_id": task_id,
                "case_id": "BASE",
                "status": "ERROR",
                "failures": ["reset_or_render_exception"],
                "error": f"{type(exc).__name__}: {exc}",
            },
            {"error": f"{type(exc).__name__}: {exc}"},
        )
    finally:
        if wrapper is not None:
            wrapper.close()


def _render_case(
    item: dict[str, Any],
    *,
    output: Path,
    image_size: int,
    settle_steps: int,
    baseline: dict[str, Any],
) -> dict[str, Any]:
    task_id = int(item["base_task_id"])
    case_id = str(item["case_id"]).upper()
    bddl = ROOT / "assets" / str(item["bddl_path"])
    case_dir = output / case_id / f"task{task_id}"
    wrapper = None
    try:
        if "error" in baseline:
            raise RuntimeError(f"BASE unavailable: {baseline['error']}")
        wrapper = _open_environment(bddl, image_size)
        env = wrapper.env
        runtime = env.perturbation_runtime
        first = _frame(env)
        first_path = case_dir / f"{case_id}_seed143_first.png"
        _write_frame(first_path, first)
        positions_before = _positions(env, include_assets=True)
        deep_before = _deep_contacts(env, include_assets=True)
        workspace_before = _object_workspace_issues(env, include_assets=True)
        finite_before, finite_issues_before = _finite_scene(env)
        success_before = bool(env._check_success())
        static_assets = _static_assets(runtime)
        support_before = _support_checks(env, runtime, case_id)
        path_review = _s05_path_review(env, runtime) if case_id == "S05" else None

        for _ in range(settle_steps):
            env.sim.step()
        env.sim.forward()

        settled = _frame(env)
        settled_path = case_dir / f"{case_id}_seed143_settled.png"
        _write_frame(settled_path, settled)
        positions_after = _positions(env, include_assets=True)
        deep_after = _deep_contacts(env, include_assets=True)
        workspace_after = _object_workspace_issues(env, include_assets=True)
        finite_after, finite_issues_after = _finite_scene(env)
        success_after = bool(env._check_success())
        support_after = _support_checks(env, runtime, case_id)
        moves = _displacements(positions_before, positions_after)
        base_moves = baseline["object_displacements"]
        excess_moves = {
            name: max(0.0, value - float(base_moves.get(name, 0.0)) - 0.01)
            for name, value in moves.items()
            if not name.startswith("perturbation_")
        }
        new_deep_before = _new_deep_contacts(
            deep_before, baseline["deep_contacts_before"]
        )
        new_deep_after = _new_deep_contacts(
            deep_after, baseline["deep_contacts_after"]
        )
        first_metrics = _image_metrics(first)
        settled_metrics = _image_metrics(settled)
        difference_first = _difference_metrics(baseline["first_frame"], first)
        difference_settled = _difference_metrics(
            baseline["settled_frame"], settled
        )
        failures: list[str] = []
        if not runtime.events:
            failures.append("missing_runtime_event")
        if not first_metrics["nonblank"] or not settled_metrics["nonblank"]:
            failures.append("blank_render")
        if difference_first["mean_abs_delta"] < 0.05:
            failures.append("no_visible_scene_change")
        if not finite_before or not finite_after:
            failures.append("nonfinite_scene_state")
        if workspace_before or workspace_after:
            failures.append("object_outside_workspace")
        if new_deep_before or new_deep_after:
            failures.append("deep_penetration")
        if success_before or success_after:
            failures.append("task_successful_without_policy")
        if any(check.get("status") != "PASS" for check in support_before + support_after):
            failures.append("support_check_failed")
        if max(excess_moves.values(), default=0.0) > 0.25:
            failures.append("scene_instability")
        if path_review is not None and path_review["status"] != "PASS":
            failures.append("s05_no_geometric_side_gap")
        return {
            "suite": "libero_goal",
            "base_task_id": task_id,
            "case_id": case_id,
            "seed": SEED,
            "settle_steps": settle_steps,
            "bddl": str(bddl),
            "status": "PASS" if not failures else "FAIL",
            "failures": failures,
            "runtime_events": list(runtime.events),
            "static_assets": static_assets,
            "support_checks_before": support_before,
            "support_checks_after": support_after,
            "path_review": path_review,
            "finite_issues_before": finite_issues_before,
            "finite_issues_after": finite_issues_after,
            "workspace_issues_before": workspace_before,
            "workspace_issues_after": workspace_after,
            "new_deep_contacts_before": new_deep_before,
            "new_deep_contacts_after": new_deep_after,
            "task_success_before": success_before,
            "task_success_after": success_after,
            "max_object_displacement_m": round(max(moves.values(), default=0.0), 6),
            "max_excess_displacement_vs_base_m": round(
                max(excess_moves.values(), default=0.0), 6
            ),
            "object_excess_displacements_m": {
                name: round(value, 6)
                for name, value in excess_moves.items()
                if value > 0.005
            },
            "image_first": str(first_path),
            "image_settled": str(settled_path),
            "image_metrics_first": first_metrics,
            "image_metrics_settled": settled_metrics,
            "image_vs_base_first": difference_first,
            "image_vs_base_settled": difference_settled,
        }
    except Exception as exc:
        return {
            "suite": "libero_goal",
            "base_task_id": task_id,
            "case_id": case_id,
            "seed": SEED,
            "bddl": str(bddl),
            "status": "ERROR",
            "failures": ["reset_or_render_exception"],
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if wrapper is not None:
            wrapper.close()


def _contact_sheet(
    case_id: str,
    results: list[dict[str, Any]],
    base_results: dict[int, dict[str, Any]],
    output: Path,
) -> str:
    rows = []
    for result in sorted(results, key=lambda value: int(value["base_task_id"])):
        if result["status"] == "ERROR":
            continue
        task_id = int(result["base_task_id"])
        paths = (
            Path(base_results[task_id]["image_first"]),
            Path(base_results[task_id]["image_settled"]),
            Path(result["image_first"]),
            Path(result["image_settled"]),
        )
        images = [cv2.imread(str(path), cv2.IMREAD_COLOR) for path in paths]
        if any(image is None for image in images):
            continue
        height = max(image.shape[0] for image in images if image is not None)
        label = np.full((30, sum(image.shape[1] for image in images), 3), 245, np.uint8)
        cv2.putText(
            label,
            f"task{task_id} {case_id} {result['status']} | BASE first / BASE settled / case first / case settled",
            (8, 21),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        normalized = [
            image
            if image.shape[0] == height
            else cv2.resize(image, (image.shape[1], height))
            for image in images
        ]
        rows.append(np.vstack((label, np.hstack(normalized))))
    if not rows:
        return ""
    width = max(row.shape[1] for row in rows)
    padded = [
        cv2.copyMakeBorder(
            row, 0, 0, 0, width - row.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        for row in rows
    ]
    sheet = np.vstack(padded)
    path = output / "contact_sheets" / f"{case_id}_seed143.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92]):
        raise RuntimeError(f"Failed to write contact sheet: {path}")
    return str(path)


def main() -> None:
    args = _parse_args()
    if args.settle_steps < 0:
        raise SystemExit("--settle-steps must be non-negative")
    if args.image_size < 64:
        raise SystemExit("--image-size must be at least 64")
    selected_cases = {str(value).upper() for value in args.case_id}
    unknown = selected_cases - set(VISIBLE_CASES)
    if unknown:
        raise SystemExit(f"Unsupported case ids: {', '.join(sorted(unknown))}")
    active_cases = selected_cases or set(VISIBLE_CASES)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MUJOCO_GL", "wgl")

    tasks = _manifest_tasks()
    base_items = {
        int(item["base_task_id"]): item
        for item in tasks
        if item["suite"] == "libero_goal" and item["case_id"] == "BASE"
    }
    case_items = [
        item
        for item in tasks
        if item["suite"] == "libero_goal" and item["case_id"] in active_cases
    ]
    base_results: dict[int, dict[str, Any]] = {}
    baselines: dict[int, dict[str, Any]] = {}
    for task_id, item in sorted(base_items.items()):
        print(f"[base] libero_goal task{task_id}", flush=True)
        result, baseline = _render_base(
            item,
            output=output,
            image_size=args.image_size,
            settle_steps=args.settle_steps,
        )
        base_results[task_id] = result
        baselines[task_id] = baseline

    results = []
    for index, item in enumerate(case_items, start=1):
        task_id = int(item["base_task_id"])
        case_id = str(item["case_id"])
        print(
            f"[render] {index}/{len(case_items)} libero_goal task{task_id} {case_id}",
            flush=True,
        )
        result = _render_case(
            item,
            output=output,
            image_size=args.image_size,
            settle_steps=args.settle_steps,
            baseline=baselines[task_id],
        )
        results.append(result)
        if result["status"] != "PASS":
            print(json.dumps(result, ensure_ascii=False), flush=True)

    contact_sheets = {}
    for case_id in VISIBLE_CASES:
        matching = [result for result in results if result["case_id"] == case_id]
        if matching:
            contact_sheets[case_id] = _contact_sheet(
                case_id, matching, base_results, output
            )

    status_counts: dict[str, int] = {}
    failure_counts: dict[str, int] = {}
    for result in results:
        status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1
        for failure in result.get("failures", []):
            failure_counts[failure] = failure_counts.get(failure, 0) + 1
    report = {
        "audit_type": "libero_goal_visible_review_render_and_physics",
        "seed": SEED,
        "settle_steps": args.settle_steps,
        "image_size": args.image_size,
        "case_ids": sorted(active_cases),
        "base_count": len(base_results),
        "task_count": len(results),
        "summary": {
            "status_counts": dict(sorted(status_counts.items())),
            "failure_counts": dict(sorted(failure_counts.items())),
            "base_status_counts": {
                status: sum(1 for item in base_results.values() if item["status"] == status)
                for status in sorted({item["status"] for item in base_results.values()})
            },
            "contact_sheets": contact_sheets,
            "limitations": [
                "No-policy rendering cannot prove PI0 trajectory success.",
                "S05 side-gap checks do not prove that a particular policy will find the alternate path.",
            ],
        },
        "base_results": list(base_results.values()),
        "results": results,
    }
    report_path = output / "render_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2), flush=True)
    print(f"Report: {report_path}", flush=True)
    raise SystemExit(
        1
        if any(item["status"] != "PASS" for item in results)
        or any(item["status"] != "PASS" for item in base_results.values())
        else 0
    )


if __name__ == "__main__":
    main()
