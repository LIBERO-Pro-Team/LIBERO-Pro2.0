from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


ALL_CASE_IDS = tuple(
    [f"S{index:02d}" for index in range(1, 22)]
    + [f"D{index:02d}" for index in range(1, 20)]
    + ["D21"]
)

CASE_MECHANISMS = {
    "S01": ("pose",),
    "S02": ("pose",),
    "S03": ("asset", "pose"),
    "S04": ("pose",),
    "S05": ("asset",),
    "S06": ("asset_replacement",),
    "S07": ("geometry",),
    "S08": ("geometry",),
    "S09": ("geometry",),
    "S10": ("asset",),
    "S11": ("asset",),
    "S12": ("asset", "occlusion"),
    "S13": ("appearance",),
    "S14": ("appearance", "lighting"),
    "S15": ("camera",),
    "S16": ("camera_intrinsics", "observation"),
    "S17": ("robot_state",),
    "S18": ("calibration",),
    "S19": ("observation",),
    "S20": ("action_timing", "observation_timing"),
    "S21": ("language",),
    "D01": ("dynamic_pose",),
    "D02": ("dynamic_pose",),
    "D03": ("asset", "dynamic_pose"),
    "D04": ("asset", "dynamic_pose", "occlusion"),
    "D05": ("asset", "dynamic_pose"),
    "D06": ("dynamic_pose",),
    "D07": ("dynamic_camera",),
    "D08": ("observation",),
    "D09": ("lighting", "observation"),
    "D10": ("observation_timing",),
    "D11": ("observation_timing",),
    "D12": ("observation_timing",),
    "D13": ("action_timing",),
    "D14": ("action_timing",),
    "D15": ("action_timing",),
    "D16": ("action_takeover",),
    "D17": ("state_event",),
    "D18": ("state_event",),
    "D19": ("state_event",),
    "D21": ("language",),
}

CASE_ASSETS = {
    "S03": ("generated/support_riser",),
    "S05": ("generated/barrier_panel",),
    "S10": ("ycb/YcbFoamBrick",),
    "S12": ("generated/occlusion_screen",),
    "D03": ("ycb/YcbFoamBrick",),
    "D04": ("generated/occlusion_screen",),
    "D05": ("generated/barrier_panel",),
}

REPLACEMENT_ASSETS = {
    "white_yellow_mug": "prl/plastic_glass",
    "porcelain_mug": "prl/plastic_glass",
    "wine_bottle": "prl/fuze_bottle",
    "alphabet_soup": "ycb/YcbTomatoSoupCan",
    "akita_black_bowl": "prl/plastic_bowl",
}


class PerturbationConfigurationError(ValueError):
    pass


class PerturbationValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class AssetSpec:
    asset_id: str
    xml_path: Path
    staged: bool
    replacement: bool = False
    scale: float = 1.0


@dataclass(frozen=True)
class ExecutionPlan:
    case_id: str
    schedule: str
    operator: str
    variant: str
    targets: tuple[str, ...]
    references: tuple[str, ...]
    mechanisms: tuple[str, ...]
    assets: tuple[AssetSpec, ...]
    trigger: str = "none"
    params: dict[str, Any] = field(default_factory=dict)
    constraints: tuple[str, ...] = ()


def describe_execution_plan(
    plan: ExecutionPlan, seed: int, event_duration_steps: int
) -> dict[str, Any]:
    """Return the path-independent plan identity persisted by remote evaluators."""

    return {
        "version": "libero_nonphysical_plan_v2",
        "case_id": plan.case_id,
        "schedule": plan.schedule,
        "operator": plan.operator,
        "variant": plan.variant,
        "trigger": plan.trigger,
        "targets": list(plan.targets),
        "references": list(plan.references),
        "mechanisms": list(plan.mechanisms),
        "assets": [
            {
                "asset_id": asset.asset_id,
                "staged": asset.staged,
                "replacement": asset.replacement,
                "scale": asset.scale,
            }
            for asset in plan.assets
        ],
        "params": dict(plan.params),
        "constraints": list(plan.constraints),
        "seed": int(seed),
        "event_duration_steps": int(event_duration_steps),
    }


@dataclass(frozen=True)
class AssetInjectionResult:
    injected_names: tuple[str, ...] = ()
    replaced_names: tuple[str, ...] = ()


def _name_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return (str(value),)


def _flatten_case(raw_case: Any) -> tuple[str, dict[str, Any]]:
    if not isinstance(raw_case, list) or not raw_case:
        raise PerturbationConfigurationError(f"Invalid perturbation entry: {raw_case!r}")
    case_id = str(raw_case[0]).upper()
    fields: dict[str, Any] = {}
    for item in raw_case[1:]:
        if not isinstance(item, dict):
            raise PerturbationConfigurationError(
                f"Invalid field in perturbation {case_id}: {item!r}"
            )
        fields.update(item)
    return case_id, fields


def _asset_index(asset_root: Path) -> dict[str, dict[str, Any]]:
    catalog_path = asset_root / "asset_catalog.json"
    if not catalog_path.is_file():
        raise PerturbationConfigurationError(f"Asset catalog not found: {catalog_path}")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    index: dict[str, dict[str, Any]] = {}
    for item in catalog.get("assets", []):
        asset_id = str(item["id"])
        index[asset_id] = item
        # BDDL scanners normalize atoms to lowercase, while catalog IDs may
        # intentionally preserve YCB/PRL capitalization.
        index.setdefault(asset_id.casefold(), item)
    return index


def _resolve_asset(
    asset_id: str,
    asset_root: Path,
    index: dict[str, dict[str, Any]],
    *,
    staged: bool,
    replacement: bool = False,
    scale: float = 1.0,
) -> AssetSpec:
    item = index.get(asset_id) or index.get(str(asset_id).casefold())
    if item is None:
        raise PerturbationConfigurationError(
            f"Perturbation asset {asset_id!r} is absent from {asset_root / 'asset_catalog.json'}"
        )
    canonical_id = str(item["id"])
    path = (asset_root / item["path"]).resolve()
    if not path.is_file():
        raise PerturbationConfigurationError(
            f"Perturbation asset {asset_id!r} is missing its MJCF file: {path}"
        )
    if scale <= 0:
        raise PerturbationConfigurationError(f"Asset scale must be positive; got {scale}")
    return AssetSpec(canonical_id, path, staged, replacement, float(scale))


