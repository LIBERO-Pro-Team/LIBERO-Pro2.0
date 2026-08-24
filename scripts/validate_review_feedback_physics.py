"""Validate reviewed scene defects after a short MuJoCo stabilization window."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import cv2
import mujoco
import numpy as np

from libero.libero.envs import OffScreenRenderEnv
from libero.libero.envs.nonphysical_perturbations import (
    _entity_body_ids,
    _entity_exists,
    _entity_has_penetrating_contact,
    _entity_has_support_contact,
    _entity_pose,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"
OUT = ROOT / "outputs" / "review_feedback_current_20260819" / "physics"
DEFAULT_CASES = [
    ("libero_spatial", 2, "S10"),
    ("libero_spatial", 3, "S04"),
    ("libero_spatial", 4, "S11"),
    ("libero_spatial", 5, "S11"),
    ("libero_spatial", 7, "S11"),
    ("libero_spatial", 9, "S11"),
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate reviewed perturbation scenes with MuJoCo physics."
    )
    parser.add_argument(
        "--all-s04-s10-s11",
        action="store_true",
        help="Validate S04, S10, and S11 for every base task in all four suites.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override the output directory.",
    )
    return parser.parse_args()


def _tasks() -> dict[tuple[str, int, str], dict[str, Any]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        (item["suite"], int(item["base_task_id"]), item["case_id"]): item
        for item in manifest["tasks"]
    }


def _save_frame(env: Any, path: Path) -> None:
    env._update_observables(force=True)
    frame = np.asarray(env._get_observations()["agentview_image"])
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), frame[::-1, :, ::-1])


def _body_speed(env: Any, name: str) -> float:
    speeds = []
    for body_id in _entity_body_ids(env, name):
        try:
            speeds.append(float(np.linalg.norm(env.sim.data.cvel[body_id])))
        except Exception:
            continue
    return max(speeds, default=0.0)


def _bottom_support_gap(env: Any, name: str) -> tuple[float, str | None]:
    """Return the vertical gap from an entity AABB bottom to the surface below."""

    model = env.sim.model
    data = env.sim.data
    body_id = int(env.obj_body_id[name])
    body_ids = set(_entity_body_ids(env, name))
    collision_geom_ids = {
        geom_id
        for geom_id, geom_body_id in enumerate(model.geom_bodyid)
        if int(geom_body_id) in body_ids
        and (
            not hasattr(model, "geom_group")
            or int(model.geom_group[geom_id]) == 0
        )
        and (
            not hasattr(model, "geom_contype")
            or int(model.geom_contype[geom_id]) != 0
        )
    }
    bottoms = []
    for geom_id, geom_body_id in enumerate(model.geom_bodyid):
        if int(geom_body_id) not in body_ids:
            continue
        if collision_geom_ids and geom_id not in collision_geom_ids:
            continue
        aabb = np.asarray(model.geom_aabb[geom_id], dtype=np.float64)
        rotation = np.asarray(data.geom_xmat[geom_id], dtype=np.float64).reshape(3, 3)
        center = np.asarray(data.geom_xpos[geom_id], dtype=np.float64) + rotation @ aabb[:3]
        vertical_extent = float(np.abs(rotation[2]) @ aabb[3:])
        bottoms.append(float(center[2] - vertical_extent))
    if not bottoms:
        raise RuntimeError(f"No geom AABB for {name}")
    bottom = min(bottoms)
    origin = np.array([data.body_xpos[body_id, 0], data.body_xpos[body_id, 1], bottom + 0.002])
    geom_id = np.array([-1], dtype=np.int32)
    geom_group = np.ones(6, dtype=np.uint8)
    distance = float(
        mujoco.mj_ray(
            model._model,
            data._data,
            origin,
            np.array([0.0, 0.0, -1.0]),
            geom_group,
            1,
            body_id,
            geom_id,
        )
    )
    if distance < 0.0:
        return float("inf"), None
    gap = max(0.0, distance - 0.002)
    support_name = model.geom_id2name(int(geom_id[0])) if geom_id[0] >= 0 else None
    return gap, support_name


def _declared_support_matches(
    configured: Any, actual_geom: str | None, placement_geom: str | None
) -> bool:
    if configured is None:
        return True
    values = configured if isinstance(configured, (list, tuple)) else (configured,)
    tokens = tuple(str(value).casefold() for value in values if str(value))
    if not tokens:
        return True
    observed = " ".join(
        str(value or "").casefold() for value in (actual_geom, placement_geom)
    )
    for token in tokens:
        if token in observed:
            return True
        if "table" in token and "table" in observed:
            return True
        if "floor" in token and "floor" in observed:
            return True
    return False


def _case(suite: str, task_id: int, case_id: str, task: dict[str, Any]) -> dict[str, Any]:
    case_dir = OUT / f"{suite}_task{task_id}_{case_id}"
    bddl = ROOT / "assets" / task["bddl_path"]
    np.random.seed(142)
    env = None
    try:
        env = OffScreenRenderEnv(
            bddl_file_name=str(bddl), camera_heights=256, camera_widths=256
        )
        env.reset()
        sim_env = env.env
        runtime = sim_env.perturbation_runtime
        event = runtime.events[-1] if runtime.events else {}
        placement_events = {
            str(item["asset"]): item
            for item in runtime.events
            if item.get("asset") and item.get("event", "").startswith("static_asset_placed")
        }
        placement_supports = {
            name: item.get("support_geom") for name, item in placement_events.items()
        }
        if case_id == "S04":
            tracked_entities = tuple(runtime.plan.targets)
            swap_support_event = next(
                (
                    item
                    for item in runtime.events
                    if item.get("first") and item.get("second")
                ),
                {},
            )
            if len(tracked_entities) == 2:
                placement_supports.update(
                    {
                        tracked_entities[0]: swap_support_event.get("first_support"),
                        tracked_entities[1]: swap_support_event.get("second_support"),
                    }
                )
        elif case_id in {"S10", "S11"} and placement_events:
            tracked_entities = tuple(placement_events)
        else:
            asset = event.get("asset")
            tracked_entities = (
                asset or event.get("target") or runtime.plan.targets[0],
            )
        before_poses = {
            name: _entity_pose(sim_env, name)[0] for name in tracked_entities
        }
        _save_frame(sim_env, case_dir / "before_settle.png")
        neutral_action = np.zeros(int(sim_env.action_dim), dtype=np.float64)
        for _ in range(250):
            env.step(neutral_action)
        sim_env.sim.forward()
        after_poses = {
            name: _entity_pose(sim_env, name)[0] for name in tracked_entities
        }
        _save_frame(sim_env, case_dir / "after_settle.png")

        changed_xy = True
        if case_id == "S04" and len(runtime.plan.targets) == 2:
            swap_event = next(
                (
                    item
                    for item in runtime.events
                    if item.get("event")
                    in {
                        "planar_object_position_swap",
                        "grounded_planar_object_position_swap",
                        "stacked_target_grounded_offset",
                        "same_class_layout_offset",
                        "planar_swap_grounded_fallback",
                        "articulation_fixture_pose_offset",
                    }
                ),
                {},
            )
            if "delta_xy" in swap_event:
                changed_xy = bool(
                    np.linalg.norm(np.asarray(swap_event["delta_xy"])) >= 0.02
                )
            else:
                first_name, second_name = runtime.plan.targets
                first_after = after_poses[first_name]
                second_after = after_poses[second_name]
                first_changed = np.linalg.norm(
                    np.asarray(swap_event.get("first_xy_after", first_after[:2]))
                    - np.asarray(swap_event.get("first_xy_before", first_after[:2]))
                ) >= 0.02
                second_changed = np.linalg.norm(
                    np.asarray(swap_event.get("second_xy_after", second_after[:2]))
                    - np.asarray(swap_event.get("second_xy_before", second_after[:2]))
                ) >= 0.02
                changed_xy = bool(first_changed and second_changed)

        entity_results = []
        for tracked in tracked_entities:
            before = before_poses[tracked]
            after = after_poses[tracked]
            displacement = float(np.linalg.norm(after - before))
            supported = _entity_has_support_contact(sim_env, tracked)
            penetrating = _entity_has_penetrating_contact(sim_env, tracked)
            support_gap, support_geom = _bottom_support_gap(sim_env, tracked)
            placement_geom = placement_supports.get(tracked)
            speed = _body_speed(sim_env, tracked)
            stable = speed <= 0.25
            geometrically_supported = support_gap <= 0.008
            requires_ground_support = not (
                case_id == "S04"
                and runtime.plan.params.get("interaction_mode") == "articulation"
            ) and tracked not in getattr(sim_env, "fixtures_dict", {}) and case_id not in {"S12"}
            support_matches = _declared_support_matches(
                runtime.plan.params.get("support_surface"),
                support_geom,
                placement_geom,
            )
            entity_passed = bool(
                stable
                and (geometrically_supported or not requires_ground_support)
                and not penetrating
                and support_matches
            )
            entity_results.append(
                {
                    "entity": tracked,
                    "position_before": before.tolist(),
                    "position_after": after.tolist(),
                    "displacement_m": round(displacement, 6),
                    "body_speed": round(speed, 6),
                    "supported": supported,
                    "support_gap_m": round(support_gap, 6),
                    "support_geom": support_geom,
                    "placement_support_geom": placement_geom,
                    "declared_support_matches": support_matches,
                    "penetrating": penetrating,
                    "requires_ground_support": requires_ground_support,
                    "status": "PASS" if entity_passed else "FAIL",
                }
            )

        passed = bool(
            changed_xy
            and all(item["status"] == "PASS" for item in entity_results)
        )
        primary = entity_results[0]
        return {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": case_id,
            "tracked_entity": primary["entity"],
            "tracked_entities": list(tracked_entities),
            "position_before": primary["position_before"],
            "position_after": primary["position_after"],
            "displacement_m": primary["displacement_m"],
            "body_speed": primary["body_speed"],
            "supported": primary["supported"],
            "support_gap_m": primary["support_gap_m"],
            "support_geom": primary["support_geom"],
            "penetrating": primary["penetrating"],
            "observable_xy_change": changed_xy,
            "requires_ground_support": primary["requires_ground_support"],
            "entities": entity_results,
            "events": runtime.events,
            "status": "PASS" if passed else "FAIL",
            "before_image": str(case_dir / "before_settle.png"),
            "after_image": str(case_dir / "after_settle.png"),
        }
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
    os.environ.setdefault("MUJOCO_GL", "egl")
    if args.output is not None:
        OUT = args.output.resolve()
    elif args.all_s04_s10_s11:
        OUT = (
            ROOT
            / "outputs"
            / "review_feedback_current_20260819"
            / "physics_all_s04_s10_s11"
        )
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = _tasks()
    cases = DEFAULT_CASES
    if args.all_s04_s10_s11:
        cases = [
            (suite, task_id, case_id)
            for suite in ("libero_goal", "libero_object", "libero_spatial", "libero_10")
            for task_id in range(10)
            for case_id in ("S04", "S10", "S11")
        ]
    results = []
    for suite, task_id, case_id in cases:
        print(f"[physics] {suite} task{task_id} {case_id}", flush=True)
        results.append(_case(suite, task_id, case_id, tasks[(suite, task_id, case_id)]))
    output = OUT / "physics_results.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(1 if any(item["status"] != "PASS" for item in results) else 0)


if __name__ == "__main__":
    main()
