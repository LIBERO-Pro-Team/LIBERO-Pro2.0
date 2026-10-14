"""Render and measure task-level BDDL tuning against its previous values."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, NamedTuple

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from apply_pending_task_bddl_tuning import apply_params


CHANGE_REPORT = (
    ROOT / "outputs" / "task_level_bddl_tuning_20260823" / "change_report.json"
)
MANIFEST = ROOT / "assets" / "task_manifest.json"
DEFAULT_OUTPUT = (
    ROOT / "outputs" / "task_level_bddl_tuning_20260823" / "render_validation"
)
VISUAL_CASES = {"S15", "S16", "S17", "D07"}


class ValidationSpec(NamedTuple):
    suite: str
    task_id: int
    case_id: str
    bddl: Path
    fields: dict[str, dict[str, list[str]]]


def load_validation_specs(
    case_ids: set[str] | None = None,
    report_path: Path = CHANGE_REPORT,
) -> list[ValidationSpec]:
    """Return only tasks actually changed by the BDDL-only tuning pass."""

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    selected = {case_id.upper() for case_id in case_ids or set()}
    specs = []
    for change in payload["changes"]:
        case_id = str(change["case_id"]).upper()
        if selected and case_id not in selected:
            continue
        specs.append(
            ValidationSpec(
                suite=str(change["suite"]),
                task_id=int(change["task_id"]),
                case_id=case_id,
                bddl=ROOT / str(change["bddl"]),
                fields=dict(change["fields"]),
            )
        )
    return specs


def previous_bddl_text(current_text: str, spec: ValidationSpec) -> str:
    """Restore the exact pre-tuning field values recorded for one task."""

    old_values = {
        field: tuple(str(atom) for atom in change["old"])
        for field, change in spec.fields.items()
    }
    return apply_params(current_text, spec.case_id, old_values)


def evaluate_d19_safety(
    *,
    target_penetrating: bool,
    support_gap_m: float,
    target_speed_m_s: float,
    receiver_distance_m: float,
    unrelated_max_displacement_m: float,
    task_success_after_settle: bool = False,
) -> dict[str, object]:
    """Apply the physical acceptance limits for one D19 task."""

    reasons = []
    if target_penetrating:
        reasons.append("target_penetration")
    if support_gap_m > 0.01:
        reasons.append("unsupported_target")
    if target_speed_m_s > 0.25:
        reasons.append("unstable_target")
    if receiver_distance_m > 0.18:
        reasons.append("receiver_too_far")
    if unrelated_max_displacement_m > 0.01:
        reasons.append("collateral_motion")
    if task_success_after_settle:
        reasons.append("task_already_successful")
    return {"status": "PASS" if not reasons else "FAIL", "reasons": reasons}


def visual_metrics(
    base: np.ndarray, previous: np.ndarray, tuned: np.ndarray
) -> dict[str, float]:
    """Measure old and tuned visibility against one deterministic BASE frame."""

    base_float = np.asarray(base, dtype=np.float64)
    previous_float = np.asarray(previous, dtype=np.float64)
    tuned_float = np.asarray(tuned, dtype=np.float64)

    def mean_delta(first: np.ndarray, second: np.ndarray) -> float:
        return round(float(np.mean(np.abs(first - second))), 4)

    def changed_ratio(first: np.ndarray, second: np.ndarray) -> float:
        per_pixel = np.max(np.abs(first - second), axis=2)
        return round(float(np.mean(per_pixel > 12.0)), 4)

    return {
        "previous_mean_abs_delta": mean_delta(base_float, previous_float),
        "tuned_mean_abs_delta": mean_delta(base_float, tuned_float),
        "tuned_vs_previous_mean_abs_delta": mean_delta(
            previous_float, tuned_float
        ),
        "previous_changed_ratio": changed_ratio(base_float, previous_float),
        "tuned_changed_ratio": changed_ratio(base_float, tuned_float),
    }


def _runtime_api() -> dict[str, Any]:
    import cv2
    import mujoco

    from libero.libero.envs import OffScreenRenderEnv
    from libero.libero.envs.nonphysical_perturbations import (
        _entity_body_ids,
        _entity_exists,
        _entity_pose,
        _goal_path_anchors,
        _set_entity_pose,
        _workspace_bounds,
    )

    return {
        "cv2": cv2,
        "mujoco": mujoco,
        "OffScreenRenderEnv": OffScreenRenderEnv,
        "entity_body_ids": _entity_body_ids,
        "entity_exists": _entity_exists,
        "entity_pose": _entity_pose,
        "goal_path_anchors": _goal_path_anchors,
        "set_entity_pose": _set_entity_pose,
        "workspace_bounds": _workspace_bounds,
    }


def _base_paths() -> dict[tuple[str, int], Path]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        (str(item["suite"]), int(item["base_task_id"])): (
            ROOT / "assets" / str(item["bddl_path"])
        )
        for item in payload["tasks"]
        if str(item["case_id"]) == "BASE"
    }


def _case_directory(output: Path, spec: ValidationSpec) -> Path:
    path = output / f"{spec.suite}_task{spec.task_id}_{spec.case_id}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_frame(frame: np.ndarray, path: Path, api: dict[str, Any]) -> None:
    image = np.asarray(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not api["cv2"].imwrite(str(path), image[::-1, :, ::-1]):
        raise RuntimeError(f"Failed to write rendered frame: {path}")


def _reset_environment(
    bddl: Path, *, seed: int, image_size: int, api: dict[str, Any]
) -> tuple[Any, dict[str, Any]]:
    np.random.seed(seed)
    wrapper = api["OffScreenRenderEnv"](
        bddl_file_name=str(bddl),
        camera_heights=image_size,
        camera_widths=image_size,
    )
    observation = wrapper.reset()
    return wrapper, observation


def _agentview(observation: dict[str, Any]) -> np.ndarray:
    frame = observation.get("agentview_image")
    if not isinstance(frame, np.ndarray) or frame.ndim != 3:
        raise RuntimeError("agentview_image is absent from the rendered observation")
    return frame.copy()


def _forced_dynamic_frame(wrapper: Any) -> tuple[np.ndarray, list[dict[str, Any]]]:
    env = wrapper.env
    runtime = env.perturbation_runtime
    runtime._dynamic_triggered = lambda _env, _step: True
    runtime.before_simulation_step(env, 0)
    env._update_observables(force=True)
    observation = runtime.transform_observation(env._get_observations(), 0)
    return _agentview(observation), list(runtime.events)


def _robot_deep_contacts(env: Any) -> list[dict[str, Any]]:
    model, data = env.sim.model, env.sim.data
    pairs = []
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        if float(contact.dist) >= -0.002:
            continue
        first_body = int(model.geom_bodyid[int(contact.geom1)])
        second_body = int(model.geom_bodyid[int(contact.geom2)])
        first_name = str(model.body_id2name(first_body) or "")
        second_name = str(model.body_id2name(second_body) or "")
        first_robot = first_name.startswith("robot0_")
        second_robot = second_name.startswith("robot0_")
        if first_robot == second_robot:
            continue
        pairs.append(
            {
                "first": first_name,
                "second": second_name,
                "depth_m": round(-float(contact.dist), 6),
            }
        )
    return pairs


def _render_visual_variant(
    bddl: Path,
    spec: ValidationSpec,
    *,
    seed: int,
    image_size: int,
    api: dict[str, Any],
) -> dict[str, Any]:
    wrapper = None
    try:
        wrapper, observation = _reset_environment(
            bddl, seed=seed, image_size=image_size, api=api
        )
        frame = _agentview(observation)
        events = list(wrapper.env.perturbation_runtime.events)
        if spec.case_id == "D07":
            frame, events = _forced_dynamic_frame(wrapper)
        robot = wrapper.env.robots[0]
        joint_indexes = list(robot._ref_joint_pos_indexes)
        qpos = np.asarray(wrapper.env.sim.data.qpos[joint_indexes], dtype=np.float64)
        eef = np.asarray(
            wrapper.env.sim.data.site_xpos[robot.eef_site_id], dtype=np.float64
        )
        return {
            "frame": frame,
            "events": events,
            "robot_joint_qpos": qpos.tolist(),
            "robot_eef_xyz": eef.tolist(),
            "robot_deep_contacts": _robot_deep_contacts(wrapper.env),
        }
    finally:
        if wrapper is not None:
            wrapper.close()


def render_visual_case(
    spec: ValidationSpec,
    *,
    output: Path,
    seed: int,
    image_size: int,
    api: dict[str, Any],
    base_paths: dict[tuple[str, int], Path],
) -> dict[str, Any]:
    case_dir = _case_directory(output, spec)
    source = spec.bddl.read_text(encoding="utf-8")
    previous_source = previous_bddl_text(source, spec)
    base_wrapper = None
    try:
        base_wrapper, base_observation = _reset_environment(
            base_paths[(spec.suite, spec.task_id)],
            seed=seed,
            image_size=image_size,
            api=api,
        )
        base_frame = _agentview(base_observation)
    finally:
        if base_wrapper is not None:
            base_wrapper.close()

    with tempfile.TemporaryDirectory(prefix="libero_previous_") as temp_dir:
        previous_path = Path(temp_dir) / spec.bddl.name
        previous_path.write_text(previous_source, encoding="utf-8")
        previous = _render_visual_variant(
            previous_path,
            spec,
            seed=seed,
            image_size=image_size,
            api=api,
        )
    tuned = _render_visual_variant(
        spec.bddl,
        spec,
        seed=seed,
        image_size=image_size,
        api=api,
    )

    _write_frame(base_frame, case_dir / "base.png", api)
    _write_frame(previous["frame"], case_dir / "previous.png", api)
    _write_frame(tuned["frame"], case_dir / "tuned.png", api)
    metrics = visual_metrics(base_frame, previous["frame"], tuned["frame"])
    required_gain = max(0.05, metrics["previous_mean_abs_delta"] * 0.02)
    visible_gain = (
        metrics["tuned_mean_abs_delta"]
        >= metrics["previous_mean_abs_delta"] + required_gain
    )
    no_new_robot_penetration = not tuned["robot_deep_contacts"]
    status = "PASS" if visible_gain and no_new_robot_penetration else "REVIEW"
    result = {
        "suite": spec.suite,
        "task_id": spec.task_id,
        "case_id": spec.case_id,
        "bddl": str(spec.bddl),
        "fields": spec.fields,
        "visual_metrics": metrics,
        "previous_events": previous["events"],
        "tuned_events": tuned["events"],
        "previous_robot_joint_qpos": previous["robot_joint_qpos"],
        "tuned_robot_joint_qpos": tuned["robot_joint_qpos"],
        "previous_robot_eef_xyz": previous["robot_eef_xyz"],
        "tuned_robot_eef_xyz": tuned["robot_eef_xyz"],
        "tuned_robot_deep_contacts": tuned["robot_deep_contacts"],
        "status": status,
        "base_image": str(case_dir / "base.png"),
        "previous_image": str(case_dir / "previous.png"),
        "tuned_image": str(case_dir / "tuned.png"),
    }
    (case_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def _entity_deep_penetration(
    env: Any, name: str, api: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    body_ids = set(api["entity_body_ids"](env, name))
    model, data = env.sim.model, env.sim.data
    contacts = []
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        if float(contact.dist) >= -0.002:
            continue
        first_body = int(model.geom_bodyid[int(contact.geom1)])
        second_body = int(model.geom_bodyid[int(contact.geom2)])
        if (first_body in body_ids) == (second_body in body_ids):
            continue
        contacts.append(
            {
                "first": str(model.body_id2name(first_body) or ""),
                "second": str(model.body_id2name(second_body) or ""),
                "depth_m": round(-float(contact.dist), 6),
            }
        )
    return bool(contacts), contacts


def _body_speed(env: Any, name: str, api: dict[str, Any]) -> float:
    return max(
        (
            float(np.linalg.norm(env.sim.data.cvel[body_id]))
            for body_id in api["entity_body_ids"](env, name)
        ),
        default=0.0,
    )


def _support_gap(env: Any, name: str, api: dict[str, Any]) -> tuple[float, str | None]:
    mujoco = api["mujoco"]
    model, data = env.sim.model, env.sim.data
    body_id = int(env.obj_body_id[name])
    body_ids = set(api["entity_body_ids"](env, name))
    bottoms = []
    for geom_id, geom_body_id in enumerate(model.geom_bodyid):
        if int(geom_body_id) not in body_ids:
            continue
        if hasattr(model, "geom_group") and int(model.geom_group[geom_id]) != 0:
            continue
        aabb = np.asarray(model.geom_aabb[geom_id], dtype=np.float64)
        rotation = np.asarray(data.geom_xmat[geom_id], dtype=np.float64).reshape(3, 3)
        center = np.asarray(data.geom_xpos[geom_id], dtype=np.float64) + rotation @ aabb[:3]
        vertical_extent = float(np.abs(rotation[2]) @ aabb[3:])
        bottoms.append(float(center[2] - vertical_extent))
    if not bottoms:
        return float("inf"), None
    origin = np.array(
        [data.body_xpos[body_id, 0], data.body_xpos[body_id, 1], min(bottoms) + 0.002]
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
            body_id,
            geom_id,
        )
    )
    if distance < 0.0:
        return float("inf"), None
    support_name = model.geom_id2name(int(geom_id[0])) if geom_id[0] >= 0 else None
    return max(0.0, distance - 0.002), support_name


def _zero_free_joint_velocity(env: Any, name: str) -> None:
    obj = env.objects_dict.get(name)
    joints = list(getattr(obj, "joints", []) or []) if obj is not None else []
    if not joints:
        return
    try:
        joint_id = int(env.sim.model.joint_name2id(joints[-1]))
        dof_address = int(env.sim.model.jnt_dofadr[joint_id])
        dof_count = 6 if int(env.sim.model.jnt_type[joint_id]) == 0 else 1
        env.sim.data.qvel[dof_address : dof_address + dof_count] = 0.0
    except Exception:
        return


def _entity_bottom_extent(env: Any, name: str, api: dict[str, Any]) -> float:
    position, _ = api["entity_pose"](env, name)
    body_ids = set(api["entity_body_ids"](env, name))
    bottoms = []
    for geom_id, geom_body_id in enumerate(env.sim.model.geom_bodyid):
        if int(geom_body_id) not in body_ids:
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
        vertical_extent = float(np.abs(rotation[2]) @ aabb[3:])
        bottoms.append(float(center[2] - vertical_extent))
    if not bottoms:
        return 0.02
    return max(0.005, float(position[2] - min(bottoms)))


def _movable_positions(env: Any, target: str, api: dict[str, Any]) -> dict[str, np.ndarray]:
    return {
        name: api["entity_pose"](env, name)[0]
        for name in sorted(getattr(env, "objects_dict", {}))
        if name != target and api["entity_exists"](env, name)
    }


def _run_d19_variant(
    bddl: Path,
    *,
    seed: int,
    image_size: int,
    api: dict[str, Any],
    apply_event: bool = True,
    hold_target: bool = False,
) -> dict[str, Any]:
    wrapper = None
    try:
        wrapper, observation = _reset_environment(
            bddl, seed=seed, image_size=image_size, api=api
        )
        env = wrapper.env
        runtime = env.perturbation_runtime
        target, initial, receiver_name, receiver = api["goal_path_anchors"](env)
        _, quaternion = api["entity_pose"](env, target)
        preplace = np.asarray(receiver, dtype=np.float64).copy()
        bottom_extent = _entity_bottom_extent(env, target, api)
        preplace[2] = max(
            float(receiver[2]) + bottom_extent + 0.006,
            float(initial[2]) + 0.035,
        )
        api["set_entity_pose"](env, target, preplace, quaternion)
        _zero_free_joint_velocity(env, target)
        env.sim.forward()
        env._update_observables(force=True)
        preplace_frame = _agentview(env._get_observations())
        unrelated_before = _movable_positions(env, target, api)

        if apply_event:
            runtime._dynamic_triggered = lambda _env, _step: True
            runtime.before_simulation_step(env, 0)
        else:
            runtime._dynamic_triggered = lambda _env, _step: False
        env.sim.forward()
        immediate_position, _ = api["entity_pose"](env, target)
        immediate_penetrating, immediate_contacts = _entity_deep_penetration(
            env, target, api
        )
        env._update_observables(force=True)
        entered_frame = _agentview(env._get_observations())

        neutral_action = np.zeros(int(env.action_dim), dtype=np.float64)
        for _ in range(100):
            wrapper.step(neutral_action)
            if hold_target:
                api["set_entity_pose"](env, target, preplace, quaternion)
                _zero_free_joint_velocity(env, target)
        env.sim.forward()
        env._update_observables(force=True)
        settled_frame = _agentview(env._get_observations())
        settled_position, _ = api["entity_pose"](env, target)
        settled_penetrating, settled_contacts = _entity_deep_penetration(
            env, target, api
        )
        support_gap, support_geom = _support_gap(env, target, api)
        target_speed = _body_speed(env, target, api)
        unrelated_displacements = {
            name: float(
                np.linalg.norm(api["entity_pose"](env, name)[0] - position)
            )
            for name, position in unrelated_before.items()
        }
        unrelated_max = max(unrelated_displacements.values(), default=0.0)
        receiver_distance = float(np.linalg.norm(settled_position[:2] - receiver[:2]))
        task_success_after_settle = bool(env._check_success())
        x_min, x_max, y_min, y_max = api["workspace_bounds"](env)
        within_workspace = bool(
            x_min <= settled_position[0] <= x_max
            and y_min <= settled_position[1] <= y_max
        )
        safety = evaluate_d19_safety(
            target_penetrating=immediate_penetrating or settled_penetrating,
            support_gap_m=support_gap,
            target_speed_m_s=target_speed,
            receiver_distance_m=receiver_distance,
            unrelated_max_displacement_m=unrelated_max,
            task_success_after_settle=task_success_after_settle,
        )
        if not within_workspace:
            safety["status"] = "FAIL"
            safety["reasons"].append("outside_workspace")
        return {
            "preplace_frame": preplace_frame,
            "entered_frame": entered_frame,
            "settled_frame": settled_frame,
            "target": target,
            "receiver": receiver_name,
            "receiver_xyz": np.asarray(receiver).tolist(),
            "initial_xyz": np.asarray(initial).tolist(),
            "preplace_xyz": preplace.tolist(),
            "entered_xyz": immediate_position.tolist(),
            "settled_xyz": settled_position.tolist(),
            "applied_displacement_xyz": (immediate_position - preplace).tolist(),
            "receiver_distance_xy_m": round(receiver_distance, 6),
            "support_gap_m": None if not np.isfinite(support_gap) else round(support_gap, 6),
            "support_geom": support_geom,
            "target_speed_m_s": round(target_speed, 6),
            "immediate_penetrating": immediate_penetrating,
            "settled_penetrating": settled_penetrating,
            "penetrating_contacts": immediate_contacts + settled_contacts,
            "unrelated_max_displacement_m": round(unrelated_max, 6),
            "unrelated_displacements_m": {
                name: round(value, 6)
                for name, value in unrelated_displacements.items()
            },
            "unrelated_settled_xyz": {
                name: api["entity_pose"](env, name)[0].tolist()
                for name in unrelated_before
            },
            "within_workspace": within_workspace,
            "task_success_after_settle": task_success_after_settle,
            "events": list(runtime.events),
            "safety": safety,
        }
    finally:
        if wrapper is not None:
            wrapper.close()


def _apply_d19_control_comparison(
    payload: dict[str, Any], control: dict[str, Any]
) -> None:
    control_positions = {
        name: np.asarray(position, dtype=np.float64)
        for name, position in control["unrelated_settled_xyz"].items()
    }
    variant_positions = payload.pop("unrelated_settled_xyz")
    excess = {
        name: float(
            np.linalg.norm(
                np.asarray(position, dtype=np.float64) - control_positions[name]
            )
        )
        for name, position in variant_positions.items()
        if name in control_positions
    }
    payload["unrelated_excess_vs_control_m"] = {
        name: round(value, 6) for name, value in excess.items()
    }
    payload["unrelated_max_excess_vs_control_m"] = round(
        max(excess.values(), default=0.0), 6
    )
    support_gap = payload["support_gap_m"]
    safety = evaluate_d19_safety(
        target_penetrating=(
            payload["immediate_penetrating"] or payload["settled_penetrating"]
        ),
        support_gap_m=float("inf") if support_gap is None else support_gap,
        target_speed_m_s=payload["target_speed_m_s"],
        receiver_distance_m=payload["receiver_distance_xy_m"],
        unrelated_max_displacement_m=payload["unrelated_max_excess_vs_control_m"],
        task_success_after_settle=bool(payload["task_success_after_settle"]),
    )
    if not payload["within_workspace"]:
        safety["status"] = "FAIL"
        safety["reasons"].append("outside_workspace")
    payload["safety"] = safety


def render_d19_case(
    spec: ValidationSpec,
    *,
    output: Path,
    seed: int,
    image_size: int,
    api: dict[str, Any],
) -> dict[str, Any]:
    case_dir = _case_directory(output, spec)
    current_source = spec.bddl.read_text(encoding="utf-8")
    previous_source = previous_bddl_text(current_source, spec)
    control = _run_d19_variant(
        spec.bddl,
        seed=seed,
        image_size=image_size,
        api=api,
        apply_event=False,
        hold_target=True,
    )
    with tempfile.TemporaryDirectory(prefix="libero_previous_") as temp_dir:
        previous_path = Path(temp_dir) / spec.bddl.name
        previous_path.write_text(previous_source, encoding="utf-8")
        previous = _run_d19_variant(
            previous_path, seed=seed, image_size=image_size, api=api
        )
    tuned = _run_d19_variant(
        spec.bddl, seed=seed, image_size=image_size, api=api
    )
    for payload in (previous, tuned):
        _apply_d19_control_comparison(payload, control)
    _write_frame(tuned["preplace_frame"], case_dir / "preplace.png", api)
    _write_frame(previous["entered_frame"], case_dir / "previous_entered.png", api)
    _write_frame(previous["settled_frame"], case_dir / "previous_settled.png", api)
    _write_frame(tuned["entered_frame"], case_dir / "tuned_entered.png", api)
    _write_frame(tuned["settled_frame"], case_dir / "tuned_settled.png", api)
    metrics = visual_metrics(
        tuned["preplace_frame"], previous["entered_frame"], tuned["entered_frame"]
    )
    for payload in (previous, tuned):
        payload.pop("preplace_frame")
        payload.pop("entered_frame")
        payload.pop("settled_frame")
    control.pop("preplace_frame")
    control.pop("entered_frame")
    control.pop("settled_frame")
    control.pop("unrelated_settled_xyz")
    result = {
        "suite": spec.suite,
        "task_id": spec.task_id,
        "case_id": spec.case_id,
        "bddl": str(spec.bddl),
        "fields": spec.fields,
        "visual_metrics": metrics,
        "control": control,
        "previous": previous,
        "tuned": tuned,
        "status": tuned["safety"]["status"],
        "preplace_image": str(case_dir / "preplace.png"),
        "previous_entered_image": str(case_dir / "previous_entered.png"),
        "previous_settled_image": str(case_dir / "previous_settled.png"),
        "tuned_entered_image": str(case_dir / "tuned_entered.png"),
        "tuned_settled_image": str(case_dir / "tuned_settled.png"),
    }
    (case_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def probe_d19_candidates(
    spec: ValidationSpec,
    candidates: list[tuple[float, float, float]],
    *,
    output: Path,
    seed: int,
    image_size: int,
    api: dict[str, Any],
) -> dict[str, Any]:
    case_dir = _case_directory(output, spec)
    source = spec.bddl.read_text(encoding="utf-8")
    control = _run_d19_variant(
        spec.bddl,
        seed=seed,
        image_size=image_size,
        api=api,
        apply_event=False,
        hold_target=True,
    )
    results = []
    with tempfile.TemporaryDirectory(prefix="libero_d19_probe_") as temp_dir:
        for index, (offset_x, offset_y, height) in enumerate(candidates):
            values = {
                "misplace_offset_xy": (str(offset_x), str(offset_y)),
                "misplace_height_m": (str(height),),
            }
            candidate_source = apply_params(source, "D19", values)
            candidate_path = Path(temp_dir) / f"candidate_{index}.bddl"
            candidate_path.write_text(candidate_source, encoding="utf-8")
            try:
                payload = _run_d19_variant(
                    candidate_path,
                    seed=seed,
                    image_size=image_size,
                    api=api,
                )
            except Exception as exc:
                payload = {
                    "candidate_index": index,
                    "candidate_values": {
                        "misplace_offset_xy": [offset_x, offset_y],
                        "misplace_height_m": height,
                    },
                    "status": "ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                    "safety": {"status": "ERROR", "reasons": ["candidate_error"]},
                }
                results.append(payload)
                print(
                    json.dumps(
                        {
                            "candidate": payload["candidate_values"],
                            "safety": payload["safety"],
                            "error": payload["error"],
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                continue
            _apply_d19_control_comparison(payload, control)
            entered_path = case_dir / f"candidate_{index}_entered.png"
            settled_path = case_dir / f"candidate_{index}_settled.png"
            _write_frame(payload.pop("entered_frame"), entered_path, api)
            _write_frame(payload.pop("settled_frame"), settled_path, api)
            payload.pop("preplace_frame")
            payload["candidate_index"] = index
            payload["candidate_values"] = {
                "misplace_offset_xy": [offset_x, offset_y],
                "misplace_height_m": height,
            }
            payload["entered_image"] = str(entered_path)
            payload["settled_image"] = str(settled_path)
            results.append(payload)
            print(
                json.dumps(
                    {
                        "candidate": payload["candidate_values"],
                        "safety": payload["safety"],
                        "receiver_distance_xy_m": payload[
                            "receiver_distance_xy_m"
                        ],
                        "target_speed_m_s": payload["target_speed_m_s"],
                        "support_gap_m": payload["support_gap_m"],
                        "unrelated_max_excess_vs_control_m": payload[
                            "unrelated_max_excess_vs_control_m"
                        ],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
    control.pop("preplace_frame")
    control.pop("entered_frame")
    control.pop("settled_frame")
    control.pop("unrelated_settled_xyz")
    passing = [item for item in results if item["safety"]["status"] == "PASS"]
    result = {
        "suite": spec.suite,
        "task_id": spec.task_id,
        "case_id": spec.case_id,
        "bddl": str(spec.bddl),
        "control": control,
        "candidates": results,
        "passing_candidate_indexes": [
            item["candidate_index"] for item in passing
        ],
        "status": "PASS" if passing else "FAIL",
    }
    (case_dir / "probe_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--suite", action="append", default=[])
    parser.add_argument("--task-id", action="append", type=int, default=[])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=142)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument(
        "--d19-probe",
        action="store_true",
        help="Probe temporary D19 values without changing the task BDDL.",
    )
    parser.add_argument(
        "--d19-candidate",
        action="append",
        nargs=3,
        type=float,
        metavar=("OFFSET_X", "OFFSET_Y", "HEIGHT"),
        default=[],
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    os.environ.setdefault("MUJOCO_GL", "wgl")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    case_ids = {case_id.upper() for case_id in args.case_id}
    specs = load_validation_specs(case_ids=case_ids or None)
    if args.suite:
        suites = set(args.suite)
        specs = [spec for spec in specs if spec.suite in suites]
    if args.task_id:
        task_ids = set(args.task_id)
        specs = [spec for spec in specs if spec.task_id in task_ids]
    unsupported = sorted(
        {spec.case_id for spec in specs} - VISUAL_CASES - {"D19"}
    )
    if unsupported:
        raise SystemExit(
            "Runtime evidence validation is not implemented yet for: "
            + ", ".join(unsupported)
        )
    api = _runtime_api()
    base_paths = _base_paths()
    if args.d19_probe:
        if len(specs) != 1 or specs[0].case_id != "D19":
            raise SystemExit("--d19-probe requires exactly one selected D19 task")
        if not args.d19_candidate:
            raise SystemExit("--d19-probe requires at least one --d19-candidate")
        result = probe_d19_candidates(
            specs[0],
            [tuple(values) for values in args.d19_candidate],
            output=output,
            seed=args.seed,
            image_size=args.image_size,
            api=api,
        )
        report = output / "probe_results.json"
        report.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        raise SystemExit(0 if result["status"] == "PASS" else 1)
    results = []
    for spec in specs:
        print(f"[render] {spec.suite} task{spec.task_id} {spec.case_id}", flush=True)
        try:
            if spec.case_id == "D19":
                result = render_d19_case(
                    spec,
                    output=output,
                    seed=args.seed,
                    image_size=args.image_size,
                    api=api,
                )
            else:
                result = render_visual_case(
                    spec,
                    output=output,
                    seed=args.seed,
                    image_size=args.image_size,
                    api=api,
                    base_paths=base_paths,
                )
        except Exception as exc:
            result = {
                "suite": spec.suite,
                "task_id": spec.task_id,
                "case_id": spec.case_id,
                "bddl": str(spec.bddl),
                "status": "ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            }
        results.append(result)
        summary = {
            "suite": result["suite"],
            "task_id": result["task_id"],
            "case_id": result["case_id"],
            "status": result["status"],
        }
        if "visual_metrics" in result:
            summary["visual_metrics"] = result["visual_metrics"]
        if result.get("case_id") == "D19" and "tuned" in result:
            summary["safety"] = result["tuned"]["safety"]
        if "error" in result:
            summary["error"] = result["error"]
        print(json.dumps(summary, ensure_ascii=False), flush=True)
    report = output / "render_results.json"
    report.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    raise SystemExit(
        1 if any(result["status"] not in {"PASS"} for result in results) else 0
    )


if __name__ == "__main__":
    main()
