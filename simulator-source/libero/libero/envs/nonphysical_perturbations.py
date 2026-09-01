from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


ALL_CASE_IDS = tuple(
    [f"S{index:02d}" for index in range(1, 23)]
    + [f"D{index:02d}" for index in range(1, 22)]
)
LEGACY_CASE_IDS = tuple(
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
    "S22": ("appearance",),
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
    "D20": ("robot_state",),
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
    disturbance_targets: tuple[str, ...] | None = None
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
        "disturbance_targets": list(plan.disturbance_targets or ()),
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
    if value is True or value is False:
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    normalized = str(value)
    if normalized.casefold() in {"none", "null", "false"}:
        return ()
    return (normalized,)


def _param_float(params: dict[str, Any], key: str, default: float) -> float:
    try:
        value = float(params.get(key, default))
    except (TypeError, ValueError) as exc:
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must be a finite number"
        ) from exc
    if not math.isfinite(value):
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must be a finite number"
        )
    return value


def _param_int(params: dict[str, Any], key: str, default: int) -> int:
    try:
        value = int(params.get(key, default))
    except (TypeError, ValueError) as exc:
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must be an integer"
        ) from exc
    return value


def _param_bool(params: dict[str, Any], key: str, default: bool = False) -> bool:
    raw = params.get(key, default)
    if isinstance(raw, bool):
        return raw
    normalized = str(raw).strip().casefold()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off", "none", "null"}:
        return False
    raise PerturbationConfigurationError(
        f"Perturbation parameter {key} must be boolean"
    )


def _param_vector(
    params: dict[str, Any], key: str, default: tuple[float, ...]
) -> np.ndarray:
    raw = params.get(key, default)
    try:
        value = np.asarray(raw, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must be a numeric vector"
        ) from exc
    if value.shape != (len(default),) or not np.all(np.isfinite(value)):
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must contain {len(default)} finite values"
        )
    return value


def _required_param_float(params: dict[str, Any], key: str) -> float:
    if key not in params:
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must be provided by the task BDDL"
        )
    return _param_float(params, key, 0.0)


def _required_param_vector(
    params: dict[str, Any], key: str, length: int
) -> np.ndarray:
    if key not in params:
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must be provided by the task BDDL"
        )
    return _param_vector(params, key, (0.0,) * length)


def _param_action_vector(
    params: dict[str, Any], key: str, default: tuple[float, ...]
) -> np.ndarray:
    """Read an action-sized vector while allowing a short prefix in BDDL."""

    raw = params.get(key, default)
    try:
        value = np.asarray(raw, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must be a numeric vector"
        ) from exc
    if not value.size or not np.all(np.isfinite(value)):
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must contain finite values"
        )
    return value


def _param_offsets(
    params: dict[str, Any],
    key: str,
    count: int,
    defaults: tuple[tuple[float, float], ...],
) -> np.ndarray:
    """Read a task-local list of XY offsets without changing legacy defaults."""

    raw = params.get(key)
    if raw is None:
        return np.asarray(defaults[:count], dtype=np.float64)
    try:
        value = np.asarray(raw, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must contain XY offsets"
        ) from exc
    if value.size != count * 2 or not np.all(np.isfinite(value)):
        raise PerturbationConfigurationError(
            f"Perturbation parameter {key} must contain {count} finite XY pairs"
        )
    return value.reshape(count, 2)


def _rpy_quaternion(rpy: np.ndarray) -> np.ndarray:
    roll, pitch, yaw = np.asarray(rpy, dtype=np.float64)
    cr, sr = math.cos(roll / 2.0), math.sin(roll / 2.0)
    cp, sp = math.cos(pitch / 2.0), math.sin(pitch / 2.0)
    cy, sy = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
    return np.array(
        [
            cr * cp * cy + sr * sp * sy,
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
        ],
        dtype=np.float64,
    )