def _case_entries(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for raw_case in config.get("perturbations", []):
        case_id, fields = _flatten_case(raw_case)
        if case_id in entries:
            raise PerturbationConfigurationError(f"Duplicate perturbation case {case_id}")
        entries[case_id] = fields
    return entries


def build_execution_plan(
    config: dict[str, Any], asset_root: str | Path
) -> ExecutionPlan:
    """Resolve one BDDL config to the complete behavior the environment executes."""
    asset_root = Path(asset_root).resolve()
    raw_active = config.get("active_cases", config.get("case_id", "BASE"))
    active = _name_tuple(raw_active)
    if not active or active == ("none",):
        active = ("BASE",)
    active = tuple(case_id.upper() for case_id in active)
    if len(active) != 1:
        raise PerturbationConfigurationError(
            f"Exactly one perturbation case must be active; got {active}"
        )
    case_id = active[0]
    declared_case = str(config.get("case_id", case_id)).upper()
    if declared_case != case_id:
        raise PerturbationConfigurationError(
            f"case_id {declared_case} disagrees with active_cases {case_id}"
        )
    if case_id == "BASE":
        return ExecutionPlan(
            case_id="BASE",
            schedule="base",
            operator="none",
            variant="identity",
            targets=(),
            references=(),
            mechanisms=("base",),
            assets=(),
            trigger="none",
        )
    if case_id not in CASE_MECHANISMS:
        raise PerturbationConfigurationError(f"Unsupported perturbation case {case_id}")

    entries = _case_entries(config)
    missing = set(ALL_CASE_IDS) - set(entries)
    if missing:
        raise PerturbationConfigurationError(
            f"Schema is missing perturbation definitions: {sorted(missing)}"
        )
    fields = entries[case_id]
    operator = str(fields.get("operator", ""))
    variant = str(fields.get("variant", ""))
    if not operator or not variant:
        raise PerturbationConfigurationError(
            f"Perturbation {case_id} needs operator and variant fields"
        )

    index = _asset_index(asset_root)
    staged = case_id.startswith("D")
    params = fields.get("params", {})
    if not isinstance(params, dict):
        params = {}
    assets = [
        _resolve_asset(asset_id, asset_root, index, staged=staged)
        for asset_id in CASE_ASSETS.get(case_id, ())
    ]
    if case_id in {"S06", "S11"}:
        source_suite = str(config.get("source_suite", ""))
        suite_default = {
            "libero_10": ("prl/plastic_glass", 0.65),
            "libero_goal": ("prl/fuze_bottle", 0.72),
            "libero_object": ("ycb/YcbTomatoSoupCan", 0.72),
            "libero_spatial": ("prl/plastic_bowl", 0.30),
        }.get(source_suite)
        configured_asset = params.get("asset_id")
        configured_scale = params.get("asset_scale")
        if configured_asset:
            try:
                configured_scale = float(configured_scale)
            except (TypeError, ValueError):
                configured_scale = 1.0
            suite_default = (str(configured_asset), configured_scale)
        if not suite_default:
            raise PerturbationConfigurationError(
                f"No semantics-preserving {case_id} asset for suite {source_suite!r}"
            )
        assets.append(
            _resolve_asset(
                suite_default[0],
                asset_root,
                index,
                staged=False,
                replacement=case_id == "S06",
                scale=suite_default[1],
            )
        )

    constraints = _name_tuple(fields.get("constraints"))
    return ExecutionPlan(
        case_id=case_id,
        schedule="static" if case_id.startswith("S") else "dynamic",
        operator=operator,
        variant=variant,
        targets=_name_tuple(fields.get("targets")),
        references=_name_tuple(fields.get("references")),
        mechanisms=CASE_MECHANISMS[case_id],
        assets=tuple(assets),
        trigger=str(fields.get("trigger", "task_phase" if staged else "reset")),
        params=params,
        constraints=constraints,
    )


def default_asset_root() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "perturbation_assets"


def _static_asset_reference_name(plan: ExecutionPlan) -> str:
    if plan.case_id in {"S03", "S12"}:
        return plan.targets[0]
    if plan.case_id == "S10":
        return plan.references[-1] if plan.references else plan.targets[-1]
    if plan.case_id == "S11":
        return plan.references[0] if plan.references else plan.targets[0]
    return plan.targets[0]


def inject_plan_assets(
    objects_dict: dict[str, Any],
    plan: ExecutionPlan,
    object_factory: Any,
) -> AssetInjectionResult:
    """Instantiate all plan assets before ``ManipulationTask`` is compiled."""
    injected: list[str] = []
    replaced: list[str] = []
    for index, asset in enumerate(plan.assets):
        if asset.replacement:
            if len(plan.targets) != 1:
                raise PerturbationConfigurationError(
                    f"Replacement case {plan.case_id} must have exactly one target"
                )
            target = plan.targets[0]
            if target not in objects_dict:
                raise PerturbationConfigurationError(
                    f"Replacement target {target!r} is not a movable scene object"
                )
            original = objects_dict[target]
            replacement = object_factory(
                str(asset.xml_path), name=target, joints="default"
            )
            replacement.category_name = getattr(original, "category_name", target)
            # Rotation metadata is asset-frame-specific. Inheriting it from the
            # source object can turn an otherwise upright replacement on its side.
            replacement.rotation = (0.0, 0.0)
            replacement.rotation_axis = "z"
            replacement.object_properties = getattr(
                original, "object_properties", {"vis_site_names": {}}
            )
            _scale_mujoco_object(replacement, asset.scale)
            objects_dict[target] = replacement
            replaced.append(target)
            continue

        name = f"perturbation_{plan.case_id.lower()}_{index}"
        if name in objects_dict:
            existing = objects_dict[name]
            if getattr(existing, "category_name", None) != "perturbation_asset":
                raise PerturbationConfigurationError(
                    f"Injected asset name collides with an existing object: {name}"
                )
            del objects_dict[name]
        # Structural assets are welded to the world. Dynamic cases move their
        # body pose at runtime; no free joint is needed and gravity cannot topple them.
        obj = object_factory(str(asset.xml_path), name=name, joints=None)
        obj.category_name = "perturbation_asset"
        obj.rotation = (0.0, 0.0)
        obj.rotation_axis = "z"
        obj.object_properties = {"vis_site_names": {}}
        _scale_mujoco_object(obj, asset.scale)
        root = obj.get_obj() if hasattr(obj, "get_obj") else None
        if root is not None:
            root.set("pos", "0 0 -5")
            if plan.case_id in {"S12", "D04"}:
                for geom in root.findall(".//geom"):
                    if geom.get("group", "0") == "0":
                        geom.set("contype", "0")
                        geom.set("conaffinity", "0")
        objects_dict[name] = obj
        injected.append(name)
    return AssetInjectionResult(tuple(injected), tuple(replaced))


def _scale_mujoco_object(obj: Any, factor: float) -> None:
    if abs(float(factor) - 1.0) < 1e-9:
        return
    if hasattr(obj, "asset"):
        for mesh in obj.asset.findall("mesh"):
            mesh.set("scale", _scale_xml_values(mesh.get("scale", "1 1 1"), factor))
    if hasattr(obj, "worldbody"):
        for element in obj.worldbody.findall(".//*[@pos]"):
            element.set("pos", _scale_xml_values(element.get("pos"), factor))
        for geom in obj.worldbody.findall(".//geom"):
            if geom.get("size"):
                geom.set("size", _scale_xml_values(geom.get("size"), factor))


def _scale_xml_values(raw: str | None, factor: float) -> str | None:
    if not raw:
        return raw
    return " ".join(str(float(value) * factor) for value in raw.split())


def _scale_xml_vector(raw: str | None, factors: tuple[float, float, float]) -> str | None:
    if not raw:
        return raw
    values = [float(value) for value in raw.split()]
    if len(values) == 1:
        applied = (float(np.prod(factors)) ** (1.0 / 3.0),)
    else:
        applied = factors[: len(values)]
    return " ".join(str(value * factor) for value, factor in zip(values, applied))


def apply_precompile_geometry(
    objects_dict: dict[str, Any],
    fixtures_dict: dict[str, Any],
    plan: ExecutionPlan,
) -> tuple[str, ...]:
    """Apply geometry cases to MJCF before MuJoCo compiles the scene."""
    if plan.case_id not in {"S07", "S08", "S09"}:
        return ()
    entities = {**fixtures_dict, **objects_dict}
    changed: list[str] = []
    if plan.case_id == "S07":
        transforms = {name: (1.0, 0.64, 1.20) for name in plan.targets}
    elif plan.case_id == "S08":
        transforms = {name: (1.35, 0.72, 1.0) for name in plan.targets}
    else:
        transforms = {
            name: ((1.12, 1.12, 1.12) if index == 0 else (0.90, 0.90, 0.90))
            for index, name in enumerate(plan.targets)
        }
    receiver_name = plan.targets[-1] if plan.case_id == "S09" else None
    for name, factors in transforms.items():
        obj = entities.get(name)
        if obj is None or not hasattr(obj, "worldbody"):
            continue
        for element in obj.worldbody.findall(".//*[@pos]"):
            element.set("pos", _scale_xml_vector(element.get("pos"), factors))
        for geom in obj.worldbody.findall(".//geom"):
            if geom.get("size"):
                geom.set("size", _scale_xml_vector(geom.get("size"), factors))
                changed.append(name)
        if hasattr(obj, "asset"):
            for mesh in obj.asset.findall("mesh"):
                old_scale = mesh.get("scale", "1 1 1")
                mesh.set("scale", _scale_xml_vector(old_scale, factors))
                changed.append(name)
        if name == receiver_name:
            for site in obj.worldbody.findall(".//site"):
                if site.get("size"):
                    site.set("size", _scale_xml_vector(site.get("size"), factors))
    if not changed:
        raise PerturbationConfigurationError(
            f"{plan.case_id} could not find scalable collision or mesh geometry in {plan.targets}"
        )
    return tuple(sorted(set(changed)))


def _entity_body_id(env: Any, name: str) -> int:
    """Resolve movable objects, fixtures, and the arena's canonical table."""

    body_ids = getattr(env, "obj_body_id", {})
    if name in body_ids:
        return int(body_ids[name])
    # ``main_table`` is declared by BDDL but robosuite names its arena body
    # ``table`` and deliberately omits it from obj_body_id.
    candidates = ("table",) if name == "main_table" else (name,)
    model = getattr(getattr(env, "sim", None), "model", None)
    for candidate in candidates:
        try:
            return int(model.body_name2id(candidate))
        except Exception:
            continue
    raise PerturbationValidationError(f"Scene entity {name!r} does not exist")


def _entity_exists(env: Any, name: str) -> bool:
    try:
        _entity_body_id(env, name)
    except PerturbationValidationError:
        return False
    return True


def _scene_entity_names(env: Any) -> tuple[str, ...]:
    names = list(getattr(env, "obj_body_id", {}).keys())
    if _entity_exists(env, "main_table") and "main_table" not in names:
        names.append("main_table")
    return tuple(names)


def _entity_body_ids(env: Any, name: str) -> tuple[int, ...]:
    """Return a body and all descendants, covering articulated fixtures."""

    root = _entity_body_id(env, name)
    model = env.sim.model
    ids = [root]
    changed = True
    while changed:
        changed = False
        for body_id in range(int(model.nbody)):
            if body_id in ids:
                continue
            parent = int(model.body_parentid[body_id])
            if parent in ids:
                ids.append(body_id)
                changed = True
    return tuple(ids)


def _entity_pose(env: Any, name: str) -> tuple[np.ndarray, np.ndarray]:
    body_id = _entity_body_id(env, name)
    return (
        np.asarray(env.sim.data.body_xpos[body_id], dtype=np.float64).copy(),
        np.asarray(env.sim.data.body_xquat[body_id], dtype=np.float64).copy(),
    )


def _set_entity_pose(
    env: Any, name: str, position: np.ndarray, quaternion: np.ndarray | None = None
) -> None:
    body_id = _entity_body_id(env, name)
    if quaternion is None:
        quaternion = np.asarray(env.sim.data.body_xquat[body_id], dtype=np.float64)
    obj = env.objects_dict.get(name)
    joints = list(getattr(obj, "joints", []) or []) if obj is not None else []
    if joints:
        env.sim.data.set_joint_qpos(
            joints[-1], np.concatenate([np.asarray(position), np.asarray(quaternion)])
        )
    else:
        env.sim.model.body_pos[body_id] = np.asarray(position)
        env.sim.model.body_quat[body_id] = np.asarray(quaternion)
    env.sim.forward()


def _yaw_quaternion(yaw: float) -> np.ndarray:
    return np.array([math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)])