def _transform_image_geometry(
    value: np.ndarray,
    shift_xy: np.ndarray,
    crop_ratio: float,
    distortion_strength: float,
) -> np.ndarray:
    """Apply the configurable S16 image transform without changing its shape."""

    if value.ndim < 2:
        return value
    spatial_axes = (-3, -2) if value.ndim >= 3 else (-2, -1)
    height = int(value.shape[spatial_axes[0]])
    width = int(value.shape[spatial_axes[1]])
    transformed = value
    if crop_ratio or distortion_strength:
        if value.ndim > 3:
            raise PerturbationConfigurationError(
                "S16 image geometry expects an image or depth array without a batch dimension"
            )
        yy, xx = np.indices((height, width), dtype=np.float64)
        center_x = (width - 1) / 2.0
        center_y = (height - 1) / 2.0
        normalized_x = (xx - center_x) / max(center_x, 1.0)
        normalized_y = (yy - center_y) / max(center_y, 1.0)
        scale = 1.0 / max(1.0 - crop_ratio, 1e-6)
        radial = 1.0 + distortion_strength * (
            normalized_x * normalized_x + normalized_y * normalized_y
        )
        source_x = center_x + normalized_x * radial * scale * max(center_x, 1.0)
        source_y = center_y + normalized_y * radial * scale * max(center_y, 1.0)
        source_x = np.clip(np.rint(source_x), 0, width - 1).astype(np.intp)
        source_y = np.clip(np.rint(source_y), 0, height - 1).astype(np.intp)
        transformed = (
            value[source_y, source_x]
            if value.ndim == 2
            else value[source_y, source_x, ...]
        )
    if np.allclose(shift_xy, np.array([0.05, -0.05])):
        # Preserve the pre-parameterization rule: one height-derived shift is
        # applied to both image axes, including the minimum one-pixel shift.
        legacy_shift = max(1, height // 20)
        shifts = (legacy_shift, -legacy_shift)
    else:
        shifts = (
            int(round(height * float(shift_xy[0]))),
            int(round(width * float(shift_xy[1]))),
        )
    return np.roll(transformed, shift=shifts, axis=spatial_axes)


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
    try:
        schema_version = int(config.get("schema_version", 4))
    except (TypeError, ValueError):
        schema_version = 4
    required_cases = ALL_CASE_IDS if schema_version >= 5 else LEGACY_CASE_IDS
    missing = set(required_cases) - set(entries)
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

    asset_index = _asset_index(asset_root)
    staged = case_id.startswith("D")
    params = fields.get("params", {})
    if not isinstance(params, dict):
        params = {}
    dynamic_asset_scale = (
        _param_float(params, "asset_scale", 1.0)
        if case_id in {"D03", "D04", "D05", "D06"}
        else 1.0
    )
    static_barrier_scale = (
        _param_float(params, "barrier_scale", 1.0)
        if case_id == "S05"
        else 1.0
    )
    asset_ids = list(CASE_ASSETS.get(case_id, ()))
    if case_id in {"D03", "D06"} and "asset_id" in params:
        configured_assets = _name_tuple(params.get("asset_id"))
        if len(configured_assets) != 1:
            raise PerturbationConfigurationError(
                f"{case_id} asset_id must name exactly one asset"
            )
        asset_ids = [configured_assets[0]]
    plan_references = _name_tuple(fields.get("references"))
    persistent_existing_obstacle = case_id == "D03" and _param_bool(
        params, "persistent_existing_obstacle", False
    )
    persistent_movable_asset = case_id == "D03" and _param_bool(
        params, "persistent_movable_asset", False
    )
    if persistent_existing_obstacle and persistent_movable_asset:
        raise PerturbationConfigurationError(
            "D03 persistent obstacle modes are mutually exclusive"
        )
    if persistent_existing_obstacle or persistent_movable_asset:
        if variant != "persistent_triggered_receiver_occupation":
            raise PerturbationConfigurationError(
                "Persistent D03 obstacles require the persistent_triggered_receiver_occupation variant"
            )
        if persistent_existing_obstacle:
            if len(plan_references) != 1:
                raise PerturbationConfigurationError(
                    "D03 persistent_existing_obstacle requires exactly one existing reference"
                )
            if "asset_id" in params:
                raise PerturbationConfigurationError(
                    "D03 persistent_existing_obstacle cannot also configure asset_id"
                )
            asset_ids = []
        else:
            if "asset_id" not in params or len(asset_ids) != 1:
                raise PerturbationConfigurationError(
                    "D03 persistent_movable_asset requires exactly one explicit asset_id"
                )
            plan_references = ()
    if case_id in {"S10", "S11"} and "asset_count" in params:
        try:
            asset_count = int(params["asset_count"])
        except (TypeError, ValueError) as exc:
            raise PerturbationConfigurationError(
                f"{case_id} asset_count must be an integer"
            ) from exc
        if not 1 <= asset_count <= 4:
            raise PerturbationConfigurationError(
                f"{case_id} asset_count must be between 1 and 4"
            )
        if case_id == "S10":
            asset_ids = list(CASE_ASSETS[case_id]) * asset_count
    assets = [
        _resolve_asset(
            asset_id,
            asset_root,
            asset_index,
            staged=staged,
            scale=(static_barrier_scale if case_id == "S05" else dynamic_asset_scale),
        )
        for index, asset_id in enumerate(asset_ids)
    ]
    if case_id in {"S06", "S11"}:
        source_suite = str(config.get("source_suite", ""))
        fixture_variant = params.get("fixture_variant") if case_id == "S06" else None
        fixture_distractor = case_id == "S11" and _param_bool(
            params, "fixture_distractor", False
        )
        if fixture_variant:
            # Fixture variants are geometry-only task overrides.  They do not
            # replace a movable target with an incompatible object asset.
            source_suite = ""
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
        if not suite_default and not fixture_variant and not fixture_distractor:
            raise PerturbationConfigurationError(
                f"No semantics-preserving {case_id} asset for suite {source_suite!r}"
            )
        if fixture_variant or fixture_distractor:
            count = 0
        elif case_id == "S11":
            count = int(params.get("asset_count", 1))
            if not 1 <= count <= 4:
                raise PerturbationConfigurationError(
                    "S11 asset_count must be between 1 and 4"
                )
        else:
            count = 1
        if count:
            assets.extend(
                _resolve_asset(
                    suite_default[0],
                    asset_root,
                    asset_index,
                    staged=False,
                    replacement=case_id == "S06",
                    scale=suite_default[1],
                )
                for _ in range(count)
            )

    constraints = _name_tuple(fields.get("constraints"))
    return ExecutionPlan(
        case_id=case_id,
        schedule="static" if case_id.startswith("S") else "dynamic",
        operator=operator,
        variant=variant,
        targets=_name_tuple(fields.get("targets")),
        disturbance_targets=(
            _name_tuple(fields["disturbance_targets"])
            if "disturbance_targets" in fields
            else None
        ),
        references=plan_references,
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


def _clutter_clearance_ignored(
    plan: ExecutionPlan,
    asset_name: str,
    placed_assets: tuple[str, ...],
    support_names: tuple[str, ...],
) -> tuple[str, ...]:
    """Resolve task-local collision exclusions for static clutter placement."""

    ignored = [asset_name, *placed_assets, *support_names]
    ignored.extend(_support_entity_names(plan.params))
    if not _param_bool(plan.params, "clear_of_task_entities", False):
        ignored.extend(plan.targets)
        ignored.extend(plan.references)
    return tuple(dict.fromkeys(ignored))


def _set_movable_asset_contact_margin(obj: Any, margin_m: float) -> None:
    if not 0.0 <= margin_m <= 0.02:
        raise PerturbationConfigurationError(
            "asset_contact_margin_m must be between 0.0 and 0.02"
        )
    value = f"{margin_m:.9g}"
    for root in _mujoco_xml_roots(obj):
        for geom in root.iter("geom"):
            if geom.get("group", "0") != "0":
                continue
            if geom.get("contype", "1") == "0" and geom.get("conaffinity", "1") == "0":
                continue
            geom.set("margin", value)


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
            replacement.rotation = getattr(original, "rotation", (0.0, 0.0))
            replacement.rotation_axis = getattr(original, "rotation_axis", "z")
            replacement.object_properties = getattr(
                original, "object_properties", {"vis_site_names": {}}
            )
            _scale_mujoco_object(replacement, asset.scale)
            if _param_bool(plan.params, "sampler_compatible", False):
                # Keep the original placement envelope during reset. The
                # compiled collision and visual geometry still come from the
                # replacement asset, while narrow BDDL regions retain their
                # original sampling contract.
                _set_object_site_pos(
                    replacement,
                    "bottom_site",
                    getattr(original, "bottom_offset"),
                )
                _set_object_site_pos(
                    replacement,
                    "top_site",
                    getattr(original, "top_offset"),
                )
                _set_object_site_pos(
                    replacement,
                    "horizontal_radius_site",
                    (float(getattr(original, "horizontal_radius")), 0.0, 0.0),
                )
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
        movable_injected_asset = (
            plan.case_id == "D03"
            and _param_bool(plan.params, "persistent_movable_asset", False)
        ) or (
            plan.case_id in {"S10", "S11"}
            and _param_bool(plan.params, "movable_asset", False)
        )
        # Structural assets stay welded. Explicitly movable object distractors
        # receive a free joint so the policy can physically relocate them.
        obj = object_factory(
            str(asset.xml_path),
            name=name,
            joints="default" if movable_injected_asset else None,
        )
        obj.category_name = "perturbation_asset"
        obj.rotation = (0.0, 0.0)
        obj.rotation_axis = "z"
        obj.object_properties = {"vis_site_names": {}}
        weld_asset_joints = _param_bool(plan.params, "weld_asset_joints", False)
        if movable_injected_asset and weld_asset_joints:
            raise PerturbationConfigurationError(
                "A movable injected asset cannot weld its free joint"
            )
        if weld_asset_joints:
            _remove_object_joints(obj)
        if plan.case_id == "S03" and "asset_geometry_factors" in plan.params:
            factors = _param_vector(
                plan.params, "asset_geometry_factors", (1.0, 1.0, 1.0)
            )
            if np.any(factors <= 0.0):
                raise PerturbationConfigurationError(
                    "S03 asset_geometry_factors must be positive"
                )
            _scale_mujoco_object_axes(obj, tuple(float(value) for value in factors))
        elif plan.case_id == "S05" and "barrier_geometry_factors" in plan.params:
            factors = _param_vector(
                plan.params, "barrier_geometry_factors", (1.0, 1.0, 1.0)
            )
            if np.any(factors <= 0.0):
                raise PerturbationConfigurationError(
                    "S05 barrier_geometry_factors must be positive"
                )
            # Apply the task-local anisotropic correction after the published
            # uniform barrier scale; this preserves across-path coverage while
            # allowing a narrow gap between nearby scene objects.
            _scale_mujoco_object(obj, asset.scale)
            _scale_mujoco_object_axes(obj, tuple(float(value) for value in factors))
        else:
            _scale_mujoco_object(obj, asset.scale)
        if movable_injected_asset and "asset_contact_margin_m" in plan.params:
            _set_movable_asset_contact_margin(
                obj,
                _param_float(plan.params, "asset_contact_margin_m", 0.0),
            )
        root = obj.get_obj() if hasattr(obj, "get_obj") else None
        if root is not None:
            # A movable body cannot start below MuJoCo's infinite floor plane.
            # Keep it safely above the scene until begin_rollout stages it with
            # collision disabled; welded assets retain their legacy pose.
            root.set("pos", "0 0 3" if movable_injected_asset else "0 0 -5")
            if (
                plan.case_id in {"S12", "D04"}
                and not _param_bool(plan.params, "physical_collision", False)
            ) or bool(plan.params.get("visual_only_asset", False)):
                for geom in root.findall(".//geom"):
                    if geom.get("group", "0") == "0":
                        geom.set("contype", "0")
                        geom.set("conaffinity", "0")
        objects_dict[name] = obj
        injected.append(name)
    return AssetInjectionResult(tuple(injected), tuple(replaced))


def _remove_object_joints(obj: Any) -> None:
    """Weld every body in an opt-in injected asset before MuJoCo compilation."""

    for root in _mujoco_xml_roots(obj):
        for parent in root.iter():
            for child in list(parent):
                if child.tag == "joint":
                    parent.remove(child)


def _scale_mujoco_object(obj: Any, factor: float) -> None:
    if abs(float(factor) - 1.0) < 1e-9:
        return
    for root in _mujoco_xml_roots(obj):
        for mesh in root.findall(".//mesh"):
            mesh.set("scale", _scale_xml_values(mesh.get("scale", "1 1 1"), factor))
        for element in root.findall(".//*[@pos]"):
            element.set("pos", _scale_xml_values(element.get("pos"), factor))
        for geom in root.findall(".//geom"):
            if geom.get("size"):
                geom.set("size", _scale_xml_values(geom.get("size"), factor))


def _mujoco_xml_roots(obj: Any) -> tuple[Any, ...]:
    """Return the asset and compiled body XML sections exactly once."""

    roots: list[Any] = []
    asset = getattr(obj, "asset", None)
    if asset is not None:
        roots.append(asset)
    get_obj = getattr(obj, "get_obj", None)
    body = get_obj() if callable(get_obj) else None
    if body is not None and all(body is not root for root in roots):
        roots.append(body)
    elif body is None:
        worldbody = getattr(obj, "worldbody", None)
        if worldbody is not None and all(worldbody is not root for root in roots):
            roots.append(worldbody)
    return tuple(roots)


def _set_object_site_pos(obj: Any, suffix: str, value: Any) -> None:
    """Set one object's local sampling site without changing its world pose."""

    prefix = str(getattr(obj, "naming_prefix", ""))
    names = {f"{prefix}{suffix}", suffix}
    roots = []
    worldbody = getattr(obj, "worldbody", None)
    if worldbody is not None:
        roots.append(worldbody)
    get_obj = getattr(obj, "get_obj", None)
    if callable(get_obj):
        root = get_obj()
        if root is not None and root not in roots:
            roots.append(root)
    site = None
    for root in roots:
        site = next(
            (element for element in root.iter("site") if element.get("name") in names),
            None,
        )
        if site is not None:
            break
    if site is None:
        raise PerturbationConfigurationError(
            f"Replacement asset is missing sampling site {suffix!r}"
        )
    position = np.asarray(value, dtype=np.float64).reshape(-1)
    if position.shape != (3,) or not np.all(np.isfinite(position)):
        raise PerturbationConfigurationError(
            f"Sampling site {suffix!r} must have three finite coordinates"
        )
    site.set("pos", " ".join(str(float(component)) for component in position))


def _scale_mujoco_object_axes(
    obj: Any, factors: tuple[float, float, float]
) -> None:
    """Scale an injected asset around its local origin on each axis."""

    for root in _mujoco_xml_roots(obj):
        for mesh in root.findall(".//mesh"):
            mesh.set("scale", _scale_xml_vector(mesh.get("scale", "1 1 1"), factors))
        for element in root.findall(".//*[@pos]"):
            element.set("pos", _scale_xml_vector(element.get("pos"), factors))
        for geom in root.findall(".//geom"):
            if geom.get("size"):
                geom.set("size", _scale_xml_vector(geom.get("size"), factors))


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
    if plan.case_id not in {"S06", "S07", "S08", "S09"}:
        return ()
    entities = {**fixtures_dict, **objects_dict}
    changed: list[str] = []
    if plan.case_id == "S06":
        configured = plan.params.get("fixture_geometry_factors")
        factors = (
            tuple(_param_vector(plan.params, "fixture_geometry_factors", (1.12, 1.12, 1.0)))
            if configured is not None
            else (1.12, 1.12, 1.0)
        )
        transforms = {name: factors for name in plan.targets}
    elif plan.case_id == "S07":
        factors = tuple(
            _required_param_vector(plan.params, "geometry_factors", 3)
        )
        if any(float(value) <= 0.0 for value in factors):
            raise PerturbationConfigurationError("S07 geometry_factors must be positive")
        transforms = {name: factors for name in plan.targets}
    elif plan.case_id == "S08":
        configured = plan.params.get("geometry_factors")
        if configured is None:
            factors = (1.35, 0.72, 1.0)
        else:
            factors = tuple(_param_vector(plan.params, "geometry_factors", (1.0, 1.0, 1.0)))
            if any(float(value) <= 0.0 for value in factors):
                raise PerturbationConfigurationError(
                    "S08 geometry_factors must be positive"
                )
        transforms = {name: factors for name in plan.targets}
    else:
        configured_target = plan.params.get("target_geometry_factors")
        configured_receiver = plan.params.get("receiver_geometry_factors")
        target_factors = (
            tuple(_param_vector(plan.params, "target_geometry_factors", (1.12, 1.12, 1.12)))
            if configured_target is not None
            else (1.12, 1.12, 1.12)
        )
        receiver_factors = (
            tuple(_param_vector(plan.params, "receiver_geometry_factors", (0.90, 0.90, 0.90)))
            if configured_receiver is not None
            else (0.90, 0.90, 0.90)
        )
        transforms = {
            name: (target_factors if index == 0 else receiver_factors)
            for index, name in enumerate(plan.targets)
        }
    receiver_name = plan.targets[-1] if plan.case_id == "S09" else None
    goal_region_scale = None
    if plan.case_id == "S07":
        goal_region_scale = tuple(
            _required_param_vector(plan.params, "goal_region_scale", 3)
        )
        if any(float(value) <= 0.0 for value in goal_region_scale):
            raise PerturbationConfigurationError(
                "S07 goal_region_scale must be positive"
            )
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
        if name == receiver_name or plan.case_id == "S07":
            site_factors = goal_region_scale if plan.case_id == "S07" else factors
            for site in obj.worldbody.findall(".//site"):
                if site.get("size"):
                    site.set("size", _scale_xml_vector(site.get("size"), site_factors))
                if plan.case_id == "S07" and site.get("pos"):
                    site.set("pos", _scale_xml_vector(site.get("pos"), site_factors))
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
    # Small test doubles and older wrappers expose only body poses.  In that
    # case the named root is still enough for contact checks; real MuJoCo
    # models provide both fields and continue through articulated descendants.
    if not hasattr(model, "nbody") or not hasattr(model, "body_parentid"):
        return tuple(ids)
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


def _entity_deep_contacts(env: Any, name: str, tolerance: float = 0.002) -> list[dict[str, Any]]:
    """Return contacts penetrating an entity beyond the accepted physics tolerance."""

    body_ids = set(_entity_body_ids(env, name))
    model = env.sim.model
    data = env.sim.data
    contacts: list[dict[str, Any]] = []
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        distance = float(contact.dist)
        if distance >= -float(tolerance):
            continue
        first_body = int(model.geom_bodyid[int(contact.geom1)])
        second_body = int(model.geom_bodyid[int(contact.geom2)])
        if (first_body in body_ids) == (second_body in body_ids):
            continue
        contacts.append(
            {
                "first": str(model.body_id2name(first_body) or ""),
                "second": str(model.body_id2name(second_body) or ""),
                "depth_m": -distance,
            }
        )
    return contacts


def _entity_has_penetrating_contact(
    env: Any, name: str, tolerance: float = 0.002
) -> bool:
    """Compatibility predicate used by scene validation scripts."""

    return bool(_entity_deep_contacts(env, name, tolerance=tolerance))


def _entity_has_support_contact(
    env: Any, name: str, tolerance: float = 0.003
) -> bool:
    """Return whether an entity is in shallow contact with a scene support."""

    body_ids = set(_entity_body_ids(env, name))
    model = env.sim.model
    data = env.sim.data
    support_tokens = (
        "table",
        "floor",
        "stove",
        "plate",
        "basket",
        "rack",
        "cabinet",
        "drawer",
        "counter",
    )
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        if float(contact.dist) > float(tolerance):
            continue
        first_body = int(model.geom_bodyid[int(contact.geom1)])
        second_body = int(model.geom_bodyid[int(contact.geom2)])
        if (first_body in body_ids) == (second_body in body_ids):
            continue
        other_body = second_body if first_body in body_ids else first_body
        try:
            other_name = str(model.body_id2name(other_body) or "").lower()
        except Exception:
            other_name = ""
        if any(token in other_name for token in support_tokens):
            return True
    return False


def _set_entity_pose(
    env: Any, name: str, position: np.ndarray, quaternion: np.ndarray | None = None
) -> None:
    body_id = _entity_body_id(env, name)
    if quaternion is None:
        quaternion = np.asarray(env.sim.data.body_xquat[body_id], dtype=np.float64)
    obj = env.objects_dict.get(name)
    joints = list(getattr(obj, "joints", []) or []) if obj is not None else []
    joint_lookup = getattr(env.sim.model, "joint_name2id", None)
    if callable(joint_lookup):
        valid_joints = []
        for joint in joints:
            try:
                joint_lookup(joint)
            except Exception:
                continue
            valid_joints.append(joint)
        joints = valid_joints
    if joints:
        env.sim.data.set_joint_qpos(
            joints[-1], np.concatenate([np.asarray(position), np.asarray(quaternion)])
        )
    else:
        env.sim.model.body_pos[body_id] = np.asarray(position)
        env.sim.model.body_quat[body_id] = np.asarray(quaternion)
    env.sim.forward()


def _zero_entity_free_joint_velocity(env: Any, name: str) -> str:
    """Stop one movable scene object before and after task-local staging."""

    scene_object = getattr(env, "objects_dict", {}).get(name)
    joints = list(getattr(scene_object, "joints", []) or [])
    model = env.sim.model
    data = env.sim.data
    for joint in joints:
        try:
            joint_id = int(model.joint_name2id(joint))
            joint_type = int(model.jnt_type[joint_id])
        except Exception:
            continue
        if joint_type != 0:
            continue
        setter = getattr(data, "set_joint_qvel", None)
        if callable(setter):
            setter(joint, np.zeros(6, dtype=np.float64))
        else:
            dof_address = int(model.jnt_dofadr[joint_id])
            data.qvel[dof_address : dof_address + 6] = 0.0
        return str(joint)
    raise PerturbationValidationError(
        f"Persistent D03 obstacle {name!r} must have a compiled free joint"
    )


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


def _collision_geom_ids(env: Any, name: str) -> tuple[int, ...]:
    """Return collision geoms attached to an entity, including descendants."""

    body_ids = set(_entity_body_ids(env, name))
    model = env.sim.model
    geom_body_ids = np.asarray(getattr(model, "geom_bodyid", ()), dtype=int)
    geom_groups = np.asarray(
        getattr(model, "geom_group", np.zeros(len(geom_body_ids), dtype=int)),
        dtype=int,
    )
    geom_contype = np.asarray(
        getattr(model, "geom_contype", np.ones(len(geom_body_ids), dtype=int)),
        dtype=int,
    )
    return tuple(
        int(geom_id)
        for geom_id, body_id in enumerate(geom_body_ids)
        if int(body_id) in body_ids
        and int(geom_groups[geom_id]) == 0
        and int(geom_contype[geom_id]) != 0
    )


def _entity_vertical_offsets(env: Any, name: str) -> tuple[float, float]:
    """Return collision AABB bottom/top offsets relative to an entity body."""

    body_id = _entity_body_id(env, name)
    body_z = float(env.sim.data.body_xpos[body_id, 2])
    model = env.sim.model
    data = env.sim.data
    offsets: list[tuple[float, float]] = []
    aabbs = getattr(model, "geom_aabb", None)
    geom_ids = _collision_geom_ids(env, name)
    # Visual-only perturbation assets intentionally disable collisions, but
    # they still need a geometric bottom when they are placed on a table or
    # other support.  Fall back to all attached geoms only when no collision
    # geom is available; this does not alter contact filtering.
    if not geom_ids:
        body_ids = set(_entity_body_ids(env, name))
        geom_body_ids = np.asarray(getattr(model, "geom_bodyid", ()), dtype=int)
        geom_ids = tuple(
            int(geom_id)
            for geom_id, body_id in enumerate(geom_body_ids)
            if int(body_id) in body_ids
        )
    for geom_id in geom_ids:
        try:
            if aabbs is not None:
                rotation = np.asarray(data.geom_xmat[geom_id], dtype=np.float64).reshape(3, 3)
                aabb = np.asarray(aabbs[geom_id], dtype=np.float64).reshape(6)
                center = np.asarray(data.geom_xpos[geom_id], dtype=np.float64) + rotation @ aabb[:3]
                extent = np.abs(rotation) @ aabb[3:]
                offsets.append((float(center[2] - extent[2] - body_z), float(center[2] + extent[2] - body_z)))
                continue
            radius = float(np.asarray(model.geom_rbound)[geom_id])
            center_z = float(data.geom_xpos[geom_id, 2])
            offsets.append((center_z - radius - body_z, center_z + radius - body_z))
        except (AttributeError, IndexError, TypeError, ValueError):
            continue
    if not offsets:
        raise PerturbationValidationError(f"No collision geometry found for {name!r}")
    return min(item[0] for item in offsets), max(item[1] for item in offsets)


def _support_geom_tokens(env: Any, params: dict[str, Any]) -> tuple[str, ...]:
    configured = _name_tuple(params.get("support_surface"))
    if configured:
        tokens = {token.casefold() for token in configured}
        if any("table" in token for token in tokens):
            tokens.add("table")
        # Floor is the canonical support in LIBERO-Object and remains a safe
        # fallback when a table is not present in a task scene.
        tokens.add("floor")
        return tuple(tokens)
    return (
        "table",
        "floor",
        "counter",
        "stove",
        "cabinet",
        "rack",
        "drawer",
        "shelf",
        "tray",
        "plate",
        "basket",
    )


def _support_height_at(
    env: Any,
    candidate_xy: np.ndarray,
    params: dict[str, Any],
    *,
    ignored: tuple[str, ...] = (),
    maximum_height: float | None = None,
) -> tuple[float, str] | None:
    """Find the highest configured support surface beneath a candidate XY."""

    model = env.sim.model
    data = env.sim.data
    ignored_bodies: set[int] = set()
    for name in ignored:
        try:
            ignored_bodies.update(_entity_body_ids(env, name))
        except PerturbationValidationError:
            continue
    tokens = _support_geom_tokens(env, params)
    aabbs = getattr(model, "geom_aabb", None)
    if aabbs is None:
        return None
    candidates: list[tuple[float, str]] = []
    geom_body_ids = np.asarray(getattr(model, "geom_bodyid", ()), dtype=int)
    geom_groups = np.asarray(
        getattr(model, "geom_group", np.zeros(len(geom_body_ids), dtype=int)), dtype=int
    )
    geom_contype = np.asarray(
        getattr(model, "geom_contype", np.ones(len(geom_body_ids), dtype=int)), dtype=int
    )
    for geom_id, body_id in enumerate(geom_body_ids):
        is_floor = "floor" in str(model.body_id2name(int(body_id)) or "").casefold() or "floor" in str(model.geom_id2name(int(geom_id)) or "").casefold()
        if int(body_id) in ignored_bodies or (
            int(geom_groups[geom_id]) != 0 and not is_floor
        ):
            continue
        if int(geom_contype[geom_id]) == 0:
            continue
        try:
            geom_name = str(model.geom_id2name(int(geom_id)) or "").casefold()
            body_name = str(model.body_id2name(int(body_id)) or "").casefold()
            if not any(token in geom_name or token in body_name for token in tokens):
                continue
            rotation = np.asarray(data.geom_xmat[geom_id], dtype=np.float64).reshape(3, 3)
            aabb = np.asarray(aabbs[geom_id], dtype=np.float64).reshape(6)
            center = np.asarray(data.geom_xpos[geom_id], dtype=np.float64) + rotation @ aabb[:3]
            extent = np.abs(rotation) @ aabb[3:]
            if abs(float(candidate_xy[0]) - center[0]) > extent[0] + 0.008:
                continue
            if abs(float(candidate_xy[1]) - center[1]) > extent[1] + 0.008:
                continue
            top = float(center[2] + extent[2])
            if maximum_height is not None and top > maximum_height:
                continue
            candidates.append((top, str(model.geom_id2name(int(geom_id)) or body_name)))
        except (AttributeError, IndexError, TypeError, ValueError):
            continue
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])


def _grounded_entity_position(
    env: Any,
    name: str,
    candidate_xy: np.ndarray,
    params: dict[str, Any],
    *,
    ignored: tuple[str, ...] = (),
    maximum_support_height: float | None = None,
) -> tuple[np.ndarray, str] | None:
    """Place an entity's collision bottom just above a support surface."""

    support = _support_height_at(
        env,
        candidate_xy,
        params,
        ignored=ignored,
        maximum_height=maximum_support_height,
    )
    if support is None:
        return None
    bottom_offset, _ = _entity_vertical_offsets(env, name)
    position = np.zeros(3, dtype=np.float64)
    position[:2] = np.asarray(candidate_xy, dtype=np.float64)
    # Leave a small deterministic clearance for the first forward pass.  The
    # object is free to settle onto the support on the next physics step, while
    # the clearance avoids treating the initial contact solver tolerance as
    # deep penetration.
    position[2] = float(support[0] - bottom_offset + 0.003)
    return position, support[1]


def _support_geom_belongs_to_entity(
    env: Any, support_geom: str, support_entity: str
) -> bool:
    support_body_ids = set(_entity_body_ids(env, support_entity))
    model = env.sim.model
    for geom_id, body_id in enumerate(
        np.asarray(getattr(model, "geom_bodyid", ()), dtype=int)
    ):
        if int(body_id) not in support_body_ids:
            continue
        geom_name = str(model.geom_id2name(int(geom_id)) or "")
        body_name = str(model.body_id2name(int(body_id)) or "")
        if support_geom in {geom_name, body_name}:
            return True
    return False


def _nearby_xy_candidates(candidate_xy: np.ndarray) -> tuple[np.ndarray, ...]:
    """Return deterministic nearby offsets for collision-safe task-local fallback."""

    base = np.asarray(candidate_xy, dtype=np.float64)
    candidates = [base]
    for distance in (0.025, 0.05, 0.075, 0.10, 0.15, 0.20):
        for direction in (
            (1.0, 0.0),
            (-1.0, 0.0),
            (0.0, 1.0),
            (0.0, -1.0),
            (1.0, 1.0),
            (1.0, -1.0),
            (-1.0, 1.0),
            (-1.0, -1.0),
        ):
            vector = np.asarray(direction, dtype=np.float64)
            vector /= np.linalg.norm(vector)
            candidates.append(base + distance * vector)
    return tuple(candidates)


def _support_entity_names(params: dict[str, Any]) -> tuple[str, ...]:
    configured = _name_tuple(params.get("support_surface"))
    names = set(configured)
    for value in configured:
        token = value.casefold()
        if "table" in token:
            names.update(
                {
                    "table",
                    "main_table",
                    "kitchen_table",
                    "living_room_table",
                    "study_table",
                    "coffee_table",
                }
            )
        if "floor" in token:
            names.add("floor")
    return tuple(names)


def _model_named_id(model: Any, kind: str, name: str) -> int:
    method_names = [f"{kind}_name2id", f"{kind}name2id"]
    if kind == "mat":
        method_names.append("material_name2id")
    for method_name in method_names:
        method = getattr(model, method_name, None)
        if callable(method):
            return int(method(name))
    accessor = getattr(model, kind, None)
    if callable(accessor):
        return int(accessor(name).id)
    raise KeyError(name)


def _workspace_visual_geom_ids(env: Any) -> tuple[int, ...]:
    """Resolve the visual-only geom that represents the active work surface."""

    model = env.sim.model
    geom_ids: list[int] = []
    for name in ("workspace_surface_visual", "table_visual"):
        try:
            geom_id = _model_named_id(model, "geom", name)
        except Exception:
            continue
        if geom_id not in geom_ids:
            geom_ids.append(geom_id)
    if geom_ids:
        return tuple(geom_ids)
    if str(getattr(env, "workspace_name", "")) == "floor":
        try:
            return (_model_named_id(model, "geom", "floor"),)
        except Exception:
            return ()

    workspace_body = {
        "main_table": "table",
        "kitchen_table": "table",
        "living_room_table": "living_room_table",
        "study_table": "study_table",
        "coffee_table": "coffee_table",
    }.get(str(getattr(env, "workspace_name", "")))
    if workspace_body is None:
        return ()
    try:
        root_body = int(model.body_name2id(workspace_body))
    except Exception:
        return ()

    descendants = {root_body}
    parent_ids = np.asarray(getattr(model, "body_parentid", ()), dtype=int)
    changed = True
    while changed:
        changed = False
        for body_id, parent_id in enumerate(parent_ids):
            if parent_id in descendants and body_id not in descendants:
                descendants.add(body_id)
                changed = True
    geom_body_ids = np.asarray(getattr(model, "geom_bodyid", ()), dtype=int)
    geom_groups = np.asarray(
        getattr(model, "geom_group", np.zeros(len(geom_body_ids), dtype=int)), dtype=int
    )
    geom_contype = np.asarray(
        getattr(model, "geom_contype", np.zeros(len(geom_body_ids), dtype=int)), dtype=int
    )
    return tuple(
        geom_id
        for geom_id, body_id in enumerate(geom_body_ids)
        if body_id in descendants
        and (geom_groups[geom_id] == 1 or geom_contype[geom_id] == 0)
    )


def _robot_body_ids(env: Any) -> set[int]:
    # Lightweight wrappers used by offline validators may expose only
    # ``sim.data``.  In that case contact-based checks have no robot geometry
    # to inspect and must safely fall back to the distance trigger.
    model = getattr(getattr(env, "sim", None), "model", None)
    if model is None:
        return set()
    robot = env.robots[0]
    root_name = str(getattr(getattr(robot, "robot_model", None), "root_body", ""))
    try:
        root_id = _model_named_id(model, "body", root_name)
    except Exception:
        return set()
    body_ids = {root_id}
    parent_ids = np.asarray(getattr(model, "body_parentid", ()), dtype=int)
    changed = True
    while changed:
        changed = False
        for body_id, parent_id in enumerate(parent_ids):
            if parent_id in body_ids and body_id not in body_ids:
                body_ids.add(body_id)
                changed = True
    return body_ids


def _robot_contacts(env: Any) -> dict[tuple[int, int], float]:
    """Return robot-involved contact distances keyed by the geom pair."""

    model = env.sim.model
    data = env.sim.data
    robot_bodies = _robot_body_ids(env)
    contacts: dict[tuple[int, int], float] = {}
    geom_body_ids = np.asarray(getattr(model, "geom_bodyid", ()), dtype=int)
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        geom1, geom2 = int(contact.geom1), int(contact.geom2)
        if geom1 >= len(geom_body_ids) or geom2 >= len(geom_body_ids):
            continue
        if (
            int(geom_body_ids[geom1]) not in robot_bodies
            and int(geom_body_ids[geom2]) not in robot_bodies
        ):
            continue
        pair = tuple(sorted((geom1, geom2)))
        contacts[pair] = min(float(contact.dist), contacts.get(pair, float("inf")))
    return contacts


def _has_new_robot_penetration(
    before: dict[tuple[int, int], float],
    after: dict[tuple[int, int], float],
    tolerance: float,
) -> bool:
    for pair, distance in after.items():
        if distance >= -tolerance:
            continue
        baseline = before.get(pair)
        if baseline is None or distance < baseline - tolerance:
            return True
    return False


def _arm_joint_limits(model: Any, qpos_indices: list[int]) -> tuple[np.ndarray, np.ndarray]:
    lower = np.full(len(qpos_indices), -np.inf, dtype=np.float64)
    upper = np.full(len(qpos_indices), np.inf, dtype=np.float64)
    qpos_to_joint = {
        int(address): joint_id
        for joint_id, address in enumerate(
            np.asarray(getattr(model, "jnt_qposadr", ()), dtype=int)
        )
    }
    ranges = np.asarray(getattr(model, "jnt_range", ()), dtype=np.float64)
    limited = np.asarray(
        getattr(model, "jnt_limited", np.ones(len(ranges), dtype=int)), dtype=int
    )
    for offset, qpos_index in enumerate(qpos_indices):
        joint_id = qpos_to_joint.get(int(qpos_index))
        if joint_id is None or joint_id >= len(ranges) or not bool(limited[joint_id]):
            continue
        lower[offset], upper[offset] = ranges[joint_id]
    return lower, upper