def _quaternion_multiply(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    lw, lx, ly, lz = np.asarray(left, dtype=np.float64)
    rw, rx, ry, rz = np.asarray(right, dtype=np.float64)
    result = np.array(
        [
            lw * rw - lx * rx - ly * ry - lz * rz,
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
        ]
    )
    return result / np.linalg.norm(result)


def _workspace_bounds(env: Any) -> tuple[float, float, float, float]:
    center = np.asarray(getattr(env, "workspace_offset", [0.0, 0.0, 0.9]))
    return (
        float(center[0] - 0.42),
        float(center[0] + 0.42),
        float(center[1] - 0.50),
        float(center[1] + 0.50),
    )


def _candidate_is_clear(
    env: Any,
    moving_name: str,
    candidate_xy: np.ndarray,
    minimum_gap: float,
    ignored: tuple[str, ...] = (),
) -> bool:
    x_min, x_max, y_min, y_max = _workspace_bounds(env)
    if not (x_min <= candidate_xy[0] <= x_max and y_min <= candidate_xy[1] <= y_max):
        return False
    for name in _scene_entity_names(env):
        if name == moving_name or name in ignored:
            continue
        try:
            other, _ = _entity_pose(env, name)
        except Exception:
            continue
        if np.linalg.norm(candidate_xy - other[:2]) < minimum_gap:
            return False
    return True


def _point_is_in_camera_view(
    env: Any,
    point: np.ndarray,
    camera_name: str = "agentview",
    margin: float = 0.8,
) -> bool:
    """Check a world point against a MuJoCo camera's inner view frustum."""

    try:
        camera_id = int(env.sim.model.camera_name2id(camera_name))
        camera_position = np.asarray(
            env.sim.data.cam_xpos[camera_id], dtype=np.float64
        )
        camera_rotation = np.asarray(
            env.sim.data.cam_xmat[camera_id], dtype=np.float64
        ).reshape(3, 3)
        vertical_fov = math.radians(float(env.sim.model.cam_fovy[camera_id]))
    except Exception as exc:
        raise PerturbationValidationError(
            f"Camera {camera_name!r} is required for visible asset placement"
        ) from exc

    camera_point = camera_rotation.T @ (np.asarray(point) - camera_position)
    depth = -float(camera_point[2])
    if depth <= 0.0:
        return False
    half_extent = depth * math.tan(vertical_fov / 2.0) * float(margin)
    return bool(
        abs(float(camera_point[0])) <= half_extent
        and abs(float(camera_point[1])) <= half_extent
    )


def _entity_has_penetrating_contact(
    env: Any, name: str, tolerance: float = -1e-4
) -> bool:
    body_ids = set(_entity_body_ids(env, name))
    model = env.sim.model
    data = env.sim.data
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        first_body = int(model.geom_bodyid[int(contact.geom1)])
        second_body = int(model.geom_bodyid[int(contact.geom2)])
        if first_body not in body_ids and second_body not in body_ids:
            continue
        if float(contact.dist) < float(tolerance):
            return True
    return False


def _visible_clutter_pose(
    env: Any,
    moving_name: str,
    reference_name: str,
    *,
    minimum_gap: float = 0.10,
) -> np.ndarray:
    reference, _ = _entity_pose(env, reference_name)
    original_position, original_quaternion = _entity_pose(env, moving_name)
    clutter_quaternion = _yaw_quaternion(0.0)
    base_angle = math.atan2(-0.12, 0.16)
    candidates: list[np.ndarray] = []
    for radius in (0.14, 0.18, 0.22, 0.26, 0.30):
        for angle_offset in np.linspace(0.0, 2.0 * math.pi, 16, endpoint=False):
            angle = base_angle + float(angle_offset)
            candidate = reference.copy()
            candidate[:2] += radius * np.array([math.cos(angle), math.sin(angle)])
            candidate[2] += 0.03
            candidates.append(candidate)

    for candidate in candidates:
        if not _candidate_is_clear(
            env,
            moving_name,
            candidate[:2],
            minimum_gap,
            ignored=("main_table", "floor"),
        ):
            continue
        if not _point_is_in_camera_view(env, candidate):
            continue
        _set_entity_pose(env, moving_name, candidate, clutter_quaternion)
        if not _entity_has_penetrating_contact(env, moving_name):
            return candidate
    _set_entity_pose(env, moving_name, original_position, original_quaternion)
    raise PerturbationValidationError(
        f"No collision-clear agentview position for {moving_name!r} near {reference_name!r}"
    )


def _safe_offset_pose(
    env: Any,
    name: str,
    requested: tuple[float, float],
    *,
    minimum_gap: float = 0.08,
    ignored: tuple[str, ...] = (),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    before, quat = _entity_pose(env, name)
    requested_array = np.asarray(requested, dtype=np.float64)
    primary_candidates = (
        requested_array,
        np.array([-requested_array[0], requested_array[1]]),
        np.array([requested_array[0], -requested_array[1]]),
        -requested_array,
        np.array([requested_array[1], requested_array[0]]),
        np.array([-requested_array[1], -requested_array[0]]),
    )
    candidates = list(primary_candidates)
    requested_distance = float(np.linalg.norm(requested_array))
    if requested_distance > 1e-9:
        base_angle = math.atan2(requested_array[1], requested_array[0])
        for multiplier in (1.5, 2.0, 2.5, 3.0, 3.5):
            distance = requested_distance * multiplier
            for angle_offset in np.linspace(0.0, 2.0 * math.pi, 16, endpoint=False):
                angle = base_angle + float(angle_offset)
                delta = distance * np.array([math.cos(angle), math.sin(angle)])
                if not any(np.allclose(delta, existing) for existing in candidates):
                    candidates.append(delta)
    for delta in candidates:
        candidate = before.copy()
        candidate[:2] += delta
        if _candidate_is_clear(env, name, candidate[:2], minimum_gap, ignored):
            _set_entity_pose(env, name, candidate, quat)
            return before, candidate, delta
    raise PerturbationValidationError(
        f"No collision-clear workspace position for {name!r} near {before[:2].tolist()}"
    )


def _dynamic_pose_requested_delta(
    case_id: str, target: str, params: dict[str, Any] | None = None
) -> tuple[float, float]:
    configured = (params or {}).get("offset_xy")
    if configured is not None:
        delta = np.asarray(configured, dtype=np.float64)
        if delta.shape != (2,) or not np.all(np.isfinite(delta)):
            raise PerturbationConfigurationError(
                f"Perturbation {case_id} offset_xy must contain two finite values"
            )
        return float(delta[0]), float(delta[1])
    if case_id == "D02" and target == "wine_rack_1":
        # Move across the rack's narrow functional axis. The previous diagonal
        # offset left the old placement point inside the moved top_region.
        return (0.0, 0.09)
    return {
        "D01": (0.075, 0.035),
        "D02": (-0.06, 0.045),
        "D06": (0.07, -0.055),
        "D18": (-0.055, 0.035),
        "D19": (0.045, -0.04),
    }[case_id]


def _injected_name(plan: ExecutionPlan, index: int = 0) -> str:
    return f"perturbation_{plan.case_id.lower()}_{index}"


def _camera_occluder_pose(
    env: Any, target_name: str, camera_name: str = "agentview", fraction: float = 0.62
) -> tuple[np.ndarray, np.ndarray]:
    target, _ = _entity_pose(env, target_name)
    try:
        camera_id = int(env.sim.model.camera_name2id(camera_name))
        camera = np.asarray(env.sim.data.cam_xpos[camera_id], dtype=np.float64)
    except Exception as exc:
        raise PerturbationValidationError(
            f"Camera {camera_name!r} is required for view occlusion"
        ) from exc
    center = camera + float(fraction) * (target - camera)
    root_position = center.copy()
    root_position[2] -= 0.08
    normal_xy = camera[:2] - center[:2]
    yaw = math.atan2(-normal_xy[0], normal_xy[1])
    return root_position, _yaw_quaternion(yaw)


def _functional_anchor(env: Any, entity_name: str) -> tuple[np.ndarray, str]:
    """Return the task-relevant site on an entity, falling back to its body."""
    sites = getattr(env, "object_sites_dict", {})
    goal_states = getattr(env, "parsed_problem", {}).get("goal_state", [])
    for state in goal_states:
        if len(state) < 3:
            continue
        site_name = state[2]
        site = sites.get(site_name)
        region = getattr(env, "parsed_problem", {}).get("regions", {}).get(site_name, {})
        site_parent = getattr(site, "parent_name", None) if site is not None else None
        region_target = region.get("target") if isinstance(region, dict) else None
        if site is not None and (site_parent == entity_name or region_target == entity_name):
            try:
                return (
                    np.asarray(env.sim.data.get_site_xpos(site_name), dtype=np.float64).copy(),
                    str(site_name),
                )
            except Exception:
                break
    for site_name, site in sites.items():
        region = getattr(env, "parsed_problem", {}).get("regions", {}).get(site_name, {})
        site_parent = getattr(site, "parent_name", None)
        region_target = region.get("target") if isinstance(region, dict) else None
        if site_parent != entity_name and region_target != entity_name:
            continue
        try:
            return (
                np.asarray(env.sim.data.get_site_xpos(site_name), dtype=np.float64).copy(),
                str(site_name),
            )
        except Exception:
            continue
    position, _ = _entity_pose(env, entity_name)
    return position, entity_name


def _goal_path_anchors(env: Any) -> tuple[str, np.ndarray, str, np.ndarray]:
    sites = getattr(env, "object_sites_dict", {})
    goal_states = getattr(env, "parsed_problem", {}).get("goal_state", [])
    for state in goal_states:
        if len(state) < 3 or not _entity_exists(env, state[1]):
            continue
        site = sites.get(state[2])
        receiver_name = getattr(site, "parent_name", None) if site is not None else None
        region = getattr(env, "parsed_problem", {}).get("regions", {}).get(state[2], {})
        if receiver_name is None and isinstance(region, dict):
            receiver_name = region.get("target")
        if receiver_name is None and _entity_exists(env, state[2]):
            receiver_name = state[2]
        if receiver_name is None or not _entity_exists(env, receiver_name):
            continue
        target, _ = _entity_pose(env, state[1])
        receiver, anchor_name = _functional_anchor(env, receiver_name)
        return state[1], target, anchor_name, receiver
    raise PerturbationValidationError(
        "Cannot resolve an object-to-receiver path from the task goal"
    )


def _goal_interaction_targets(env: Any) -> tuple[str, ...]:
    """Resolve entities the robot must approach to make task progress."""
    targets: list[str] = []
    sites = getattr(env, "object_sites_dict", {})
    for state in getattr(env, "parsed_problem", {}).get("goal_state", []):
        if len(state) < 2:
            continue
        candidate = str(state[1])
        if not _entity_exists(env, candidate):
            site = sites.get(candidate)
            candidate = str(getattr(site, "parent_name", candidate))
        if _entity_exists(env, candidate) and candidate not in targets:
            targets.append(candidate)
    return tuple(targets)


def _goal_articulation_targets(env: Any) -> tuple[tuple[str, list[Any]], ...]:
    """Return articulation goal predicates resolved to their fixture bodies."""
    targets: list[tuple[str, list[Any]]] = []
    sites = getattr(env, "object_sites_dict", {})
    for state in getattr(env, "parsed_problem", {}).get("goal_state", []):
        if not state or str(state[0]).lower() not in {
            "open",
            "close",
            "turnon",
            "turnoff",
        }:
            continue
        if len(state) < 2:
            continue
        candidate = str(state[1])
        site = sites.get(candidate)
        if site is not None:
            candidate = str(getattr(site, "parent_name", candidate))
        if _entity_exists(env, candidate):
            targets.append((candidate, list(state)))
    return tuple(targets)

class NonPhysicalPerturbationRuntime:
    """Execute one resolved perturbation through reset, action and observation hooks."""

    EVENT_START = 48
    EVENT_END = 72

    def __init__(self, plan: ExecutionPlan, seed: int = 0):
        self.plan = plan
        self.seed = 0
        self.rng = np.random.default_rng(0)
        self.events: list[dict[str, Any]] = []
        self.previous_action: np.ndarray | None = None
        self.previous_gripper_force: float | None = None
        self.previous_observation: dict[str, Any] | None = None
        self.observation_queue: deque[dict[str, Any]] = deque(maxlen=4)
        self.action_queue: deque[np.ndarray] = deque(maxlen=4)
        self.gripper_queue: deque[float] = deque(maxlen=4)
        self._stale_action_chunk: list[np.ndarray] = []
        self._stale_action_index = 0
        self._stale_gripper_chunk: list[float] = []
        self._stale_gripper_index = 0
        self._logged: set[str] = set()
        self._saved_poses: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._saved_joint_states: dict[str, tuple[np.ndarray, ...]] = {}
        self._dynamic_applied = False
        self._dynamic_restored = False
        self._dynamic_event_step: int | None = None
        self._dynamic_event_origin_eef: np.ndarray | None = None
        self._baseline_model_id: int | None = None
        self._model_baseline: dict[str, np.ndarray] = {}
        self.set_seed(seed)

    def set_seed(self, seed: int) -> None:
        """Restart this runtime's random stream for a deterministic attempt."""

        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)

    def prepare_reset(self, env: Any) -> None:
        """Restore mutable MuJoCo model arrays before starting another episode."""
        model = env.sim.model
        model_id = id(model)
        if self._baseline_model_id != model_id:
            self.capture_model_baseline(env)
            return
        for model_field, value in self._model_baseline.items():
            getattr(model, model_field)[:] = value

    def capture_model_baseline(self, env: Any) -> None:
        """Capture the clean model after LIBERO has placed episode fixtures."""
        model = env.sim.model
        fields = (
            "body_pos",
            "body_quat",
            "cam_pos",
            "cam_quat",
            "cam_fovy",
            "geom_rgba",
            "light_diffuse",
            "light_ambient",
        )
        self._baseline_model_id = id(model)
        self._model_baseline = {
            field: np.asarray(getattr(model, field)).copy()
            for field in fields
            if hasattr(model, field)
        }

    def reset(self) -> None:
        self.events.clear()
        self._clear_temporal_state()
        self._saved_poses.clear()
        self._saved_joint_states.clear()
        self._dynamic_applied = False
        self._dynamic_restored = False
        self._dynamic_event_step = None
        self._dynamic_event_origin_eef = None

    def _clear_temporal_state(self) -> None:
        self.previous_action = None
        self.previous_gripper_force = None
        self.previous_observation = None
        self.observation_queue.clear()
        self.action_queue.clear()
        self.gripper_queue.clear()
        self._stale_action_chunk.clear()
        self._stale_action_index = 0
        self._stale_gripper_chunk.clear()
        self._stale_gripper_index = 0
        self._logged.clear()

    def _d15_chunk_config(self) -> tuple[int, int]:
        params = self.plan.params
        try:
            chunk_size = max(1, int(params.get("chunk_size", 4)))
        except (TypeError, ValueError):
            chunk_size = 4
        try:
            stale_steps = max(1, int(params.get("stale_chunk_steps", chunk_size)))
        except (TypeError, ValueError):
            stale_steps = chunk_size
        return chunk_size, stale_steps

    def begin_rollout(self, env: Any) -> None:
        """Start perturbation timing after environment-only settling steps."""
        if not self.plan.case_id.startswith("D"):
            self._clear_temporal_state()
            return

        if self._dynamic_applied:
            for name, (position, quaternion) in self._saved_poses.items():
                if _entity_exists(env, name):
                    _set_entity_pose(env, name, position, quaternion)
        self.reset()
        self._stage_dynamic_assets(env)

    def _log_once(self, key: str, step: int, **details: Any) -> None:
        if key in self._logged:
            return
        self._logged.add(key)
        self.events.append(
            {"case_id": self.plan.case_id, "event": key, "step": int(step), **details}
        )

    def _event_started(self, step: int) -> bool:
        return self._dynamic_event_step is not None and step == self._dynamic_event_step

    def _event_duration_steps(self) -> int:
        if self.plan.case_id == "D14":
            return 1
        if self.plan.case_id == "D15":
            _, stale_steps = self._d15_chunk_config()
            return stale_steps
        default_duration = {
            "D16": 6,
            "D17": 40,
        }.get(self.plan.case_id, self.EVENT_END - self.EVENT_START)
        try:
            return max(
                1,
                int(
                    self.plan.params.get(
                        "event_duration_steps", default_duration
                    )
                ),
            )
        except (TypeError, ValueError):
            return default_duration

    @property
    def event_duration_steps(self) -> int:
        return self._event_duration_steps()

    def _event_active(self, step: int, duration: int | None = None) -> bool:
        if self._dynamic_event_step is None:
            return False
        if duration is None:
            duration = self._event_duration_steps()
        return self._dynamic_event_step <= step < self._dynamic_event_step + duration

    def _interaction_mode(self) -> str:
        return str(self.plan.params.get("interaction_mode", "placement")).lower()

    def _articulation_progress(self, env: Any, target: str) -> float:
        state = getattr(env, "object_states_dict", {}).get(target)
        before = self._saved_joint_states.get(target)
        if state is None or before is None:
            return 0.0
        after = tuple(np.asarray(value, dtype=np.float64) for value in state.get_joint_state())
        if len(after) != len(before):
            return 0.0
        return max(
            (float(np.linalg.norm(current - initial)) for current, initial in zip(after, before)),
            default=0.0,
        )

    def _articulation_anchor(self, env: Any, target: str) -> np.ndarray:
        position, _ = _functional_anchor(env, target)
        return np.asarray(position, dtype=np.float64)

    @staticmethod
    def _copy_observation(observation: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value.copy() if isinstance(value, np.ndarray) else value
            for key, value in observation.items()
        }

    @staticmethod
    def _image_keys(observation: dict[str, Any]) -> list[str]:
        return [
            key
            for key, value in observation.items()
            if isinstance(value, np.ndarray)
            and (key.endswith("_image") or key.endswith("_depth"))
        ]

    def _configured_rgb_image_keys(self, observation: dict[str, Any]) -> list[str]:
        """Resolve BDDL camera targets to RGB observation keys."""
        targets = {str(target).strip().lower() for target in self.plan.targets}
        if not targets:
            return []
        image_keys = self._image_keys(observation)
        if "rgb" in targets:
            return [key for key in image_keys if key.endswith("_image")]
        configured: list[str] = []
        for key in image_keys:
            if not key.endswith("_image"):
                continue
            camera_name = key[: -len("_image")].lower()
            if key.lower() in targets or camera_name in targets:
                configured.append(key)
        return configured

    def transform_observation(
        self, observation: dict[str, Any], step: int
    ) -> dict[str, Any]:
        case_id = self.plan.case_id
        out = self._copy_observation(observation)
        image_keys = self._image_keys(out)

        if case_id == "S16":
            for key in image_keys:
                value = out[key]
                if value.ndim >= 2:
                    shift = max(1, value.shape[-2] // 20)
                    out[key] = np.roll(value, shift=(shift, -shift), axis=(-3, -2))
            self._log_once("intrinsics_distortion", step)
        elif case_id == "S18":
            for key, value in list(out.items()):
                if isinstance(value, np.ndarray) and (
                    "eef_pos" in key or "joint_pos" in key
                ):
                    offset = np.zeros_like(value, dtype=np.float64)
                    offset.flat[: min(3, offset.size)] = [0.006, -0.004, 0.003][
                        : min(3, offset.size)
                    ]
                    out[key] = value + offset
            self._log_once("calibration_offset", step)
        elif case_id == "S19":
            for key in image_keys:
                value = out[key]
                if np.issubdtype(value.dtype, np.integer):
                    noise = self.rng.normal(0.0, 12.0, value.shape)
                    out[key] = np.clip(value.astype(np.float32) * 0.82 + noise, 0, 255).astype(
                        value.dtype
                    )
                else:
                    degraded = value.copy()
                    degraded[..., ::8, ::8] = 0
                    out[key] = degraded
            self._log_once("sensor_degradation", step)
        elif case_id == "D08" and self._event_active(step):
            for key in self._configured_rgb_image_keys(out):
                out[key] = np.zeros_like(out[key])
            self._log_once(
                "camera_dropout",
                step,
                targets=list(self.plan.targets),
                image_keys=self._configured_rgb_image_keys(out),
            )
        elif case_id == "D09" and self._event_active(step):
            for key in image_keys:
                value = out[key]
                if np.issubdtype(value.dtype, np.integer):
                    out[key] = np.clip(value.astype(np.float32) * 0.45, 0, 255).astype(
                        value.dtype
                    )
            self._log_once("exposure_change", step)
        elif case_id == "D10":
            if self._event_active(step) and self.previous_observation:
                for key in image_keys:
                    if key in self.previous_observation:
                        out[key] = self.previous_observation[key].copy()
                self._log_once("frame_freeze", step)
        elif case_id == "D11":
            if self._event_active(step) and self.previous_observation:
                for key, value in list(out.items()):
                    if key in self.previous_observation and isinstance(value, np.ndarray):
                        out[key] = self.previous_observation[key].copy()
                self._log_once("modality_state_freeze", step)
        elif case_id in {"S20", "D12"}:
            delay = 1 if case_id == "S20" else (2 if self._event_active(step) else 0)
            self.observation_queue.append(self._copy_observation(out))
            if delay and len(self.observation_queue) > delay:
                out = self._copy_observation(list(self.observation_queue)[-delay - 1])
                self._log_once("observation_delay", step, delay_steps=delay)

        self.previous_observation = self._copy_observation(out)
        return out

    def transform_action(self, action: np.ndarray, step: int) -> np.ndarray:
        current = np.asarray(action, dtype=np.float64).copy()
        case_id = self.plan.case_id
        previous = None if self.previous_action is None else self.previous_action.copy()

        if case_id == "S20":
            self.action_queue.append(current.copy())
            if len(self.action_queue) > 1:
                current = list(self.action_queue)[-2].copy()
                self._log_once("fixed_action_delay", step, delay_steps=1)
        elif case_id == "D13" and self._event_active(step) and previous is not None:
            current[:-1] = previous[:-1]
            self._log_once("arm_gripper_desynchronization", step)
        elif case_id == "D14" and self._event_started(step) and previous is not None:
            current = previous
            self._log_once("command_drop_repeat", step)
        elif case_id == "D15":
            chunk_size, stale_steps = self._d15_chunk_config()
            if not self._dynamic_applied:
                self.action_queue.append(current.copy())
            elif self._event_active(step, stale_steps):
                if not self._stale_action_chunk:
                    self._stale_action_chunk = list(self.action_queue)[-chunk_size:]
                    self._stale_action_index = 0
                if self._stale_action_chunk:
                    replay_index = min(
                        self._stale_action_index, len(self._stale_action_chunk) - 1
                    )
                    current = self._stale_action_chunk[replay_index].copy()
                    self._stale_action_index += 1
                    self._log_once(
                        "stale_action_chunk",
                        step,
                        chunk_length=len(self._stale_action_chunk),
                        stale_steps=stale_steps,
                    )
            else:
                self.action_queue.clear()
                self.action_queue.append(current.copy())
                self._stale_action_chunk.clear()
                self._stale_action_index = 0
        elif case_id == "D16" and self._event_active(step):
            current[:] = 0.0
            if current.size:
                current[0] = 0.12
            self._log_once("bounded_action_takeover", step)
        elif (
            case_id == "D17"
            and self._dynamic_applied
            and not self._dynamic_restored
            and self._event_active(step)
        ):
            current[-1] = -1.0
            self._log_once("recoverable_grasp_failure", step)

        self.previous_action = current.copy()
        return current

    def transform_gripper_force_command(self, command: float, step: int) -> float:
        current = float(np.clip(command, 0.0, 1.0))
        previous = self.previous_gripper_force
        case_id = self.plan.case_id

        if case_id == "S20" and previous is not None:
            current = previous
        elif case_id == "D14" and self._event_started(step) and previous is not None:
            current = previous
        elif case_id == "D15":
            chunk_size, stale_steps = self._d15_chunk_config()
            if not self._dynamic_applied:
                self.gripper_queue.append(current)
            elif self._event_active(step, stale_steps):
                if not self._stale_gripper_chunk:
                    self._stale_gripper_chunk = list(self.gripper_queue)[-chunk_size:]
                    self._stale_gripper_index = 0
                if self._stale_gripper_chunk:
                    replay_index = min(
                        self._stale_gripper_index, len(self._stale_gripper_chunk) - 1
                    )
                    current = self._stale_gripper_chunk[replay_index]
                    self._stale_gripper_index += 1
                    self._log_once(
                        "stale_action_chunk",
                        step,
                        chunk_length=len(self._stale_gripper_chunk),
                        stale_steps=stale_steps,
                    )
            else:
                self.gripper_queue.clear()
                self.gripper_queue.append(current)
                self._stale_gripper_chunk.clear()
                self._stale_gripper_index = 0
        elif case_id == "D16" and self._event_active(step):
            current = 0.0
        elif (
            case_id == "D17"
            and self._dynamic_applied
            and not self._dynamic_restored
            and self._event_active(step)
        ):
            current = 0.0

        self.previous_gripper_force = current
        return current

    def language_instruction(self, original: str, step: int) -> str:
        if self.plan.case_id == "S21":
            value = str(self.plan.params.get("value", "")).replace("_", " ").strip()
            if not value:
                raise PerturbationConfigurationError("S21 needs an equivalent language value")
            self._log_once("semantic_paraphrase", step)
            return value
        if (
            self.plan.case_id == "D21"
            and self._dynamic_event_step is not None
            and step >= self._dynamic_event_step
        ):
            self._log_once("runtime_language_clarification", step)
            return f"Please continue: {original}"
        return original

    def diagnostics(self) -> dict[str, Any]:
        return {
            "case_id": self.plan.case_id,
            "operator": self.plan.operator,
            "variant": self.plan.variant,
            "schedule": self.plan.schedule,
            "trigger": self.plan.trigger,
            "trigger_step": self._dynamic_event_step,
            "event_duration_steps": self.event_duration_steps,
            "assets": [asset.asset_id for asset in self.plan.assets],
            "events": list(self.events),
        }

    def apply_static(self, env: Any) -> None:
        case_id = self.plan.case_id
        if not case_id.startswith("S"):
            self._stage_dynamic_assets(env)
            return

        if case_id in {"S01", "S02"}:
            target = self.plan.targets[0]
            before, original_quat = _entity_pose(env, target)
            _, after, delta = _safe_offset_pose(
                env, target, (0.075, 0.045), ignored=self.plan.targets
            )
            yaw = 0.32 if case_id == "S01" else -0.24
            _set_entity_pose(
                env,
                target,
                after,
                _quaternion_multiply(_yaw_quaternion(yaw), original_quat),
            )
            self._log_once(
                "static_pose_transform", 0, target=target, delta_xy=delta.tolist(), yaw=yaw
            )
        elif case_id == "S04":
            if len(self.plan.targets) != 2:
                raise PerturbationConfigurationError(
                    "S04 planar position swap requires exactly two movable targets"
                )
            first, second = self.plan.targets
            first_position, first_quaternion = _entity_pose(env, first)
            second_position, second_quaternion = _entity_pose(env, second)
            first_after = first_position.copy()
            second_after = second_position.copy()
            first_after[:2] = second_position[:2]
            second_after[:2] = first_position[:2]
            _set_entity_pose(env, first, first_after, first_quaternion)
            _set_entity_pose(env, second, second_after, second_quaternion)
            self._log_once(
                "planar_object_position_swap",
                0,
                first=first,
                second=second,
                first_xy_before=first_position[:2].tolist(),
                first_xy_after=first_after[:2].tolist(),
                second_xy_before=second_position[:2].tolist(),
                second_xy_after=second_after[:2].tolist(),
            )
        elif case_id in {"S03", "S05", "S10", "S11", "S12"}:
            name = _injected_name(self.plan)
            if not _entity_exists(env, name):
                raise PerturbationValidationError(
                    f"Expected injected asset {name!r} is absent from the compiled scene"
                )
            reference_name = _static_asset_reference_name(self.plan)
            reference, _ = _entity_pose(env, reference_name)
            position = reference.copy()
            quaternion = _yaw_quaternion(0.0)
            anchor_name = reference_name
            if case_id == "S03":
                raised = reference.copy()
                raised[2] += 0.05
                _set_entity_pose(env, reference_name, raised)
                position[2] -= 0.01
            elif case_id == "S05":
                receiver_name = self.plan.targets[-1]
                receiver, anchor_name = _functional_anchor(env, receiver_name)
                target, _ = _entity_pose(env, self.plan.targets[0])
                direction = receiver[:2] - target[:2]
                length = float(np.linalg.norm(direction))
                if length < 1e-6:
                    direction = np.array([0.0, 1.0])
                else:
                    direction /= length
                position = target + 0.58 * (receiver - target)
                position[:2] += np.array([-direction[1], direction[0]]) * 0.035
                quaternion = _yaw_quaternion(math.atan2(direction[1], direction[0]) + math.pi / 2)
            elif case_id == "S10":
                position = _visible_clutter_pose(env, name, reference_name)
            elif case_id == "S11":
                # A same-class distractor belongs near the task target, but at a
                # distinct location from S10 so the two cases cannot collapse.
                target_position, _ = _entity_pose(env, self.plan.targets[0])
                position = target_position + np.array([-0.11, 0.09, 0.025])
            else:
                position, quaternion = _camera_occluder_pose(env, reference_name)
            if case_id != "S10" and not _candidate_is_clear(
                env,
                name,
                position[:2],
                0.055,
                ignored=(reference_name, *self.plan.targets),
            ):
                position[1] += 0.11
            _set_entity_pose(env, name, position, quaternion)
            self._log_once(
                "static_asset_placed",
                0,
                asset=name,
                asset_id=self.plan.assets[0].asset_id,
                reference=reference_name,
                anchor=anchor_name,
                position=position.tolist(),
            )
        elif case_id == "S13":
            changed = self._change_appearance(env, self.plan.targets)
            self._log_once("appearance_changed", 0, targets=changed)
        elif case_id == "S14":
            changed_geoms = self._change_scene_domain(env)
            self._set_lighting(env, 0.64)
            self._log_once("scene_domain_changed", 0, changed_geoms=changed_geoms)
        elif case_id == "S15":
            self._offset_camera(env, np.array([0.045, -0.035, 0.025]))
            self._log_once("camera_extrinsics_changed", 0)
        elif case_id == "S16":
            changed = []
            for camera in self.plan.targets:
                try:
                    camera_id = int(env.sim.model.camera_name2id(camera))
                except Exception:
                    continue
                before = float(env.sim.model.cam_fovy[camera_id])
                env.sim.model.cam_fovy[camera_id] = float(np.clip(before * 1.12, 20.0, 100.0))
                changed.append(camera)
            if not changed:
                raise PerturbationValidationError(
                    f"No camera intrinsics found for {self.plan.targets}"
                )
            env.sim.forward()
            self._log_once("camera_intrinsics_changed", 0, cameras=changed)
        elif case_id == "S17":
            robot = env.robots[0]
            indices = list(robot._ref_joint_pos_indexes)
            current = np.asarray(env.sim.data.qpos[indices]).copy()
            offset = np.array([0.035, -0.025, 0.02, 0.0, 0.0, 0.0, 0.0])[: len(current)]
            env.sim.data.qpos[indices] = current + offset
            env.sim.forward()
            self._log_once("robot_initial_state_changed", 0, joint_offset=offset.tolist())
        elif case_id == "S21":
            self.language_instruction("", 0)
        elif case_id == "S06":
            self._log_once(
                "target_instance_replaced",
                0,
                target=self.plan.targets[0],
                asset_id=self.plan.assets[0].asset_id,
                scale=self.plan.assets[0].scale,
            )
        elif case_id in {"S07", "S08", "S09"}:
            self._log_once("precompiled_geometry_changed", 0, targets=list(self.plan.targets))

        if case_id != "BASE" and not self.events and case_id not in {
            "S18",
            "S19",
            "S20",
        }:
            raise PerturbationValidationError(
                f"Static perturbation {case_id} produced no observable event"
            )

    def _stage_dynamic_assets(self, env: Any) -> None:
        for name in (*self.plan.targets, *self.plan.references):
            if _entity_exists(env, name) and name not in self._saved_poses:
                self._saved_poses[name] = _entity_pose(env, name)
        try:
            goal_target, _, _, _ = _goal_path_anchors(env)
        except PerturbationValidationError:
            goal_target = None
        if goal_target is not None and goal_target not in self._saved_poses:
            self._saved_poses[goal_target] = _entity_pose(env, goal_target)
        for target in _goal_interaction_targets(env):
            if target not in self._saved_poses:
                self._saved_poses[target] = _entity_pose(env, target)
        for target, _ in _goal_articulation_targets(env):
            state = getattr(env, "object_states_dict", {}).get(target)
            if state is not None and target not in self._saved_joint_states:
                self._saved_joint_states[target] = tuple(
                    np.asarray(value, dtype=np.float64).copy()
                    for value in state.get_joint_state()
                )
        for index, _ in enumerate(self.plan.assets):
            name = _injected_name(self.plan, index)
            if _entity_exists(env, name):
                position, quat = _entity_pose(env, name)
                self._saved_poses[name] = (position, quat)
                _set_entity_pose(env, name, np.array([0.0, 0.0, -5.0]), quat)

    def _change_appearance(self, env: Any, targets: tuple[str, ...]) -> list[str]:
        changed: list[str] = []
        for target in targets:
            if not _entity_exists(env, target):
                continue
            body_ids = set(_entity_body_ids(env, target))
            for geom_id in range(int(env.sim.model.ngeom)):
                if int(env.sim.model.geom_bodyid[geom_id]) not in body_ids:
                    continue
                rgba = np.asarray(env.sim.model.geom_rgba[geom_id]).copy()
                rgba[:3] = np.array([0.18, 0.72, 0.38])
                env.sim.model.geom_rgba[geom_id] = rgba
                changed.append(target)
        if not changed:
            raise PerturbationValidationError(
                f"No visible or collision geoms found for appearance targets {targets}"
            )
        env.sim.forward()
        return sorted(set(changed))

    def _change_scene_domain(self, env: Any) -> int:
        """Shift the full scene palette without duplicating S13's target recolor."""
        changed = 0
        for geom_id in range(int(env.sim.model.ngeom)):
            rgba = np.asarray(env.sim.model.geom_rgba[geom_id]).copy()
            if rgba.shape[0] < 4 or rgba[3] <= 0.0:
                continue
            rgb = rgba[:3]
            # A cool, lower-saturation domain shift preserves shading and texture;
            # S13 instead applies one flat green material to task entities only.
            luminance = float(np.dot(rgb, np.array([0.2126, 0.7152, 0.0722])))
            shifted = 0.52 * rgb + 0.48 * np.array(
                [0.72 * luminance, 0.86 * luminance, min(1.0, 1.18 * luminance)]
            )
            rgba[:3] = np.clip(shifted, 0.0, 1.0)
            env.sim.model.geom_rgba[geom_id] = rgba
            changed += 1
        if not changed:
            raise PerturbationValidationError("MuJoCo model exposes no visible scene geoms")
        env.sim.forward()
        return changed

    def _set_lighting(self, env: Any, factor: float) -> None:
        if not hasattr(env.sim.model, "light_diffuse"):
            raise PerturbationValidationError("MuJoCo model exposes no lights")
        env.sim.model.light_diffuse[:] *= float(factor)
        env.sim.model.light_ambient[:] *= float(factor)
        env.sim.forward()

    def _restore_lighting(self, env: Any) -> None:
        fields = ("light_diffuse", "light_ambient")
        if any(field not in self._model_baseline for field in fields):
            raise PerturbationValidationError(
                "MuJoCo lighting baseline was not captured before D09"
            )
        for model_field in fields:
            getattr(env.sim.model, model_field)[:] = self._model_baseline[model_field]
        env.sim.forward()

    def _offset_camera(self, env: Any, delta: np.ndarray) -> None:
        changed = False
        for camera in self.plan.targets or ("agentview",):
            try:
                camera_id = env.sim.model.camera_name2id(camera)
            except Exception:
                continue
            env.sim.model.cam_pos[camera_id] += np.asarray(delta)
            changed = True
        if not changed:
            raise PerturbationValidationError(
                f"No configured cameras exist: {self.plan.targets}"
            )
        env.sim.forward()

    def before_simulation_step(self, env: Any, step: int) -> None:
        case_id = self.plan.case_id
        if not case_id.startswith("D"):
            return
        if self._dynamic_applied:
            if (
                case_id == "D09"
                and not self._dynamic_restored
                and not self._event_active(step)
            ):
                self._restore_lighting(env)
                self._dynamic_restored = True
                self._log_once("dynamic_lighting_restored", step)
            if case_id == "D17" and not self._dynamic_restored:
                try:
                    eef = np.asarray(
                        env.sim.data.site_xpos[env.robots[0].eef_site_id],
                        dtype=np.float64,
                    )
                except Exception:
                    eef = None
                retreat = float(self.plan.params.get("recovery_retreat_m", 0.07))
                retreated = (
                    eef is not None
                    and self._dynamic_event_origin_eef is not None
                    and np.linalg.norm(eef - self._dynamic_event_origin_eef) >= retreat
                )
                expired = not self._event_active(step)
                if retreated or expired:
                    self._dynamic_restored = True
                    self._log_once(
                        "grasp_failure_window_ended",
                        step,
                        reason="retreated" if retreated else "duration_elapsed",
                    )
            if (
                case_id == "D04"
                and not self._dynamic_restored
                and self._dynamic_event_step is not None
                and step >= self._dynamic_event_step + self._event_duration_steps()
            ):
                name = _injected_name(self.plan)
                position, quat = self._saved_poses.get(
                    name, (np.array([0.0, 0.0, -5.0]), _yaw_quaternion(0.0))
                )
                _set_entity_pose(env, name, position, quat)
                self._dynamic_restored = True
                self._log_once("dynamic_asset_restored", step, asset=name)
            return
        if not self._dynamic_triggered(env, step):
            return

        if case_id in {"D01", "D02", "D06", "D18", "D19"}:
            if self._interaction_mode() == "articulation" and case_id in {"D18", "D19"}:
                articulation_targets = _goal_articulation_targets(env)
                if not articulation_targets:
                    raise PerturbationValidationError(
                        f"{case_id} articulation fallback has no goal fixture"
                    )
                target, _ = articulation_targets[0]
                _, after, applied = _safe_offset_pose(
                    env,
                    target,
                    _dynamic_pose_requested_delta(case_id, target, self.plan.params),
                )
                self._log_once(
                    "articulation_reachable_state_change",
                    step,
                    target=target,
                    delta_xy=applied.tolist(),
                    position=after.tolist(),
                )
                self._dynamic_event_step = int(step)
                self._dynamic_applied = True
                return
            targets = [name for name in self.plan.targets if _entity_exists(env, name)]
            if not targets:
                raise PerturbationValidationError(
                    f"Dynamic case {case_id} has no movable target in {self.plan.targets}"
                )
            target = targets[0]
            delta = _dynamic_pose_requested_delta(case_id, target, self.plan.params)
            if case_id == "D19":
                before, current_quaternion = _entity_pose(env, target)
                initial = self._saved_poses.get(target, (before, current_quaternion))[0]
                return_direction = initial[:2] - before[:2]
                return_length = float(np.linalg.norm(return_direction))
                if return_length < 1e-6:
                    return_direction = np.array([-1.0, 0.0])
                else:
                    return_direction /= return_length
                after = before.copy()
                after[:2] += return_direction * 0.065
                after[2] += 0.035
                x_min, x_max, y_min, y_max = _workspace_bounds(env)
                after[0] = np.clip(after[0], x_min, x_max)
                after[1] = np.clip(after[1], y_min, y_max)
                applied = after[:2] - before[:2]
                _set_entity_pose(env, target, after, current_quaternion)
            else:
                _, after, applied = _safe_offset_pose(env, target, delta)
            yaw = {"D01": 0.28, "D02": -0.24}.get(case_id)
            if case_id == "D18" and target in self._saved_poses:
                initial_position, current_quaternion = self._saved_poses[target]
                after[2] = initial_position[2]
                _set_entity_pose(env, target, after, current_quaternion)
            if yaw is not None:
                _, current_quaternion = _entity_pose(env, target)
                _set_entity_pose(
                    env,
                    target,
                    after,
                    _quaternion_multiply(_yaw_quaternion(yaw), current_quaternion),
                )
            self._log_once(
                "dynamic_state_change",
                step,
                target=target,
                delta_xy=applied.tolist(),
                yaw=yaw,
            )
        elif case_id in {"D03", "D04", "D05"}:
            name = _injected_name(self.plan)
            reference_name = next(
                (target for target in self.plan.targets if _entity_exists(env, target)),
                self.plan.references[0] if self.plan.references else None,
            )
            if reference_name is None:
                raise PerturbationValidationError(
                    f"Dynamic asset case {case_id} has no scene reference"
                )
            reference, _ = _entity_pose(env, reference_name)
            anchor_name = reference_name
            offset = {
                "D03": np.array([0.0, 0.0, 0.025]),
            }.get(case_id)
            if case_id == "D04":
                position, quaternion = _camera_occluder_pose(env, reference_name)
            elif case_id == "D05":
                if self._interaction_mode() == "articulation":
                    articulation_targets = _goal_articulation_targets(env)
                    if not articulation_targets:
                        raise PerturbationValidationError(
                            "D05 articulation fallback has no goal fixture"
                        )
                    target_name, _ = articulation_targets[0]
                    target = self._articulation_anchor(env, target_name)
                    anchor_name = target_name
                    position = target.copy()
                    position[2] += 0.04
                    quaternion = _yaw_quaternion(0.0)
                else:
                    target_name, target, anchor_name, receiver = _goal_path_anchors(env)
                    direction = receiver[:2] - target[:2]
                    length = float(np.linalg.norm(direction))
                    direction = direction / length if length >= 1e-6 else np.array([0.0, 1.0])
                    position = target + 0.62 * (receiver - target)
                    position[:2] += np.array([-direction[1], direction[0]]) * 0.025
                    quaternion = _yaw_quaternion(math.atan2(direction[1], direction[0]) + math.pi / 2)
            else:
                position, anchor_name = _functional_anchor(env, reference_name)
                position = position + offset
                quaternion = _yaw_quaternion(0.0)
            _set_entity_pose(env, name, position, quaternion)
            self._log_once(
                "dynamic_asset_entered",
                step,
                asset=name,
                reference=reference_name,
                anchor=anchor_name,
                position=position.tolist(),
            )
        elif case_id == "D07":
            self._offset_camera(env, np.array([0.025, -0.018, 0.012]))
            self._log_once("dynamic_camera_offset", step)
        elif case_id == "D09":
            self._set_lighting(env, 0.48)
            self._log_once("dynamic_lighting_change", step)
        elif case_id == "D17":
            # Opening the gripper is applied through transform_action; no pose teleport.
            self._dynamic_event_origin_eef = np.asarray(
                env.sim.data.site_xpos[env.robots[0].eef_site_id], dtype=np.float64
            ).copy()
            self._log_once("grasp_failure_window_started", step)
        elif case_id == "D21":
            self._log_once("runtime_language_clarification", step)
        elif case_id in {"D08", "D10", "D11", "D12", "D13", "D14", "D15", "D16"}:
            # These execute in observation, action, or language hooks.
            pass
        else:
            raise PerturbationConfigurationError(
                f"No simulator-state implementation for dynamic case {case_id}"
            )
        self._dynamic_event_step = int(step)
        self._dynamic_applied = True

    def _dynamic_triggered(self, env: Any, step: int) -> bool:
        case_id = self.plan.case_id
        target = next(
            (name for name in self.plan.targets if _entity_exists(env, name)), None
        )
        try:
            eef = np.asarray(
                env.sim.data.site_xpos[env.robots[0].eef_site_id], dtype=np.float64
            )
        except Exception:
            eef = None

        if case_id == "D01" and target and eef is not None:
            position, _ = _entity_pose(env, target)
            return bool(np.linalg.norm(eef - position) <= 0.12)
        if case_id == "D17" and target and eef is not None:
            position, _ = _entity_pose(env, target)
            if self._interaction_mode() == "articulation":
                return bool(np.linalg.norm(eef - self._articulation_anchor(env, target)) <= 0.14)
            closing = bool(
                self.previous_action is not None
                and self.previous_action.size
                and self.previous_action[-1] > 0.0
            )
            return bool(closing and np.linalg.norm(eef - position) <= 0.12)
        if (
            self._interaction_mode() == "articulation"
            and case_id in {"D02", "D03", "D05", "D19"}
            and eef is not None
        ):
            articulation_targets = _goal_articulation_targets(env)
            if articulation_targets:
                target_name, _ = articulation_targets[0]
                anchor = self._articulation_anchor(env, target_name)
                threshold = 0.18 if case_id == "D05" else 0.16
                if case_id == "D19":
                    return bool(
                        self._articulation_progress(env, target_name)
                        >= float(self.plan.params.get("trigger_state_change_m", 0.02))
                        and np.linalg.norm(eef - anchor) <= threshold
                    )
                return bool(np.linalg.norm(eef - anchor) <= threshold)
        if case_id in {"D02", "D03", "D05", "D19"}:
            try:
                goal_target, position, _, receiver = _goal_path_anchors(env)
            except PerturbationValidationError:
                goal_target = None
                position = None
                receiver = None
            if goal_target is not None and position is not None:
                saved = self._saved_poses.get(goal_target)
                if saved is None:
                    return False
                initial = saved[0]
                transported = bool(
                    position[2] >= initial[2] + 0.025
                    or np.linalg.norm(position[:2] - initial[:2]) >= 0.05
                )
                if case_id == "D05":
                    closing = bool(
                        self.previous_action is not None
                        and self.previous_action.size
                        and self.previous_action[-1] > 0.0
                    )
                    held_near_eef = bool(
                        eef is not None and np.linalg.norm(eef - position) <= 0.18
                    )
                    return bool(transported and closing and held_near_eef)
                return bool(
                    transported
                    and receiver is not None
                    and eef is not None
                    and np.linalg.norm(eef - receiver) <= 0.16
                )
        if case_id == "D18" and target:
            if self._interaction_mode() == "articulation":
                articulation_targets = _goal_articulation_targets(env)
                if not articulation_targets or eef is None:
                    return False
                articulation_target, _ = articulation_targets[0]
                return bool(
                    self._articulation_progress(env, articulation_target)
                    >= float(self.plan.params.get("trigger_state_change_m", 0.02))
                    and np.linalg.norm(
                        eef - self._articulation_anchor(env, articulation_target)
                    )
                    <= 0.18
                )
            position, _ = _entity_pose(env, target)
            saved = self._saved_poses.get(target)
            if saved is None:
                return False
            transported = bool(
                position[2] >= saved[0][2] + 0.04
                or np.linalg.norm(position[:2] - saved[0][:2]) >= 0.06
            )
            closing = bool(
                self.previous_action is not None
                and self.previous_action.size
                and self.previous_action[-1] > 0.0
            )
            held_near_eef = bool(
                eef is not None and np.linalg.norm(eef - position) <= 0.18
            )
            return bool(transported and closing and held_near_eef)
        if self.plan.trigger == "state_change":
            if eef is None:
                return False
            lift_threshold = float(self.plan.params.get("trigger_lift_m", 0.025))
            move_threshold = float(self.plan.params.get("trigger_move_m", 0.05))
            grasp_distance = float(self.plan.params.get("grasp_distance_m", 0.18))
            closing = bool(
                self.previous_action is not None
                and self.previous_action.size
                and self.previous_action[-1] > 0.0
            )
            if not closing:
                return False
            for name in _goal_interaction_targets(env):
                saved = self._saved_poses.get(name)
                if saved is None:
                    continue
                position, _ = _entity_pose(env, name)
                moved = bool(
                    position[2] >= saved[0][2] + lift_threshold
                    or np.linalg.norm(position[:2] - saved[0][:2]) >= move_threshold
                )
                if moved and np.linalg.norm(eef - position) <= grasp_distance:
                    return True
            return False
        if self.plan.trigger == "task_phase":
            if eef is None:
                return False
            threshold = float(self.plan.params.get("trigger_distance_m", 0.15))
            for name in _goal_interaction_targets(env):
                position, _ = _entity_pose(env, name)
                if np.linalg.norm(eef - position) <= threshold:
                    return True
            return False
        return False