def _safe_offset_pose(
    env: Any,
    name: str,
    requested: tuple[float, float],
    *,
    minimum_gap: float = 0.08,
    minimum_displacement: float = 0.0,
    baseline_deep_contacts: list[dict[str, Any]] | None = None,
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
        if float(np.linalg.norm(delta)) < float(minimum_displacement):
            continue
        candidate = before.copy()
        candidate[:2] += delta
        if _candidate_is_clear(env, name, candidate[:2], minimum_gap, ignored):
            _set_entity_pose(env, name, candidate, quat)
            if baseline_deep_contacts is not None:
                baseline_depths = {
                    (str(item["first"]), str(item["second"])): float(item["depth_m"])
                    for item in baseline_deep_contacts
                }
                invalid_contacts = []
                for item in _entity_deep_contacts(env, name):
                    pair = (str(item["first"]), str(item["second"]))
                    previous_depth = baseline_depths.get(pair)
                    if previous_depth is None or float(item["depth_m"]) > previous_depth + 0.002:
                        invalid_contacts.append(item)
                if invalid_contacts:
                    _set_entity_pose(env, name, before, quat)
                    continue
            return before, candidate, delta
    raise PerturbationValidationError(
        f"No collision-clear workspace position for {name!r} near {before[:2].tolist()}"
    )


def _safe_dynamic_asset_pose(
    env: Any,
    name: str,
    requested_position: np.ndarray,
    quaternion: np.ndarray,
    params: dict[str, Any],
    *,
    ignored: tuple[str, ...] = (),
) -> tuple[np.ndarray, str | None]:
    """Place a staged asset without embedding it in another scene entity."""

    requested = np.asarray(requested_position, dtype=np.float64).copy()
    original, original_quat = _entity_pose(env, name)
    placement_ignored = tuple(ignored)
    if _param_bool(params, "allow_goal_overlap", False):
        placement_ignored = tuple(
            dict.fromkeys((*placement_ignored, *_goal_interaction_targets(env)))
        )
    declared_supports = set(_name_tuple(params.get("support_surface")))
    support_ignored = tuple(
        name for name in placement_ignored if name not in declared_supports
    )
    for candidate_xy in _nearby_xy_candidates(requested[:2]):
        grounded = _grounded_entity_position(
            env,
            name,
            candidate_xy,
            params,
            ignored=(name, *support_ignored),
        )
        candidate = requested.copy()
        support_geom: str | None = None
        if grounded is not None:
            candidate, support_geom = grounded
            # A functional anchor may be above the work surface (e.g. a
            # cabinet knob).  Preserve that height when it is intentionally
            # above the best support, but never lower below the support.
            candidate[2] = max(candidate[2], requested[2])
        if not _candidate_is_clear(
            env, name, candidate[:2], 0.018, ignored=(name, *placement_ignored)
        ):
            continue
        _set_entity_pose(env, name, candidate, quaternion)
        if _entity_deep_contacts(env, name, tolerance=0.0015):
            _set_entity_pose(env, name, original, original_quat)
            continue
        return candidate, support_geom
    _set_entity_pose(env, name, original, original_quat)
    raise PerturbationValidationError(
        f"No collision-clear dynamic asset position for {name!r} near {requested[:2].tolist()}"
    )


def _dynamic_pose_requested_delta(
    case_id: str, target: str, params: dict[str, Any] | None = None
) -> tuple[float, float]:
    if case_id == "D19":
        configured = _required_param_vector(
            params or {}, "misplace_offset_xy", 2
        )
    else:
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
        "D06": (0.12, -0.09),
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


def _functional_anchor(
    env: Any, entity_name: str, configured_anchor: str | None = None
) -> tuple[np.ndarray, str]:
    """Return the task-relevant site on an entity, falling back to its body."""
    sites = getattr(env, "object_sites_dict", {})
    if configured_anchor:
        site = sites.get(configured_anchor)
        region = (
            getattr(env, "parsed_problem", {})
            .get("regions", {})
            .get(configured_anchor, {})
        )
        site_parent = (
            getattr(site, "parent_name", None) if site is not None else None
        )
        region_target = region.get("target") if isinstance(region, dict) else None
        if site is None or (site_parent != entity_name and region_target != entity_name):
            raise PerturbationConfigurationError(
                f"receiver_anchor {configured_anchor!r} does not belong to {entity_name!r}"
            )
        try:
            return (
                np.asarray(
                    env.sim.data.get_site_xpos(configured_anchor), dtype=np.float64
                ).copy(),
                configured_anchor,
            )
        except Exception as exc:
            raise PerturbationValidationError(
                f"receiver_anchor {configured_anchor!r} is unavailable"
            ) from exc
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


def _goal_path_anchor_candidates(
    env: Any,
) -> tuple[tuple[str, np.ndarray, str, np.ndarray], ...]:
    """Resolve every object-to-receiver path in a multi-object goal.

    Dynamic occupancy and barrier events must also trigger when the policy
    transports the second object in a task.  The legacy helper intentionally
    returns the first goal only, so this task-local expansion keeps existing
    behavior for single-object tasks while covering all declared goals.
    """

    sites = getattr(env, "object_sites_dict", {})
    candidates: list[tuple[str, np.ndarray, str, np.ndarray]] = []
    for state in getattr(env, "parsed_problem", {}).get("goal_state", []):
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
        target_name = str(state[1])
        target, _ = _entity_pose(env, target_name)
        receiver, anchor_name = _functional_anchor(env, receiver_name)
        candidate = (target_name, target, anchor_name, receiver)
        if not any(existing[0] == target_name for existing in candidates):
            candidates.append(candidate)
    return tuple(candidates)


def _goal_path_receiver_for_target(
    env: Any, target_name: str
) -> tuple[str, np.ndarray, str]:
    """Resolve the receiver and functional anchor for one declared goal."""

    sites = getattr(env, "object_sites_dict", {})
    regions = getattr(env, "parsed_problem", {}).get("regions", {})
    for state in getattr(env, "parsed_problem", {}).get("goal_state", []):
        if len(state) < 3 or str(state[1]) != str(target_name):
            continue
        site_name = str(state[2])
        site = sites.get(site_name)
        receiver_name = getattr(site, "parent_name", None) if site is not None else None
        region = regions.get(site_name, {})
        if receiver_name is None and isinstance(region, dict):
            receiver_name = region.get("target")
        if receiver_name is None and _entity_exists(env, site_name):
            receiver_name = site_name
        if receiver_name is None or not _entity_exists(env, receiver_name):
            break
        receiver, anchor_name = _functional_anchor(env, str(receiver_name))
        return str(receiver_name), receiver, anchor_name
    raise PerturbationValidationError(
        f"Cannot resolve a receiver for goal target {target_name!r}"
    )


def _eef_target_contact(env: Any, target: str, tolerance: float = 0.004) -> bool:
    """Return true when robot collision geometry touches the target."""

    if not _entity_exists(env, target):
        return False
    robot_bodies = _robot_body_ids(env)
    if not robot_bodies:
        return False
    target_bodies = set(_entity_body_ids(env, target))
    model = getattr(getattr(env, "sim", None), "model", None)
    data = getattr(getattr(env, "sim", None), "data", None)
    if model is None or data is None:
        return False
    geom_body_ids = np.asarray(getattr(model, "geom_bodyid", ()), dtype=int)
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        first_body = int(geom_body_ids[int(contact.geom1)])
        second_body = int(geom_body_ids[int(contact.geom2)])
        if not (
            (first_body in robot_bodies and second_body in target_bodies)
            or (second_body in robot_bodies and first_body in target_bodies)
        ):
            continue
        if float(contact.dist) <= float(tolerance):
            return True
    return False


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
        self.observation_queue: deque[dict[str, Any]] = deque(maxlen=64)
        self.action_queue: deque[np.ndarray] = deque(maxlen=64)
        self.gripper_queue: deque[float] = deque(maxlen=64)
        self._delayed_action_history: deque[np.ndarray] = deque(maxlen=64)
        self._delayed_gripper_history: deque[float] = deque(maxlen=64)
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
        self._initial_eef_position: np.ndarray | None = None
        self._staged_persistent_obstacle: tuple[
            str,
            tuple[tuple[int, float], ...],
            tuple[tuple[int, int, int], ...],
        ] | None = None
        self._dynamic_active_goal_target: str | None = None
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
            "body_gravcomp",
            "cam_pos",
            "cam_quat",
            "cam_fovy",
            "geom_rgba",
            "geom_matid",
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
        self._initial_eef_position = None
        self._staged_persistent_obstacle = None
        self._dynamic_active_goal_target = None

    def _clear_temporal_state(self) -> None:
        self.previous_action = None
        self.previous_gripper_force = None
        self.previous_observation = None
        self.observation_queue.clear()
        self.action_queue.clear()
        self.gripper_queue.clear()
        self._delayed_action_history.clear()
        self._delayed_gripper_history.clear()
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

        persistent_obstacle = self._persistent_d03_obstacle_name()
        if self._staged_persistent_obstacle is not None:
            self._restore_staged_persistent_obstacle_physics(env)
        if self._dynamic_applied or persistent_obstacle is not None:
            for name, (position, quaternion) in self._saved_poses.items():
                if _entity_exists(env, name):
                    _set_entity_pose(env, name, position, quaternion)
        self.reset()
        self._stage_dynamic_assets(env)
        persistent_obstacle = self._persistent_d03_obstacle_name()
        if persistent_obstacle is not None:
            self._stage_persistent_obstacle(env, persistent_obstacle)
        if self.plan.case_id == "D20":
            try:
                self._initial_eef_position = np.asarray(
                    env.sim.data.site_xpos[env.robots[0].eef_site_id],
                    dtype=np.float64,
                ).copy()
            except Exception as exc:
                raise PerturbationValidationError(
                    "D20 requires a valid robot end-effector site"
                ) from exc

    def _persistent_d03_obstacle_name(self) -> str | None:
        if self.plan.case_id != "D03":
            return None
        if _param_bool(self.plan.params, "persistent_existing_obstacle", False):
            if len(self.plan.references) != 1:
                raise PerturbationConfigurationError(
                    "D03 persistent_existing_obstacle requires exactly one existing reference"
                )
            return self.plan.references[0]
        if _param_bool(self.plan.params, "persistent_movable_asset", False):
            if len(self.plan.assets) != 1:
                raise PerturbationConfigurationError(
                    "D03 persistent_movable_asset requires exactly one injected asset"
                )
            return _injected_name(self.plan)
        return None

    def _d03_receiver_selection(self) -> str:
        """Return the explicitly configured D03 receiver-selection mode."""

        mode = str(self.plan.params.get("receiver_selection", "configured_target"))
        normalized = mode.strip().casefold()
        if normalized not in {"configured_target", "active_goal_path"}:
            raise PerturbationConfigurationError(
                "D03 receiver_selection must be configured_target or active_goal_path"
            )
        return normalized

    def _restore_staged_persistent_obstacle_physics(self, env: Any) -> None:
        state = self._staged_persistent_obstacle
        if state is None:
            return
        _, gravcomp, contact_masks = state
        model = env.sim.model
        values = getattr(model, "body_gravcomp", None)
        if values is not None:
            for body_id, value in gravcomp:
                values[body_id] = value
        contype = getattr(model, "geom_contype", None)
        conaffinity = getattr(model, "geom_conaffinity", None)
        if contype is not None and conaffinity is not None:
            for geom_id, original_contype, original_conaffinity in contact_masks:
                contype[geom_id] = original_contype
                conaffinity[geom_id] = original_conaffinity
        self._staged_persistent_obstacle = None
        env.sim.forward()

    def _stage_persistent_obstacle(self, env: Any, obstacle: str) -> None:
        if not _entity_exists(env, obstacle):
            raise PerturbationValidationError(
                f"Persistent D03 obstacle {obstacle!r} is absent from the scene"
            )
        _zero_entity_free_joint_velocity(env, obstacle)
        gravcomp_values = getattr(env.sim.model, "body_gravcomp", None)
        if gravcomp_values is None:
            raise PerturbationValidationError(
                "Persistent D03 staging requires MuJoCo body_gravcomp"
            )
        gravcomp = tuple(
            (body_id, float(gravcomp_values[body_id]))
            for body_id in _entity_body_ids(env, obstacle)
        )
        body_ids = set(_entity_body_ids(env, obstacle))
        model = env.sim.model
        contype = getattr(model, "geom_contype", None)
        conaffinity = getattr(model, "geom_conaffinity", None)
        if contype is None or conaffinity is None:
            raise PerturbationValidationError(
                "Persistent D03 staging requires MuJoCo contact masks"
            )
        contact_masks = tuple(
            (
                geom_id,
                int(contype[geom_id]),
                int(conaffinity[geom_id]),
            )
            for geom_id in range(int(model.ngeom))
            if int(model.geom_bodyid[geom_id]) in body_ids
        )
        if not any(
            mask != 0 and affinity != 0
            for _, mask, affinity in contact_masks
        ):
            raise PerturbationValidationError(
                f"Persistent D03 obstacle {obstacle!r} must have collision geometry"
            )
        for body_id, _ in gravcomp:
            gravcomp_values[body_id] = 1.0
        for geom_id, _, _ in contact_masks:
            contype[geom_id] = 0
            conaffinity[geom_id] = 0
        self._staged_persistent_obstacle = (obstacle, gravcomp, contact_masks)
        _, quaternion = self._saved_poses[obstacle]
        staging_position = _required_param_vector(
            self.plan.params, "staging_position_xyz", 3
        )
        try:
            _set_entity_pose(env, obstacle, staging_position, quaternion)
            _zero_entity_free_joint_velocity(env, obstacle)
        except Exception:
            self._restore_staged_persistent_obstacle_physics(env)
            raise

    def _enter_persistent_obstacle(self, env: Any, step: int) -> None:
        state = self._staged_persistent_obstacle
        if state is None:
            raise PerturbationValidationError(
                "Persistent D03 obstacle was not staged before its trigger"
            )
        obstacle, gravcomp, contact_masks = state
        selection = self._d03_receiver_selection()
        selected_goal_target = None
        if selection == "active_goal_path":
            selected_goal_target = self._dynamic_active_goal_target
            if selected_goal_target is None:
                raise PerturbationValidationError(
                    "D03 active_goal_path receiver was not selected before trigger"
                )
            receiver, requested_position, anchor_name = _goal_path_receiver_for_target(
                env, selected_goal_target
            )
        else:
            receiver = self.plan.targets[0] if self.plan.targets else None
            if receiver is None or not _entity_exists(env, receiver):
                raise PerturbationValidationError(
                    "Persistent D03 obstacle has no valid receiver"
                )
            configured_anchors = _name_tuple(self.plan.params.get("receiver_anchor"))
            if len(configured_anchors) > 1:
                raise PerturbationConfigurationError(
                    "D03 receiver_anchor must name at most one site"
                )
            requested_position, anchor_name = _functional_anchor(
                env,
                receiver,
                configured_anchors[0] if configured_anchors else None,
            )
        requested_position += _param_vector(
            self.plan.params, "asset_offset_xyz", (0.0, 0.0, 0.0)
        )
        _, quaternion = self._saved_poses[obstacle]
        gravcomp_values = env.sim.model.body_gravcomp
        for body_id, value in gravcomp:
            gravcomp_values[body_id] = value
        contype = env.sim.model.geom_contype
        conaffinity = env.sim.model.geom_conaffinity
        for geom_id, original_contype, original_conaffinity in contact_masks:
            contype[geom_id] = original_contype
            conaffinity[geom_id] = original_conaffinity
        try:
            placement_ignored = (receiver,)
            if selected_goal_target is not None:
                # The carried goal object is above the receiver during the
                # pre-place event; it must not force the persistent obstacle
                # outside the receiver's footprint.
                placement_ignored = (receiver, selected_goal_target)
            position, support_geom = _safe_dynamic_asset_pose(
                env,
                obstacle,
                requested_position,
                quaternion,
                self.plan.params,
                ignored=placement_ignored,
            )
        except Exception:
            for body_id, _ in gravcomp:
                gravcomp_values[body_id] = 1.0
            for geom_id, _, _ in contact_masks:
                contype[geom_id] = 0
                conaffinity[geom_id] = 0
            staging_position = _required_param_vector(
                self.plan.params, "staging_position_xyz", 3
            )
            _set_entity_pose(env, obstacle, staging_position, quaternion)
            _zero_entity_free_joint_velocity(env, obstacle)
            raise
        _zero_entity_free_joint_velocity(env, obstacle)
        self._staged_persistent_obstacle = None
        self._dynamic_event_step = int(step)
        self._dynamic_applied = True
        self._dynamic_restored = True
        details = {
            "obstacle": obstacle,
            "receiver": receiver,
            "anchor": anchor_name,
            "position": position.tolist(),
            "support_geom": support_geom,
        }
        if selected_goal_target is not None:
            details["goal_target"] = selected_goal_target
        self._log_once("persistent_dynamic_obstacle_entered", step, **details)

    def _maintain_staged_persistent_obstacle(self, env: Any) -> None:
        state = self._staged_persistent_obstacle
        if state is None:
            return
        obstacle, _, _ = state
        _, quaternion = self._saved_poses[obstacle]
        staging_position = _required_param_vector(
            self.plan.params, "staging_position_xyz", 3
        )
        _set_entity_pose(env, obstacle, staging_position, quaternion)
        _zero_entity_free_joint_velocity(env, obstacle)

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
        if self.plan.case_id == "D15":
            _, stale_steps = self._d15_chunk_config()
            return stale_steps
        default_duration = {
            "D14": 1,
            "D16": 6,
            "D17": 40,
        }.get(self.plan.case_id, self.EVENT_END - self.EVENT_START)
        duration_key = "event_duration_steps"
        if self.plan.case_id == "D16" and "takeover_duration_steps" in self.plan.params:
            duration_key = "takeover_duration_steps"
        try:
            return max(
                1,
                int(self.plan.params.get(duration_key, default_duration)),
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

    def _receiver_trigger_distance_m(self, case_id: str) -> float:
        """Return the task-local receiver approach threshold without changing defaults."""

        default = 0.18 if case_id == "D05" else 0.16
        threshold = _param_float(
            self.plan.params, "receiver_trigger_distance_m", default
        )
        if threshold <= 0.0:
            raise PerturbationConfigurationError(
                f"{case_id} receiver_trigger_distance_m must be positive"
            )
        return threshold

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
            params = self.plan.params
            fov_scale = _param_float(params, "fov_scale", 1.12)
            shift_xy = _param_vector(params, "image_shift_xy", (0.05, -0.05))
            crop_ratio = _param_float(params, "crop_ratio", 0.0)
            distortion_strength = _param_float(
                params, "distortion_strength", 0.0
            )
            if fov_scale <= 0.0:
                raise PerturbationConfigurationError("S16 fov_scale must be positive")
            if not 0.0 <= crop_ratio < 1.0:
                raise PerturbationConfigurationError(
                    "S16 crop_ratio must be in the interval [0, 1)"
                )
            for key in image_keys:
                value = out[key]
                if value.ndim >= 2:
                    out[key] = _transform_image_geometry(
                        value, shift_xy, crop_ratio, distortion_strength
                    )
            self._log_once(
                "intrinsics_distortion",
                step,
                fov_scale=fov_scale,
                image_shift_xy=shift_xy.tolist(),
                crop_ratio=crop_ratio,
                distortion_strength=distortion_strength,
            )
        elif case_id == "S18":
            params = self.plan.params
            eef_offset = _required_param_vector(params, "eef_offset_xyz", 3)
            joint_offset = _required_param_vector(
                params, "joint_zero_offset_rad", 3
            )
            grasp_offset = _required_param_vector(
                params, "grasp_center_offset_xyz", 3
            )
            applied_offsets: dict[str, list[float]] = {}
            for key, value in list(out.items()):
                if not isinstance(value, np.ndarray) or (
                    "eef_pos" not in key and "joint_pos" not in key
                ):
                    continue
                source = (
                    eef_offset + grasp_offset if "eef_pos" in key else joint_offset
                )
                offset = np.zeros_like(value, dtype=np.float64)
                offset.flat[: min(source.size, offset.size)] = source[
                    : min(source.size, offset.size)
                ]
                out[key] = value + offset
                applied_offsets[key] = offset.tolist()
            if not applied_offsets:
                raise PerturbationValidationError(
                    "S18 requires eef_pos or joint_pos state in the observation"
                )
            self._log_once(
                "calibration_offset",
                step,
                eef_offset_xyz=eef_offset.tolist(),
                joint_zero_offset_rad=joint_offset.tolist(),
                grasp_center_offset_xyz=grasp_offset.tolist(),
                applied_offsets=applied_offsets,
            )
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
            lighting_factor = _param_float(
                self.plan.params, "lighting_factor", 0.48
            )
            if not 0.0 < lighting_factor <= 1.0:
                raise PerturbationConfigurationError(
                    "D09 lighting_factor must be in the interval (0, 1]"
                )
            exposure_values: dict[str, dict[str, float]] = {}
            for key in image_keys:
                value = out[key]
                if np.issubdtype(value.dtype, np.integer):
                    transformed = np.clip(
                        value.astype(np.float32) * lighting_factor,
                        0,
                        255,
                    ).astype(value.dtype)
                    out[key] = transformed
                    applied_value = {
                        "before_mean": float(np.mean(value)),
                        "after_mean": float(np.mean(transformed)),
                        "factor": float(lighting_factor),
                    }
                else:
                    applied_value = {
                        "before_mean": float(np.mean(value)),
                        "after_mean": float(np.mean(value)),
                        "factor": float(lighting_factor),
                    }
                exposure_values[key] = applied_value
            self._log_once(
                "exposure_change",
                step,
                lighting_factor=lighting_factor,
                requested_value={"lighting_factor": float(lighting_factor)},
                applied_value=exposure_values,
            )
        elif case_id == "D10":
            if self._event_active(step) and self.previous_observation:
                for key in image_keys:
                    if key in self.previous_observation:
                        out[key] = self.previous_observation[key].copy()
                self._log_once("frame_freeze", step)
        elif case_id == "D11":
            if self._event_active(step) and self.previous_observation:
                configured = self.plan.params.get("freeze_modalities")
                if configured is None:
                    modalities = {"all"}
                elif isinstance(configured, (list, tuple)):
                    modalities = {str(item).strip().lower() for item in configured}
                else:
                    modalities = {str(configured).strip().lower()}
                if not modalities:
                    modalities = {"all"}

                def should_freeze(key: str) -> bool:
                    normalized = key.lower()
                    if "all" in modalities or "*" in modalities:
                        return True
                    if normalized in modalities:
                        return True
                    if "rgb" in modalities and normalized.endswith("_image"):
                        return True
                    if "depth" in modalities and normalized.endswith("_depth"):
                        return True
                    if "state" in modalities and not (
                        normalized.endswith("_image")
                        or normalized.endswith("_depth")
                    ):
                        return True
                    return False

                frozen_keys: list[str] = []
                for key, value in list(out.items()):
                    if (
                        key in self.previous_observation
                        and isinstance(value, np.ndarray)
                        and should_freeze(key)
                    ):
                        out[key] = self.previous_observation[key].copy()
                        frozen_keys.append(key)
                self._log_once(
                    "modality_state_freeze",
                    step,
                    freeze_modalities=sorted(modalities),
                    frozen_keys=frozen_keys,
                )
        elif case_id in {"S20", "D12"}:
            default_delay = 1 if case_id == "S20" else 2
            configured_delay = _param_int(
                self.plan.params, "delay_steps", default_delay
            )
            if configured_delay < 0:
                raise PerturbationConfigurationError(
                    f"{case_id} delay_steps must be non-negative"
                )
            delay = configured_delay if case_id == "S20" else (
                configured_delay if self._event_active(step) else 0
            )
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
            delay = _param_int(self.plan.params, "delay_steps", 1)
            if delay < 0:
                raise PerturbationConfigurationError("S20 delay_steps must be non-negative")
            self.action_queue.append(current.copy())
            if delay and len(self.action_queue) > delay:
                current = list(self.action_queue)[-delay - 1].copy()
                self._log_once("fixed_action_delay", step, delay_steps=delay)
        elif case_id == "D13":
            arm_delay = _param_int(self.plan.params, "arm_delay_steps", 1)
            gripper_delay = _param_int(self.plan.params, "gripper_delay_steps", 0)
            if arm_delay < 0 or gripper_delay < 0:
                raise PerturbationConfigurationError(
                    "D13 arm_delay_steps and gripper_delay_steps must be non-negative"
                )
            self._delayed_action_history.append(current.copy())
            if self._event_active(step) and current.size > 1 and arm_delay:
                history = list(self._delayed_action_history)
                if len(history) > arm_delay:
                    delayed = history[-arm_delay - 1]
                    current[:-1] = delayed[:-1]
                    self._log_once(
                        "arm_gripper_desynchronization",
                        step,
                        arm_delay_steps=arm_delay,
                        gripper_delay_steps=gripper_delay,
                    )
        elif case_id == "D14" and self._event_active(step) and previous is not None:
            drop_count = _param_int(self.plan.params, "drop_count", 1)
            repeat_count = _param_int(self.plan.params, "repeat_count", 1)
            if drop_count < 0 or repeat_count < 0:
                raise PerturbationConfigurationError(
                    "D14 drop_count and repeat_count must be non-negative"
                )
            elapsed = step - int(self._dynamic_event_step)
            if drop_count + repeat_count > 0 and elapsed < drop_count + repeat_count:
                current = previous
                self._log_once(
                    "command_drop_repeat",
                    step,
                    drop_count=drop_count,
                    repeat_count=repeat_count,
                )
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
            takeover = _param_action_vector(
                self.plan.params, "takeover_action", (0.12,)
            )
            if takeover.size > current.size:
                raise PerturbationConfigurationError(
                    "D16 takeover_action cannot exceed the action size"
                )
            current[:] = 0.0
            current[: takeover.size] = takeover
            self._log_once(
                "bounded_action_takeover",
                step,
                takeover_action=current.tolist(),
                takeover_duration_steps=self._event_duration_steps(),
            )
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

        if case_id == "S20":
            delay = _param_int(self.plan.params, "delay_steps", 1)
            if delay < 0:
                raise PerturbationConfigurationError("S20 delay_steps must be non-negative")
            self._delayed_gripper_history.append(current)
            if delay and len(self._delayed_gripper_history) > delay:
                current = list(self._delayed_gripper_history)[-delay - 1]
        elif case_id == "D13":
            gripper_delay = _param_int(self.plan.params, "gripper_delay_steps", 0)
            if gripper_delay < 0:
                raise PerturbationConfigurationError(
                    "D13 gripper_delay_steps must be non-negative"
                )
            self._delayed_gripper_history.append(current)
            if self._event_active(step) and gripper_delay:
                history = list(self._delayed_gripper_history)
                if len(history) > gripper_delay:
                    current = history[-gripper_delay - 1]
        elif case_id == "D14" and self._event_active(step) and previous is not None:
            drop_count = _param_int(self.plan.params, "drop_count", 1)
            repeat_count = _param_int(self.plan.params, "repeat_count", 1)
            if drop_count < 0 or repeat_count < 0:
                raise PerturbationConfigurationError(
                    "D14 drop_count and repeat_count must be non-negative"
                )
            elapsed = step - int(self._dynamic_event_step)
            if drop_count + repeat_count > 0 and elapsed < drop_count + repeat_count:
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
            value = str(
                self.plan.params.get("value", "Please_continue")
            ).replace("_", " ").strip()
            if not value:
                raise PerturbationConfigurationError("D21 needs a non-empty language value")
            self._log_once("runtime_language_clarification", step)
            if "{instruction}" in value:
                return value.replace("{instruction}", original)
            return f"{value}: {original}"
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

    def _apply_workspace_texture(self, env: Any) -> None:
        material_name = str(self.plan.params.get("material_id", "s22_table_texture"))
        try:
            material_id = _model_named_id(env.sim.model, "mat", material_name)
        except Exception as exc:
            raise PerturbationValidationError(
                f"S22 material {material_name!r} is not compiled into the scene"
            ) from exc
        geom_ids = _workspace_visual_geom_ids(env)
        if not geom_ids:
            raise PerturbationValidationError(
                f"S22 found no visual work-surface geom for "
                f"{getattr(env, 'workspace_name', None)!r}"
            )
        env.sim.model.geom_matid[list(geom_ids)] = material_id
        env.sim.forward()
        self._log_once(
            "workspace_texture_replaced",
            0,
            material=material_name,
            visual_geom_ids=list(geom_ids),
        )

    def _apply_safe_robot_displacement(self, env: Any, step: int) -> None:
        robot = env.robots[0]
        qpos_indices = [int(index) for index in robot._ref_joint_pos_indexes]
        qvel_indices = [int(index) for index in robot._ref_joint_vel_indexes]
        if not qpos_indices:
            raise PerturbationValidationError("D20 robot has no controllable arm joints")

        data = env.sim.data
        before_qpos = np.asarray(data.qpos[qpos_indices], dtype=np.float64).copy()
        before_qvel = np.asarray(data.qvel[qvel_indices], dtype=np.float64).copy()
        before_eef = np.asarray(
            data.site_xpos[robot.eef_site_id], dtype=np.float64
        ).copy()
        baseline_contacts = _robot_contacts(env)
        lower, upper = _arm_joint_limits(env.sim.model, qpos_indices)
        magnitude = float(self.plan.params.get("joint_delta_rad", 0.10))
        min_displacement = float(
            self.plan.params.get("min_eef_displacement_m", 0.035)
        )
        contact_tolerance = abs(
            float(self.plan.params.get("penetration_tolerance_m", 0.001))
        )
        clearance = float(self.plan.params.get("min_workspace_clearance_m", 0.035))
        workspace_offset = np.asarray(
            getattr(env, "workspace_offset", (0.0, 0.0, 0.0)), dtype=np.float64
        )
        workspace_z = float(workspace_offset[2]) if workspace_offset.size >= 3 else 0.0

        patterns: list[np.ndarray] = []
        for joint_offset in range(min(4, len(qpos_indices))):
            for sign in (1.0, -1.0):
                delta = np.zeros(len(qpos_indices), dtype=np.float64)
                delta[joint_offset] = sign * magnitude
                patterns.append(delta)
        if len(qpos_indices) >= 3:
            for sign in (1.0, -1.0):
                delta = np.zeros(len(qpos_indices), dtype=np.float64)
                delta[0] = sign * magnitude
                delta[2] = -sign * magnitude * 0.5
                patterns.append(delta)

        try:
            for candidate_index, delta in enumerate(patterns):
                candidate = before_qpos + delta
                if not np.all(np.isfinite(candidate)):
                    continue
                if np.any(candidate < lower + 1e-5) or np.any(
                    candidate > upper - 1e-5
                ):
                    continue
                data.qpos[qpos_indices] = candidate
                data.qvel[qvel_indices] = 0.0
                env.sim.forward()
                after_eef = np.asarray(
                    data.site_xpos[robot.eef_site_id], dtype=np.float64
                ).copy()
                if not np.all(np.isfinite(after_eef)):
                    continue
                displacement = float(np.linalg.norm(after_eef - before_eef))
                if (
                    displacement < min_displacement
                    or after_eef[2] < workspace_z + clearance
                ):
                    continue
                if hasattr(data, "site_xmat"):
                    orientation = np.asarray(
                        data.site_xmat[robot.eef_site_id], dtype=np.float64
                    ).reshape(3, 3)
                    if not np.all(np.isfinite(orientation)) or not np.isclose(
                        np.linalg.det(orientation), 1.0, atol=0.08
                    ):
                        continue
                candidate_contacts = _robot_contacts(env)
                if _has_new_robot_penetration(
                    baseline_contacts, candidate_contacts, contact_tolerance
                ):
                    continue
                self._log_once(
                    "robot_collision_displacement",
                    step,
                    candidate_index=candidate_index,
                    joint_delta_rad=delta.tolist(),
                    eef_before=before_eef.tolist(),
                    eef_after=after_eef.tolist(),
                    eef_displacement_m=displacement,
                )
                return
        except Exception:
            data.qpos[qpos_indices] = before_qpos
            data.qvel[qvel_indices] = before_qvel
            env.sim.forward()
            raise

        data.qpos[qpos_indices] = before_qpos
        data.qvel[qvel_indices] = before_qvel
        env.sim.forward()
        raise PerturbationValidationError(
            "No collision-free D20 robot displacement satisfies the configured limits"
        )

    def apply_static(self, env: Any) -> None:
        case_id = self.plan.case_id
        if not case_id.startswith("S"):
            self._stage_dynamic_assets(env)
            return

        if case_id in {"S01", "S02"}:
            target = self.plan.targets[0]
            before, original_quat = _entity_pose(env, target)
            requested_offset = _param_vector(
                self.plan.params,
                "offset_xy",
                (0.075, 0.045),
            )
            _, after, delta = _safe_offset_pose(
                env, target, tuple(float(value) for value in requested_offset), ignored=self.plan.targets
            )
            if _param_bool(self.plan.params, "grounded_pose", False):
                grounded = _grounded_entity_position(
                    env,
                    target,
                    after[:2],
                    self.plan.params,
                    ignored=(target,),
                )
                if grounded is None:
                    raise PerturbationValidationError(
                        f"{case_id} grounded pose for {target!r} has no declared support"
                    )
                after, support_geom = grounded
                self._log_once(
                    "static_pose_grounded",
                    0,
                    target=target,
                    support_geom=support_geom,
                    position=after.tolist(),
                )
            yaw = _param_float(
                self.plan.params,
                "yaw_rad",
                0.32 if case_id == "S01" else -0.24,
            )
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
            if first == second:
                raise PerturbationConfigurationError(
                    "S04 planar position swap requires two distinct task targets"
                )
            first_position, first_quaternion = _entity_pose(env, first)
            second_position, second_quaternion = _entity_pose(env, second)
            swap_offset = _param_vector(
                self.plan.params, "swap_xy", (0.0, 0.0)
            )
            grounded_swap = _param_bool(self.plan.params, "grounded_swap", False)
            if grounded_swap:
                support_params = self.plan.params
                support_ignored = (first, second, *_support_entity_names(self.plan.params))
                grounding_ignored = support_ignored
                if _param_bool(
                    self.plan.params, "ground_support_from_declared_surface", False
                ):
                    # Keep support entities ignored for center-distance collision
                    # checks, while allowing the declared collision geometry to
                    # provide the grounding height.
                    grounding_ignored = (first, second)
                if _param_bool(self.plan.params, "strict_swap_xy", False):
                    candidates = (
                        (
                            second_position[:2] + swap_offset,
                            first_position[:2] - swap_offset,
                        ),
                    )
                else:
                    midpoint = 0.5 * (first_position[:2] + second_position[:2])
                    direction = second_position[:2] - first_position[:2]
                    distance = float(np.linalg.norm(direction))
                    direction = (
                        direction / distance
                        if distance >= 1e-6
                        else np.array([1.0, 0.0], dtype=np.float64)
                    )
                    radius = _param_float(
                        self.plan.params,
                        "swap_cluster_radius_m",
                        min(max(distance * 0.25, 0.06), 0.12),
                    )
                    if radius <= 0.02:
                        raise PerturbationConfigurationError(
                            "S04 swap_cluster_radius_m must be greater than 0.02 m"
                        )
                    first_xy = midpoint + direction * (radius * 0.5) + swap_offset
                    second_xy = midpoint - direction * (radius * 0.5) - swap_offset
                    candidates = tuple(
                        (left, right)
                        for left, right in zip(
                            _nearby_xy_candidates(first_xy),
                            _nearby_xy_candidates(second_xy),
                        )
                    )
                selected: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str, str] | None = None
                for first_xy_candidate, second_xy_candidate in candidates:
                    first_grounded = _grounded_entity_position(
                        env,
                        first,
                        first_xy_candidate,
                        support_params,
                        ignored=grounding_ignored,
                    )
                    second_grounded = _grounded_entity_position(
                        env,
                        second,
                        second_xy_candidate,
                        support_params,
                        ignored=grounding_ignored,
                    )
                    if first_grounded is None or second_grounded is None:
                        continue
                    first_after, first_support = first_grounded
                    second_after, second_support = second_grounded
                    if _param_bool(
                        self.plan.params,
                        "preserve_swapped_support_heights",
                        False,
                    ):
                        first_after = first_after.copy()
                        second_after = second_after.copy()
                        first_after[2] = second_position[2]
                        second_after[2] = first_position[2]
                    if not _candidate_is_clear(
                        env, first, first_after[:2], 0.02, ignored=support_ignored
                    ) or not _candidate_is_clear(
                        env, second, second_after[:2], 0.02, ignored=support_ignored
                    ):
                        continue
                    if float(np.linalg.norm(first_after[:2] - second_after[:2])) < 0.04:
                        continue
                    _set_entity_pose(env, first, first_after, first_quaternion)
                    _set_entity_pose(env, second, second_after, second_quaternion)
                    if _entity_deep_contacts(env, first) or _entity_deep_contacts(env, second):
                        _set_entity_pose(env, first, first_position, first_quaternion)
                        _set_entity_pose(env, second, second_position, second_quaternion)
                        continue
                    selected = (
                        first_after,
                        second_after,
                        first_quaternion,
                        second_quaternion,
                        first_support,
                        second_support,
                    )
                    break
                if selected is None:
                    _set_entity_pose(env, first, first_position, first_quaternion)
                    _set_entity_pose(env, second, second_position, second_quaternion)
                    raise PerturbationValidationError(
                        f"S04 grounded swap for {first!r}/{second!r} has no collision-clear placement"
                    )
                first_after, second_after, _, _, first_support, second_support = selected
            else:
                first_after = first_position.copy()
                second_after = second_position.copy()
                first_after[:2] = second_position[:2] + swap_offset
                second_after[:2] = first_position[:2] - swap_offset
                if not _candidate_is_clear(
                    env, first, first_after[:2], 0.045, ignored=(first, second)
                ) or not _candidate_is_clear(
                    env, second, second_after[:2], 0.045, ignored=(first, second)
                ):
                    raise PerturbationValidationError(
                        f"S04 swap for {first!r}/{second!r} has no collision-clear placement"
                    )
                try:
                    _set_entity_pose(env, first, first_after, first_quaternion)
                    _set_entity_pose(env, second, second_after, second_quaternion)
                    if _entity_deep_contacts(env, first) or _entity_deep_contacts(env, second):
                        raise PerturbationValidationError(
                            f"S04 swap for {first!r}/{second!r} created deep penetration"
                        )
                except Exception:
                    _set_entity_pose(env, first, first_position, first_quaternion)
                    _set_entity_pose(env, second, second_position, second_quaternion)
                    raise
            self._log_once(
                "grounded_planar_object_position_swap" if grounded_swap else "planar_object_position_swap",
                0,
                first=first,
                second=second,
                first_xy_before=first_position[:2].tolist(),
                first_xy_after=first_after[:2].tolist(),
                second_xy_before=second_position[:2].tolist(),
                second_xy_after=second_after[:2].tolist(),
                **(
                    {
                        "first_support": first_support,
                        "second_support": second_support,
                    }
                    if grounded_swap
                    else {}
                ),
            )
        elif case_id in {"S03", "S05", "S10", "S11", "S12"}:
            if case_id == "S11" and _param_bool(
                self.plan.params, "fixture_distractor", False
            ):
                targets = _name_tuple(
                    self.plan.params.get("fixture_distractor_targets")
                ) or self.plan.targets
                missing = [name for name in targets if not _entity_exists(env, name)]
                if missing:
                    raise PerturbationValidationError(
                        f"S11 fixture distractors are absent from the compiled scene: {missing}"
                    )
                self._log_once(
                    "static_fixture_distractor_present", 0, targets=list(targets)
                )
                return
            asset_names = tuple(
                _injected_name(self.plan, index)
                for index in range(len(self.plan.assets))
            )
            if any(not _entity_exists(env, name) for name in asset_names):
                raise PerturbationValidationError(
                    f"Expected injected assets {asset_names!r} are absent from the compiled scene"
                )
            name = asset_names[0]
            reference_name = _static_asset_reference_name(self.plan)
            reference, _ = _entity_pose(env, reference_name)
            position = reference.copy()
            quaternion = _yaw_quaternion(0.0)
            anchor_name = reference_name
            if case_id == "S03":
                height_delta = _param_float(
                    self.plan.params, "height_delta_m", 0.05
                )
                if height_delta <= 0.0:
                    raise PerturbationConfigurationError(
                        "S03 height_delta_m must be positive"
                    )
                raised = reference.copy()
                raised[2] += height_delta
                workspace_entities = {
                    "main_table",
                    "kitchen_table",
                    "living_room_table",
                    "study_table",
                    "coffee_table",
                    "floor",
                }
                # Never lift the shared work surface.  For a task whose first
                # target is a movable receiver, only that receiver is raised;
                # a table/floor target gets a riser placed below it instead.
                if reference_name not in workspace_entities:
                    _set_entity_pose(env, reference_name, raised)
                else:
                    raised = reference.copy()
                support_height = 0.05
                if "asset_geometry_factors" in self.plan.params:
                    factors = _param_vector(
                        self.plan.params,
                        "asset_geometry_factors",
                        (1.0, 1.0, 1.0),
                    )
                    if np.any(factors <= 0.0):
                        raise PerturbationConfigurationError(
                            "S03 asset_geometry_factors must be positive"
                        )
                    support_height *= float(factors[2])
                position[2] = raised[2] - support_height - 0.01
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
                path_fraction = _param_float(
                    self.plan.params, "barrier_path_fraction", 0.58
                )
                if not 0.0 < path_fraction < 1.0:
                    raise PerturbationConfigurationError(
                        "S05 barrier_path_fraction must be between 0 and 1"
                    )
                lateral_offset = _param_float(
                    self.plan.params, "barrier_lateral_offset_m", 0.035
                )
                position = target + path_fraction * (receiver - target)
                position[:2] += np.array([-direction[1], direction[0]]) * lateral_offset
                quaternion = _yaw_quaternion(math.atan2(direction[1], direction[0]) + math.pi / 2)
            elif case_id in {"S10", "S11"}:
                target_position, _ = _entity_pose(env, self.plan.targets[0])
                count = len(asset_names)
                defaults = (
                    (0.14, -0.10),
                    (0.10, 0.12),
                    (-0.13, -0.08),
                    (-0.12, 0.12),
                )
                if case_id == "S11":
                    defaults = (
                        (0.085, 0.065),
                        (-0.085, 0.065),
                        (0.085, -0.065),
                        (-0.085, -0.065),
                    )
                offsets = _param_offsets(
                    self.plan.params, "clutter_offsets_xy", count, defaults
                )
                placed_assets: list[str] = []
                configured_quaternion = _param_vector(
                    self.plan.params, "asset_quat", (1.0, 0.0, 0.0, 0.0)
                )
                for index, asset_name in enumerate(asset_names):
                    requested_xy = target_position[:2] + offsets[index]
                    selected_candidate: tuple[np.ndarray, str] | None = None
                    original_asset_position, original_asset_quaternion = _entity_pose(
                        env, asset_name
                    )
                    for candidate_xy in _nearby_xy_candidates(requested_xy):
                        grounded = _grounded_entity_position(
                            env,
                            asset_name,
                            candidate_xy,
                            self.plan.params,
                            ignored=(asset_name, *placed_assets),
                        )
                        if grounded is None:
                            continue
                        candidate, support_geom = grounded
                        minimum_gap = _param_float(
                            self.plan.params, "clutter_minimum_gap_m", 0.045
                        )
                        support_names = _name_tuple(
                            self.plan.params.get("support_surface")
                        ) or ("main_table",)
                        if not _candidate_is_clear(
                            env,
                            asset_name,
                            candidate[:2],
                            minimum_gap,
                            ignored=_clutter_clearance_ignored(
                                self.plan,
                                asset_name,
                                tuple(placed_assets),
                                tuple(support_names),
                            ),
                        ):
                            continue
                        if any(
                            float(np.linalg.norm(candidate[:2] - _entity_pose(env, placed)[0][:2]))
                            < minimum_gap
                            for placed in placed_assets
                        ):
                            continue
                        _set_entity_pose(
                            env,
                            asset_name,
                            candidate,
                            configured_quaternion,
                        )
                        if _entity_deep_contacts(env, asset_name, tolerance=0.0015):
                            _set_entity_pose(
                                env,
                                asset_name,
                                original_asset_position,
                                original_asset_quaternion,
                            )
                            continue
                        selected_candidate = (candidate, support_geom)
                        break
                    if selected_candidate is None:
                        _set_entity_pose(
                            env,
                            asset_name,
                            original_asset_position,
                            original_asset_quaternion,
                        )
                        raise PerturbationValidationError(
                            f"{case_id} clutter asset {asset_name!r} has no collision-clear support position"
                        )
                    candidate, support_geom = selected_candidate
                    placed_assets.append(asset_name)
                    self._log_once(
                        "static_asset_placed" if index == 0 else "static_asset_placed_additional",
                        0,
                        asset=asset_name,
                        asset_id=self.plan.assets[index].asset_id,
                        reference=reference_name,
                        anchor=reference_name,
                        position=candidate.tolist(),
                        support_geom=support_geom,
                        requested_xy=requested_xy.tolist(),
                    )
                return
            else:
                fraction = _param_float(
                    self.plan.params, "occlusion_fraction", 0.62
                )
                position, quaternion = _camera_occluder_pose(
                    env, reference_name, fraction=fraction
                )
            if not _candidate_is_clear(
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
            light_factor = _required_param_float(self.plan.params, "light_factor")
            if not 0.0 < light_factor <= 1.0:
                raise PerturbationConfigurationError(
                    "S14 light_factor must be in the interval (0, 1]"
                )
            self._set_lighting(env, light_factor)
            self._log_once(
                "scene_domain_changed",
                0,
                changed_geoms=changed_geoms,
                light_factor=light_factor,
            )
        elif case_id == "S15":
            offset = _param_vector(
                self.plan.params,
                "camera_offset_xyz",
                (0.045, -0.035, 0.025),
            )
            rotation = _param_vector(
                self.plan.params, "camera_rotation_rpy", (0.0, 0.0, 0.0)
            )
            self._offset_camera(env, offset, rotation)
            self._log_once(
                "camera_extrinsics_changed",
                0,
                camera_offset_xyz=offset.tolist(),
                camera_rotation_rpy=rotation.tolist(),
            )
        elif case_id == "S16":
            fov_scale = _param_float(self.plan.params, "fov_scale", 1.12)
            changed = []
            for camera in self.plan.targets:
                try:
                    camera_id = int(env.sim.model.camera_name2id(camera))
                except Exception:
                    continue
                before = float(env.sim.model.cam_fovy[camera_id])
                env.sim.model.cam_fovy[camera_id] = float(
                    np.clip(before * fov_scale, 20.0, 100.0)
                )
                changed.append(camera)
            if not changed:
                raise PerturbationValidationError(
                    f"No camera intrinsics found for {self.plan.targets}"
                )
            env.sim.forward()
            self._log_once(
                "camera_intrinsics_changed",
                0,
                cameras=changed,
                fov_scale=fov_scale,
            )
        elif case_id == "S17":
            robot = env.robots[0]
            indices = list(robot._ref_joint_pos_indexes)
            current = np.asarray(env.sim.data.qpos[indices]).copy()
            configured = self.plan.params.get(
                "joint_offset_rad",
                (0.035, -0.025, 0.02, 0.0, 0.0, 0.0, 0.0),
            )
            try:
                offset = np.asarray(configured, dtype=np.float64).reshape(-1)
            except (TypeError, ValueError) as exc:
                raise PerturbationConfigurationError(
                    "S17 joint_offset_rad must be a numeric vector"
                ) from exc
            if offset.size > len(current) or not np.all(np.isfinite(offset)):
                raise PerturbationConfigurationError(
                    "S17 joint_offset_rad cannot exceed the robot joint count"
                )
            offset = np.pad(offset, (0, len(current) - offset.size))
            env.sim.data.qpos[indices] = current + offset
            env.sim.forward()
            self._log_once(
                "robot_initial_state_changed",
                0,
                joint_offset_rad=offset.tolist(),
                eef_offset_xyz=_param_vector(
                    self.plan.params, "eef_offset_xyz", (0.0, 0.0, 0.0)
                ).tolist(),
                gripper_opening_offset=_param_float(
                    self.plan.params, "gripper_opening_offset", 0.0
                ),
            )
        elif case_id == "S21":
            self.language_instruction("", 0)
        elif case_id == "S22":
            self._apply_workspace_texture(env)
        elif case_id == "S06":
            target = self.plan.targets[0]
            if self.plan.params.get("fixture_variant"):
                self._log_once(
                    "fixture_variant_applied",
                    0,
                    target=target,
                    fixture_variant=str(self.plan.params["fixture_variant"]),
                    geometry_factors=(
                        _param_vector(
                            self.plan.params,
                            "fixture_geometry_factors",
                            (1.12, 1.12, 1.0),
                        ).tolist()
                    ),
                )
                return
            if "asset_quat" in self.plan.params:
                quaternion = _param_vector(
                    self.plan.params, "asset_quat", (1.0, 0.0, 0.0, 0.0)
                )
                norm = float(np.linalg.norm(quaternion))
                if norm <= 1e-8:
                    raise PerturbationConfigurationError(
                        "S06 asset_quat must be non-zero"
                    )
                position, _ = _entity_pose(env, target)
                _set_entity_pose(env, target, position, quaternion / norm)
            if _param_bool(self.plan.params, "grounded_replacement", False):
                position, quaternion = _entity_pose(env, target)
                grounded = _grounded_entity_position(
                    env,
                    target,
                    position[:2],
                    self.plan.params,
                    ignored=(target,),
                )
                if grounded is None:
                    raise PerturbationValidationError(
                        f"S06 replacement target {target!r} has no configured support surface"
                    )
                grounded_position, support_geom = grounded
                grounded_height_offset = _param_float(
                    self.plan.params, "grounded_height_offset_m", 0.0
                )
                if grounded_height_offset < 0.0:
                    raise PerturbationConfigurationError(
                        "S06 grounded_height_offset_m must be nonnegative"
                    )
                grounded_position[2] += grounded_height_offset
                _set_entity_pose(env, target, grounded_position, quaternion)
                self._log_once(
                    "replacement_target_grounded",
                    0,
                    target=target,
                    position=grounded_position.tolist(),
                    support_geom=support_geom,
                    xy_preserved=True,
                    height_offset_m=grounded_height_offset,
                )
            self._log_once(
                "target_instance_replaced",
                0,
                target=target,
                asset_id=self.plan.assets[0].asset_id if self.plan.assets else None,
                scale=self.plan.assets[0].scale if self.plan.assets else None,
                asset_quat=(
                    self.plan.params.get("asset_quat")
                    if "asset_quat" in self.plan.params
                    else None
                ),
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
        for target in self.plan.disturbance_targets or ():
            if _entity_exists(env, target) and target not in self._saved_poses:
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
                if self.plan.case_id == "D03" and _param_bool(
                    self.plan.params, "persistent_movable_asset", False
                ):
                    # This free-joint asset must stay above the scene until
                    # _stage_persistent_obstacle disables its collisions.
                    self._saved_poses[name] = (position, quat)
                    continue
                if self.plan.case_id == "D06":
                    anchors = _name_tuple(
                        self.plan.params.get("asset_initial_anchor")
                    )
                    if len(anchors) != 1 or not _entity_exists(env, anchors[0]):
                        raise PerturbationConfigurationError(
                            "D06 asset_initial_anchor must name one scene entity"
                        )
                    anchor, _ = _entity_pose(env, anchors[0])
                    offset_xy = _required_param_vector(
                        self.plan.params, "asset_initial_offset_xy", 2
                    )
                    grounded = _grounded_entity_position(
                        env,
                        name,
                        anchor[:2] + offset_xy,
                        self.plan.params,
                        ignored=(name,),
                    )
                    if grounded is None:
                        raise PerturbationValidationError(
                            "D06 injected distractor has no configured support surface"
                        )
                    grounded_position, _ = grounded
                    support_names = _support_entity_names(self.plan.params)
                    initial_clearance = _param_float(
                        self.plan.params, "asset_initial_clearance_m", 0.08
                    )
                    if not _candidate_is_clear(
                        env,
                        name,
                        grounded_position[:2],
                        initial_clearance,
                        ignored=(name, *support_names),
                    ):
                        raise PerturbationValidationError(
                            "D06 injected distractor initial pose is not collision-clear"
                        )
                    configured_quaternion = _param_vector(
                        self.plan.params, "asset_quat", (1.0, 0.0, 0.0, 0.0)
                    )
                    _set_entity_pose(
                        env, name, grounded_position, configured_quaternion
                    )
                    self._saved_poses[name] = (
                        grounded_position.copy(),
                        configured_quaternion.copy(),
                    )
                    continue
                self._saved_poses[name] = (position, quat)
                _set_entity_pose(env, name, np.array([0.0, 0.0, -5.0]), quat)

    def _change_appearance(self, env: Any, targets: tuple[str, ...]) -> list[str]:
        color = _required_param_vector(self.plan.params, "color_rgb", 3)
        if np.any(color < 0.0) or np.any(color > 1.0):
            raise PerturbationConfigurationError("S13 color_rgb must be in [0, 1]")
        changed: list[str] = []
        for target in targets:
            if not _entity_exists(env, target):
                continue
            body_ids = set(_entity_body_ids(env, target))
            for geom_id in range(int(env.sim.model.ngeom)):
                if int(env.sim.model.geom_bodyid[geom_id]) not in body_ids:
                    continue
                rgba = np.asarray(env.sim.model.geom_rgba[geom_id]).copy()
                rgba[:3] = color
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
        mix = _required_param_float(self.plan.params, "scene_color_mix")
        luminance_factors = _required_param_vector(
            self.plan.params, "scene_luminance_factors", 3
        )
        if not 0.0 <= mix <= 1.0:
            raise PerturbationConfigurationError("S14 scene_color_mix must be in [0, 1]")
        changed = 0
        for geom_id in range(int(env.sim.model.ngeom)):
            rgba = np.asarray(env.sim.model.geom_rgba[geom_id]).copy()
            if rgba.shape[0] < 4 or rgba[3] <= 0.0:
                continue
            rgb = rgba[:3]
            # A cool, lower-saturation domain shift preserves shading and texture;
            # S13 instead applies one flat green material to task entities only.
            luminance = float(np.dot(rgb, np.array([0.2126, 0.7152, 0.0722])))
            shifted = (1.0 - mix) * rgb + mix * np.array(
                [
                    luminance_factors[0] * luminance,
                    luminance_factors[1] * luminance,
                    min(1.0, luminance_factors[2] * luminance),
                ]
            )
            rgba[:3] = np.clip(shifted, 0.0, 1.0)
            env.sim.model.geom_rgba[geom_id] = rgba
            changed += 1
        if not changed:
            raise PerturbationValidationError("MuJoCo model exposes no visible scene geoms")
        env.sim.forward()
        return changed

    def _set_lighting(self, env: Any, factor: float) -> dict[str, list[list[float]]]:
        if not hasattr(env.sim.model, "light_diffuse"):
            raise PerturbationValidationError("MuJoCo model exposes no lights")
        env.sim.model.light_diffuse[:] *= float(factor)
        env.sim.model.light_ambient[:] *= float(factor)
        env.sim.forward()
        return {
            "light_diffuse": np.asarray(env.sim.model.light_diffuse).tolist(),
            "light_ambient": np.asarray(env.sim.model.light_ambient).tolist(),
        }

    def _restore_lighting(self, env: Any) -> dict[str, list[list[float]]]:
        fields = ("light_diffuse", "light_ambient")
        if any(field not in self._model_baseline for field in fields):
            raise PerturbationValidationError(
                "MuJoCo lighting baseline was not captured before D09"
            )
        for model_field in fields:
            getattr(env.sim.model, model_field)[:] = self._model_baseline[model_field]
        env.sim.forward()
        return {
            "light_diffuse": np.asarray(env.sim.model.light_diffuse).tolist(),
            "light_ambient": np.asarray(env.sim.model.light_ambient).tolist(),
        }

    def _offset_camera(
        self,
        env: Any,
        delta: np.ndarray,
        rotation_rpy: np.ndarray | None = None,
    ) -> None:
        changed = False
        rotation = (
            _rpy_quaternion(rotation_rpy)
            if rotation_rpy is not None
            else _rpy_quaternion(np.zeros(3, dtype=np.float64))
        )
        for camera in self.plan.targets or ("agentview",):
            try:
                camera_id = env.sim.model.camera_name2id(camera)
            except Exception:
                continue
            env.sim.model.cam_pos[camera_id] += np.asarray(delta)
            if rotation_rpy is not None and np.any(np.asarray(rotation_rpy)):
                current = np.asarray(env.sim.model.cam_quat[camera_id], dtype=np.float64)
                env.sim.model.cam_quat[camera_id] = _quaternion_multiply(rotation, current)
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
        if self._staged_persistent_obstacle is not None:
            self._maintain_staged_persistent_obstacle(env)
        if self._dynamic_applied:
            if (
                case_id == "D09"
                and not self._dynamic_restored
                and not self._event_active(step)
            ):
                restored_value = self._restore_lighting(env)
                self._dynamic_restored = True
                self._log_once(
                    "dynamic_lighting_restored",
                    step,
                    restored_value=restored_value,
                )
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
                case_id in {"D03", "D04"}
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

        if self._persistent_d03_obstacle_name() is not None:
            self._enter_persistent_obstacle(env, step)
            return

        if case_id in {"D01", "D02", "D06", "D18", "D19"}:
            if self._interaction_mode() == "articulation" and case_id in {"D18", "D19"}:
                articulation_targets = _goal_articulation_targets(env)
                if not articulation_targets:
                    raise PerturbationValidationError(
                        f"{case_id} articulation fallback has no goal fixture"
                    )
                target, _ = articulation_targets[0]
                articulation_clearance = _param_float(
                    self.plan.params, "minimum_clearance_m", 0.08
                )
                if articulation_clearance <= 0.0:
                    raise PerturbationConfigurationError(
                        f"{case_id} minimum_clearance_m must be positive"
                    )
                _, after, applied = _safe_offset_pose(
                    env,
                    target,
                    _dynamic_pose_requested_delta(case_id, target, self.plan.params),
                    minimum_gap=articulation_clearance,
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
            if case_id == "D06" and self.plan.assets:
                targets = [
                    _injected_name(self.plan, index)
                    for index in range(len(self.plan.assets))
                ]
                missing = [name for name in targets if not _entity_exists(env, name)]
                if missing:
                    raise PerturbationValidationError(
                        f"D06 injected distractors are absent from the scene: {missing}"
                    )
            elif case_id == "D06" and self.plan.disturbance_targets is not None:
                targets = list(self.plan.disturbance_targets)
                if len(set(targets)) != len(targets):
                    raise PerturbationValidationError(
                        f"D06 disturbance_targets must be unique: {targets}"
                    )
                goal_targets = set(_goal_interaction_targets(env))
                invalid = [
                    name
                    for name in targets
                    if not _entity_exists(env, name)
                    or name not in getattr(env, "objects_dict", {})
                    or name in goal_targets
                ]
                if invalid:
                    raise PerturbationValidationError(
                        f"D06 disturbance_targets must be unrelated movable objects: {invalid}"
                    )
            else:
                targets = [name for name in self.plan.targets if _entity_exists(env, name)]
            if not targets and case_id != "D06":
                raise PerturbationValidationError(
                    f"Dynamic case {case_id} has no movable target in {self.plan.targets}"
                )
            if case_id == "D06":
                original_poses: dict[str, tuple[np.ndarray, np.ndarray]] = {}
                changes: list[dict[str, Any]] = []
                before_contacts = {
                    name: _entity_deep_contacts(env, name) for name in targets
                }
                minimum_clearance = _param_float(
                    self.plan.params, "minimum_clearance_m", 0.08
                )
                if minimum_clearance <= 0.0:
                    raise PerturbationConfigurationError(
                        "D06 minimum_clearance_m must be positive"
                    )
                minimum_displacement = max(
                    0.10,
                    _param_float(
                        self.plan.params, "minimum_displacement_m", 0.10
                    ),
                )
                try:
                    for target in targets:
                        original_poses[target] = _entity_pose(env, target)
                        before, after, applied = _safe_offset_pose(
                            env,
                            target,
                            _dynamic_pose_requested_delta(case_id, target, self.plan.params),
                            minimum_gap=minimum_clearance,
                            minimum_displacement=minimum_displacement,
                            baseline_deep_contacts=before_contacts[target],
                        )
                        after_contacts = _entity_deep_contacts(env, target)
                        baseline_pairs = {
                            (item["first"], item["second"])
                            for item in before_contacts[target]
                        }
                        new_contacts = [
                            item
                            for item in after_contacts
                            if (item["first"], item["second"]) not in baseline_pairs
                        ]
                        if new_contacts:
                            raise PerturbationValidationError(
                                f"D06 moved {target!r} into deep penetration: {new_contacts}"
                            )
                        changes.append(
                            {
                                "target": target,
                                "delta_xy": applied.tolist(),
                                "position": after.tolist(),
                                "distance_m": float(np.linalg.norm(applied)),
                            }
                        )
                except Exception:
                    for name in reversed(original_poses):
                        position, quaternion = original_poses[name]
                        _set_entity_pose(env, name, position, quaternion)
                    raise
                self._log_once(
                    "dynamic_state_change",
                    step,
                    targets=targets,
                    changes=changes,
                    minimum_clearance_m=minimum_clearance,
                    minimum_displacement_m=minimum_displacement,
                )
                self._dynamic_event_step = int(step)
                self._dynamic_applied = True
                return
            target = targets[0]
            delta = _dynamic_pose_requested_delta(case_id, target, self.plan.params)
            support_relation_state = None
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
                offset = _required_param_vector(
                    self.plan.params, "misplace_offset_xy", 2
                )
                perpendicular = np.array([-return_direction[1], return_direction[0]])
                after[:2] += return_direction * offset[0] + perpendicular * offset[1]
                misplace_height = _required_param_float(
                    self.plan.params, "misplace_height_m"
                )
                after[2] += misplace_height
                x_min, x_max, y_min, y_max = _workspace_bounds(env)
                after[0] = np.clip(after[0], x_min, x_max)
                after[1] = np.clip(after[1], y_min, y_max)
                applied = after[:2] - before[:2]
                minimum_clearance = _param_float(
                    self.plan.params,
                    "minimum_clearance_m",
                    _param_float(
                        self.plan.params, "misplace_minimum_gap_m", 0.045
                    ),
                )
                if minimum_clearance <= 0.0:
                    raise PerturbationConfigurationError(
                        "D19 minimum_clearance_m must be positive"
                    )
                if not _candidate_is_clear(
                    env,
                    target,
                    after[:2],
                    minimum_clearance,
                    ignored=(target, *self.plan.references),
                ):
                    _, after, applied = _safe_offset_pose(
                        env,
                        target,
                        (float(applied[0]), float(applied[1])),
                        minimum_gap=minimum_clearance,
                        ignored=(target, *self.plan.references),
                    )
                    after[2] = before[2] + misplace_height
                # A misplacement must remain recoverable and supported.  Use
                # the task's declared support surface when available, then
                # fall back to the original support height.  Never leave a
                # free object at an arbitrary fixed lift height.
                grounded = _grounded_entity_position(
                    env,
                    target,
                    after[:2],
                    self.plan.params,
                    ignored=(target, *self.plan.references),
                )
                if grounded is not None:
                    after, support_geom = grounded
                    self._log_once(
                        "misplacement_grounded",
                        step,
                        target=target,
                        support_geom=support_geom,
                        support_position=after.tolist(),
                    )
                elif bool(self.plan.params.get("preserve_support_z", False)):
                    after[2] = initial[2]
                _set_entity_pose(env, target, after, current_quaternion)
                if _entity_deep_contacts(env, target):
                    _set_entity_pose(env, target, before, current_quaternion)
                    raise PerturbationValidationError(
                        f"D19 misplacement for {target!r} created deep penetration"
                    )
            else:
                preserve_support_relation = case_id == "D01" and _param_bool(
                    self.plan.params, "preserve_original_support_relation", False
                )
                if preserve_support_relation:
                    support_entities = _name_tuple(
                        self.plan.params.get("support_surface")
                    )
                    if len(support_entities) != 1:
                        raise PerturbationConfigurationError(
                            "D01 support preservation requires exactly one support_surface"
                        )
                    support_entity = support_entities[0]
                    if support_entity == target or not _entity_exists(env, support_entity):
                        raise PerturbationConfigurationError(
                            f"D01 support entity {support_entity!r} is invalid"
                        )
                    local_clearance = _required_param_float(
                        self.plan.params, "support_relation_clearance_m"
                    )
                    if not 0.0 < local_clearance < 0.03:
                        raise PerturbationConfigurationError(
                            "D01 support_relation_clearance_m must be between 0 and 0.03"
                        )
                    before, original_quaternion = _entity_pose(env, target)
                    after = before.copy()
                    after[:2] += np.asarray(delta, dtype=np.float64)
                    applied = after[:2] - before[:2]
                    if not _candidate_is_clear(
                        env,
                        target,
                        after[:2],
                        local_clearance,
                        ignored=(support_entity,),
                    ):
                        raise PerturbationValidationError(
                            f"D01 support-preserving position for {target!r} is blocked"
                        )
                    grounded = _grounded_entity_position(
                        env,
                        target,
                        after[:2],
                        self.plan.params,
                        ignored=(target, *self.plan.references),
                    )
                    if grounded is None:
                        raise PerturbationValidationError(
                            f"D01 could not ground {target!r} on {support_entity!r}"
                        )
                    _, support_geom = grounded
                    if not _support_geom_belongs_to_entity(
                        env, support_geom, support_entity
                    ):
                        raise PerturbationValidationError(
                            f"D01 candidate for {target!r} left support {support_entity!r}"
                        )
                    # Movable support assets can expose collision AABBs below
                    # their semantic top. Keep the established relative height
                    # while using the support geom only to validate XY coverage.
                    after[2] = before[2]
                    _set_entity_pose(env, target, after, original_quaternion)
                    support_relation_state = (
                        before,
                        original_quaternion,
                        support_entity,
                        support_geom,
                    )
                else:
                    minimum_clearance = (
                        _param_float(self.plan.params, "minimum_clearance_m", 0.08)
                        if case_id == "D18"
                        else 0.08
                    )
                    if minimum_clearance <= 0.0:
                        raise PerturbationConfigurationError(
                            f"{case_id} minimum_clearance_m must be positive"
                        )
                    _, after, applied = _safe_offset_pose(
                        env,
                        target,
                        delta,
                        minimum_gap=minimum_clearance,
                    )
                    grounded = _grounded_entity_position(
                        env,
                        target,
                        after[:2],
                        self.plan.params,
                        ignored=(target, *self.plan.references),
                    )
                    if grounded is not None:
                        after, support_geom = grounded
                        self._log_once(
                            "drop_position_grounded",
                            step,
                            target=target,
                            support_geom=support_geom,
                            support_position=after.tolist(),
                        )
            yaw = (
                _param_float(self.plan.params, "yaw_rad", 0.28)
                if case_id == "D01"
                and _param_bool(
                    self.plan.params, "preserve_original_support_relation", False
                )
                else {"D01": 0.28, "D02": -0.24}.get(case_id)
            )
            if (
                case_id == "D18"
                and target in self._saved_poses
                and not _param_bool(self.plan.params, "grounded_pose", False)
            ):
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
            if support_relation_state is not None:
                before, original_quaternion, support_entity, support_geom = (
                    support_relation_state
                )
                deep_contacts = _entity_deep_contacts(env, target)
                if deep_contacts:
                    _set_entity_pose(env, target, before, original_quaternion)
                    raise PerturbationValidationError(
                        f"D01 support-preserving move for {target!r} created deep penetration"
                    )
                self._log_once(
                    "support_relation_preserved",
                    step,
                    target=target,
                    support=support_entity,
                    support_geom=support_geom,
                    support_position=after.tolist(),
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
                fraction = _param_float(
                    self.plan.params, "occlusion_fraction", 0.62
                )
                position, quaternion = _camera_occluder_pose(
                    env, reference_name, fraction=fraction
                )
                offset = _param_vector(
                    self.plan.params, "occlusion_offset_xyz", (0.0, 0.0, 0.0)
                )
                position = position + offset
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
                    lateral_offset = _param_float(
                        self.plan.params, "lateral_offset_m", 0.025
                    )
                    position[:2] += np.array([-direction[1], direction[0]]) * lateral_offset
                    position[2] += _param_float(
                        self.plan.params, "barrier_height_m", 0.0
                    )
                    quaternion = _yaw_quaternion(math.atan2(direction[1], direction[0]) + math.pi / 2)
            else:
                configured_anchors = _name_tuple(
                    self.plan.params.get("receiver_anchor")
                )
                if len(configured_anchors) > 1:
                    raise PerturbationConfigurationError(
                        f"{case_id} receiver_anchor must name at most one site"
                    )
                position, anchor_name = _functional_anchor(
                    env,
                    reference_name,
                    configured_anchors[0] if configured_anchors else None,
                )
                asset_offset = _param_vector(
                    self.plan.params, "asset_offset_xyz", (0.0, 0.0, 0.025)
                )
                position = position + asset_offset
                if case_id == "D03":
                    # Larger occupancy assets need a small proportional lift so
                    # their collision mesh clears receiver rims and cabinet tops.
                    asset_scale = _param_float(
                        self.plan.params, "asset_scale", 1.0
                    )
                    position[2] += max(0.0, (asset_scale - 1.0) * 0.008)
                quaternion = _yaw_quaternion(0.0)
            placed_position, support_geom = _safe_dynamic_asset_pose(
                env,
                name,
                position,
                quaternion,
                self.plan.params,
                ignored=(reference_name, *self.plan.targets, *self.plan.references),
            )
            self._log_once(
                "dynamic_asset_entered",
                step,
                asset=name,
                reference=reference_name,
                anchor=anchor_name,
                position=placed_position.tolist(),
                support_geom=support_geom,
            )
        elif case_id == "D07":
            offset = _param_vector(
                self.plan.params,
                "camera_offset_xyz",
                (0.025, -0.018, 0.012),
            )
            rotation = _param_vector(
                self.plan.params, "camera_rotation_rpy", (0.0, 0.0, 0.0)
            )
            self._offset_camera(env, offset, rotation)
            self._log_once(
                "dynamic_camera_offset",
                step,
                camera_offset_xyz=offset.tolist(),
                camera_rotation_rpy=rotation.tolist(),
            )
        elif case_id == "D09":
            lighting_factor = _param_float(
                self.plan.params, "lighting_factor", 0.48
            )
            if not 0.0 < lighting_factor <= 1.0:
                raise PerturbationConfigurationError(
                    "D09 lighting_factor must be in the interval (0, 1]"
                )
            applied_value = self._set_lighting(env, lighting_factor)
            baseline_value = {
                "light_diffuse": np.asarray(
                    self._model_baseline["light_diffuse"]
                ).tolist(),
                "light_ambient": np.asarray(
                    self._model_baseline["light_ambient"]
                ).tolist(),
            }
            self._log_once(
                "dynamic_lighting_change",
                step,
                lighting_factor=lighting_factor,
                requested_value={"lighting_factor": float(lighting_factor)},
                baseline_value=baseline_value,
                applied_value=applied_value,
            )
        elif case_id == "D17":
            # Opening the gripper is applied through transform_action; no pose teleport.
            self._dynamic_event_origin_eef = np.asarray(
                env.sim.data.site_xpos[env.robots[0].eef_site_id], dtype=np.float64
            ).copy()
            self._log_once("grasp_failure_window_started", step)
        elif case_id == "D20":
            self._apply_safe_robot_displacement(env, step)
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
            threshold = _param_float(
                self.plan.params, "trigger_distance_m", 0.12
            )
            if threshold <= 0.0:
                raise PerturbationConfigurationError(
                    "D01 trigger_distance_m must be positive"
                )
            return bool(np.linalg.norm(eef - position) <= threshold)
        if case_id == "D20":
            if eef is None:
                return False
            if self._initial_eef_position is None:
                self._initial_eef_position = eef.copy()
                return False
            action = self.previous_action
            action_norm = 0.0
            if action is not None and action.size:
                arm_action = action[:-1] if action.size > 1 else action
                action_norm = float(np.linalg.norm(arm_action))
            return bool(
                action_norm
                >= float(self.plan.params.get("trigger_action_norm", 0.05))
                and np.linalg.norm(eef - self._initial_eef_position)
                >= float(self.plan.params.get("trigger_eef_motion_m", 0.025))
            )
        if case_id == "D17" and target and eef is not None:
            position, _ = _entity_pose(env, target)
            if self._interaction_mode() == "articulation":
                articulation_distance = _required_param_float(
                    self.plan.params, "articulation_grasp_distance_m"
                )
                if articulation_distance <= 0.0:
                    raise PerturbationConfigurationError(
                        "D17 articulation_grasp_distance_m must be positive"
                    )
                return bool(
                    np.linalg.norm(eef - self._articulation_anchor(env, target))
                    <= articulation_distance
                )
            closing = bool(
                self.previous_action is not None
                and self.previous_action.size
                and self.previous_action[-1] > 0.0
            )
            # Require a real robot/object contact when MuJoCo reports one.
            # The distance fallback is retained for wrappers that omit contact
            # data, but the object must also be near its initial support so a
            # post-lift close command cannot fabricate a failed grasp.
            saved = self._saved_poses.get(target)
            initial_tolerance = _required_param_float(
                self.plan.params, "grasp_initial_tolerance_m"
            )
            grasp_distance = _required_param_float(
                self.plan.params, "grasp_distance_m"
            )
            contact_fallback = _required_param_float(
                self.plan.params, "contact_fallback_distance_m"
            )
            wrapper_fallback = _required_param_float(
                self.plan.params, "wrapper_fallback_distance_m"
            )
            if min(
                initial_tolerance,
                grasp_distance,
                contact_fallback,
                wrapper_fallback,
            ) <= 0.0:
                raise PerturbationConfigurationError(
                    "D17 grasp trigger distances must be positive"
                )
            near_initial = (
                saved is None
                or np.linalg.norm(position - saved[0]) <= initial_tolerance
            )
            has_contact_model = getattr(getattr(env, "sim", None), "model", None) is not None
            distance_fallback = contact_fallback if has_contact_model else wrapper_fallback
            return bool(
                closing
                and near_initial
                and np.linalg.norm(eef - position) <= grasp_distance
                and (
                    _eef_target_contact(env, target)
                    or np.linalg.norm(eef - position) <= distance_fallback
                )
            )
        if (
            self._interaction_mode() == "articulation"
            and case_id in {"D02", "D03", "D05", "D19"}
            and eef is not None
        ):
            articulation_targets = _goal_articulation_targets(env)
            if articulation_targets:
                target_name, _ = articulation_targets[0]
                anchor = self._articulation_anchor(env, target_name)
                threshold = self._receiver_trigger_distance_m(case_id)
                if case_id == "D19":
                    return bool(
                        self._articulation_progress(env, target_name)
                        >= float(self.plan.params.get("trigger_state_change_m", 0.02))
                        and np.linalg.norm(eef - anchor) <= threshold
                    )
                return bool(np.linalg.norm(eef - anchor) <= threshold)
        if case_id in {"D02", "D03", "D05", "D19"}:
            candidates = _goal_path_anchor_candidates(env)
            for goal_target, position, _, receiver in candidates:
                saved = self._saved_poses.get(goal_target)
                if saved is None:
                    continue
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
                        eef is not None
                        and np.linalg.norm(eef - position)
                        <= self._receiver_trigger_distance_m(case_id)
                    )
                    if transported and closing and held_near_eef:
                        return True
                elif case_id == "D19":
                    # D19 is a placement-stage perturbation: trigger only
                    # when the carried object is at the receiver, not merely
                    # when it has been lifted elsewhere in the workspace.
                    # Full environments provide the gripper action.  Some
                    # replay/validation wrappers intentionally omit action
                    # history; their transport pose and receiver approach
                    # are still sufficient evidence for the event.
                    closing = self.previous_action is None or bool(
                        self.previous_action.size and self.previous_action[-1] > 0.0
                    )
                    if (
                        transported
                        and closing
                        and eef is not None
                        and np.linalg.norm(eef - receiver)
                        <= self._receiver_trigger_distance_m(case_id)
                    ):
                        return True
                elif (
                    transported
                    and receiver is not None
                    and eef is not None
                    and np.linalg.norm(eef - receiver)
                    <= self._receiver_trigger_distance_m(case_id)
                ):
                    if case_id == "D03" and self._d03_receiver_selection() == "active_goal_path":
                        self._dynamic_active_goal_target = goal_target
                    return True
            if case_id in {"D02", "D03", "D05", "D19"}:
                return False
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
