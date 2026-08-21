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

S22_COMPILED_TEXTURES = {
    "s22_table_texture": "textures/table_light_wood.png",
}

# S05's barrier is 0.08 m wide on either side of its local centre line. Keep
# the carried-object corridor clear even for the largest standard LIBERO
# object and leave a small modelling margin for the gripper/object envelope.
S05_BARRIER_HALF_WIDTH_M = 0.08
# The generated panel is thin in the direction used to route around it.  Do
# not use its 3-D bounding-sphere radius for this lateral clearance.
S05_BARRIER_HALF_THICKNESS_M = 0.012
S05_CARRIED_OBJECT_RADIUS_M = 0.05
S05_TRANSPORT_MARGIN_M = 0.02
S05_MIN_LATERAL_OFFSET_M = (
    S05_BARRIER_HALF_WIDTH_M
    + S05_CARRIED_OBJECT_RADIUS_M
    + S05_TRANSPORT_MARGIN_M
)
S05_DEFAULT_LATERAL_OFFSET_M = S05_MIN_LATERAL_OFFSET_M

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


@dataclass(frozen=True)
class GoalPath:
    target_name: str
    target_position: np.ndarray
    receiver_name: str
    anchor_name: str
    receiver_position: np.ndarray


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

    index = _asset_index(asset_root)
    staged = case_id.startswith("D")
    params = fields.get("params", {})
    if not isinstance(params, dict):
        params = {}
    asset_scale = 1.35 if case_id == "D03" else 1.0
    if case_id in CASE_ASSETS and "asset_scale" in params:
        try:
            asset_scale = float(params["asset_scale"])
        except (TypeError, ValueError) as exc:
            raise PerturbationConfigurationError(
                f"{case_id} asset_scale must be numeric; got {params['asset_scale']!r}"
            ) from exc
        if not np.isfinite(asset_scale) or asset_scale <= 0.0:
            raise PerturbationConfigurationError(
                f"{case_id} asset_scale must be positive; got {asset_scale!r}"
            )
    configured_asset_id = params.get("asset_id")
    asset_ids = CASE_ASSETS.get(case_id, ())
    if configured_asset_id and asset_ids:
        # BDDL may select a task-specific, semantics-preserving asset (for
        # example a bottle in front of a drawer handle) without changing the
        # shared operator implementation.
        asset_ids = (str(configured_asset_id),)
    assets = [
        _resolve_asset(asset_id, asset_root, index, staged=staged, scale=asset_scale)
        for asset_id in asset_ids
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


def _replacement_fit_scale(
    original: Any,
    replacement: Any,
    requested_scale: float,
    tolerance: float = 1.05,
) -> float:
    """Cap an S06 replacement to the source instance's graspable envelope."""

    limits = [float(requested_scale)]
    try:
        source_radius = abs(float(original.horizontal_radius))
        replacement_radius = abs(float(replacement.horizontal_radius))
        if source_radius > 1e-9 and replacement_radius > 1e-9:
            limits.append(tolerance * source_radius / replacement_radius)
    except (AttributeError, TypeError, ValueError, IndexError):
        pass
    try:
        source_height = abs(
            float(np.asarray(original.top_offset)[-1])
            - float(np.asarray(original.bottom_offset)[-1])
        )
        replacement_height = abs(
            float(np.asarray(replacement.top_offset)[-1])
            - float(np.asarray(replacement.bottom_offset)[-1])
        )
        if source_height > 1e-9 and replacement_height > 1e-9:
            limits.append(tolerance * source_height / replacement_height)
    except (AttributeError, TypeError, ValueError, IndexError):
        pass
    finite_limits = [limit for limit in limits if np.isfinite(limit) and limit > 0.0]
    if not finite_limits:
        raise PerturbationConfigurationError(
            f"S06 replacement scale must be finite and positive, got {requested_scale!r}"
        )
    return min(finite_limits)


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
                # A fixture-targeted S06 is a geometry/appearance variant. It
                # is handled after compilation by the runtime; replacing an
                # articulated fixture with a free-standing XML object would
                # destroy its joints and task semantics.
                if not plan.params.get("fixture_variant"):
                    raise PerturbationConfigurationError(
                        f"Replacement target {target!r} is not a movable scene object"
                    )
                continue
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
            applied_scale = _replacement_fit_scale(
                original, replacement, asset.scale
            )
            _scale_mujoco_object(replacement, applied_scale)
            replacement._libero_pro_replacement_scale = applied_scale
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
        if plan.case_id == "S03" and "asset_geometry_factors" in plan.params:
            raw_factors = np.asarray(
                plan.params["asset_geometry_factors"], dtype=np.float64
            )
            if (
                raw_factors.shape != (3,)
                or not np.all(np.isfinite(raw_factors))
                or np.any(raw_factors <= 0.0)
            ):
                raise PerturbationConfigurationError(
                    "S03 asset_geometry_factors must contain three positive finite values"
                )
            _scale_mujoco_object_vector(
                obj, tuple(float(value) for value in raw_factors)
            )
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
    # MujocoXMLObject keeps a worldbody template and a separate root returned
    # by get_obj(); ManipulationTask compiles the latter.  Scale both copies so
    # structural injected assets do not silently retain their original size.
    roots: list[Any] = []
    worldbody = getattr(obj, "worldbody", None)
    if worldbody is not None:
        roots.append(worldbody)
    try:
        compiled_root = obj.get_obj()
    except Exception:
        compiled_root = None
    if compiled_root is not None and all(compiled_root is not root for root in roots):
        roots.append(compiled_root)
    for root in roots:
        for element in root.findall(".//*[@pos]"):
            element.set("pos", _scale_xml_values(element.get("pos"), factor))
        for geom in root.findall(".//geom"):
            if geom.get("size"):
                geom.set("size", _scale_xml_values(geom.get("size"), factor))


def _scale_mujoco_object_vector(
    obj: Any, factors: tuple[float, float, float]
) -> None:
    """Scale one injected primitive anisotropically before MuJoCo compiles it."""

    if hasattr(obj, "asset"):
        for mesh in obj.asset.findall("mesh"):
            mesh.set(
                "scale", _scale_xml_vector(mesh.get("scale", "1 1 1"), factors)
            )
    roots: list[Any] = []
    worldbody = getattr(obj, "worldbody", None)
    if worldbody is not None:
        roots.append(worldbody)
    try:
        compiled_root = obj.get_obj()
    except Exception:
        compiled_root = None
    if compiled_root is not None and all(compiled_root is not root for root in roots):
        roots.append(compiled_root)
    for root in roots:
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
    fixture_s06 = plan.case_id == "S06" and any(
        name in fixtures_dict for name in plan.targets
    )
    if plan.case_id not in {"S07", "S08", "S09"} and not fixture_s06:
        return ()
    entities = {**fixtures_dict, **objects_dict}
    changed: list[str] = []
    def factors_for(key: str, default: tuple[float, float, float]) -> tuple[float, float, float]:
        raw = plan.params.get(key)
        if raw is None:
            return default
        values = np.asarray(raw, dtype=np.float64)
        if values.shape != (3,) or not np.all(np.isfinite(values)) or np.any(values <= 0.0):
            raise PerturbationConfigurationError(
                f"{plan.case_id} {key} must contain three positive finite values"
            )
        return tuple(float(value) for value in values)

    if fixture_s06:
        factors = factors_for("geometry_factors", (1.08, 1.08, 1.0))
        transforms = {name: factors for name in plan.targets}
    elif plan.case_id == "S07":
        factors = factors_for("geometry_factors", (1.0, 0.64, 1.20))
        transforms = {name: factors for name in plan.targets}
    elif plan.case_id == "S08":
        factors = factors_for("geometry_factors", (1.35, 0.72, 1.0))
        transforms = {name: factors for name in plan.targets}
    else:
        target_factors = factors_for("target_geometry_factors", (1.12, 1.12, 1.12))
        receiver_factors = factors_for("receiver_geometry_factors", (0.90, 0.90, 0.90))
        transforms: dict[str, tuple[float, float, float]] = {}
        for index, name in enumerate(plan.targets):
            factors = target_factors if index == 0 else receiver_factors
            if name in transforms:
                # Some LIBERO goals name the same body as both target and
                # receiver. Keep the stronger target geometry instead of
                # silently overwriting it with the receiver shrink factor.
                factors = tuple(
                    max(previous, current)
                    for previous, current in zip(transforms[name], factors)
                )
            transforms[name] = factors
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
        if name == receiver_name or name in fixtures_dict:
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


def _entity_is_movable(env: Any, name: str) -> bool:
    """Return whether an entity has a free joint and can be replaced safely."""

    obj = getattr(env, "objects_dict", {}).get(name)
    if obj is not None:
        return bool(getattr(obj, "joints", None))
    return name in getattr(env, "obj_body_id", {})


def _entity_semantic_category(env: Any, name: str) -> str:
    """Return the stable object category used to detect visually equivalent pairs."""

    obj = getattr(env, "objects_dict", {}).get(name)
    category = getattr(obj, "category_name", None) if obj is not None else None
    if category:
        return str(category).casefold()
    # Test doubles and lightweight evaluators often only expose BDDL names.
    head, separator, suffix = str(name).rpartition("_")
    return head.casefold() if separator and suffix.isdigit() else str(name).casefold()


def _scene_entity_names(env: Any) -> tuple[str, ...]:
    names = list(getattr(env, "obj_body_id", {}).keys())
    for support_name in ("main_table", "floor"):
        if _entity_exists(env, support_name) and support_name not in names:
            names.append(support_name)
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


def _entity_xy_radius(env: Any, name: str) -> float:
    """Return a conservative horizontal radius from MuJoCo geom bounds."""

    model = getattr(getattr(env, "sim", None), "model", None)
    if model is None or not hasattr(model, "geom_bodyid") or not hasattr(model, "geom_rbound"):
        return 0.0
    try:
        body_ids = set(_entity_body_ids(env, name))
        values = [
            float(model.geom_rbound[index])
            for index, body_id in enumerate(model.geom_bodyid)
            if int(body_id) in body_ids
        ]
    except Exception:
        return 0.0
    return max([0.0, *values])


def _entity_vertical_radius(env: Any, name: str) -> float:
    """Return a conservative vertical extent for support-preserving placement."""

    return _entity_xy_radius(env, name)


def _entity_bottom_offset(env: Any, name: str) -> float:
    """Return the root-body height above the lowest compiled geom AABB."""

    model = getattr(getattr(env, "sim", None), "model", None)
    data = getattr(getattr(env, "sim", None), "data", None)
    if (
        model is None
        or data is None
        or not hasattr(model, "geom_aabb")
        or not hasattr(data, "geom_xmat")
    ):
        return _entity_vertical_radius(env, name)
    body_id = _entity_body_id(env, name)
    body_ids = set(_entity_body_ids(env, name))
    collision_bottoms: list[float] = []
    all_bottoms: list[float] = []
    for geom_id, geom_body_id in enumerate(model.geom_bodyid):
        if int(geom_body_id) not in body_ids:
            continue
        aabb = np.asarray(model.geom_aabb[geom_id], dtype=np.float64)
        rotation = np.asarray(data.geom_xmat[geom_id], dtype=np.float64).reshape(3, 3)
        center = np.asarray(data.geom_xpos[geom_id], dtype=np.float64) + rotation @ aabb[:3]
        vertical_extent = float(np.abs(rotation[2]) @ aabb[3:])
        bottom = float(center[2] - vertical_extent)
        all_bottoms.append(bottom)
        if not hasattr(model, "geom_group") or int(model.geom_group[geom_id]) == 0:
            collision_bottoms.append(bottom)
    bottoms = collision_bottoms or all_bottoms
    if not bottoms:
        return _entity_vertical_radius(env, name)
    return max(0.0, float(data.body_xpos[body_id, 2]) - min(bottoms))


def _entity_top_offset(env: Any, name: str) -> float:
    """Return the root-body height above the highest compiled geom AABB."""

    model = getattr(getattr(env, "sim", None), "model", None)
    data = getattr(getattr(env, "sim", None), "data", None)
    if (
        model is None
        or data is None
        or not hasattr(model, "geom_aabb")
        or not hasattr(data, "geom_xmat")
    ):
        return _entity_vertical_radius(env, name)
    body_id = _entity_body_id(env, name)
    body_ids = set(_entity_body_ids(env, name))
    tops: list[float] = []
    for geom_id, geom_body_id in enumerate(model.geom_bodyid):
        if int(geom_body_id) not in body_ids:
            continue
        aabb = np.asarray(model.geom_aabb[geom_id], dtype=np.float64)
        rotation = np.asarray(data.geom_xmat[geom_id], dtype=np.float64).reshape(3, 3)
        center = np.asarray(data.geom_xpos[geom_id], dtype=np.float64) + rotation @ aabb[:3]
        vertical_extent = float(np.abs(rotation[2]) @ aabb[3:])
        tops.append(float(center[2] + vertical_extent))
    if not tops:
        return _entity_vertical_radius(env, name)
    return max(0.0, max(tops) - float(data.body_xpos[body_id, 2]))


def _collision_support_below(
    env: Any,
    moving_name: str,
    origin: np.ndarray,
) -> tuple[float, str]:
    """Raycast downward, accepting scene geometry but skipping robot links."""

    import mujoco

    model = env.sim.model
    data = env.sim.data
    support_body_ids: set[int] = set()
    for entity_name in _scene_entity_names(env):
        if entity_name == moving_name:
            continue
        try:
            support_body_ids.update(_entity_body_ids(env, entity_name))
        except PerturbationValidationError:
            continue
    # Arena supports are not consistently assigned to collision group 0.
    # For example, FloorArena's collidable floor geom is in group 1. Query
    # every group, then use the scene-body allowlist below to reject robot
    # and decorative geometry.
    geom_group = np.ones(6, dtype=np.uint8)
    ray_origin = np.asarray(origin, dtype=np.float64).copy()
    for _ in range(24):
        geom_id = np.array([-1], dtype=np.int32)
        distance = float(
            mujoco.mj_ray(
                model._model,
                data._data,
                ray_origin,
                np.array([0.0, 0.0, -1.0]),
                geom_group,
                1,
                _entity_body_id(env, moving_name),
                geom_id,
            )
        )
        if distance < 0.0 or geom_id[0] < 0:
            break
        hit_height = float(ray_origin[2] - distance)
        hit_body = int(model.geom_bodyid[int(geom_id[0])])
        if hit_body in support_body_ids:
            support_name = str(model.geom_id2name(int(geom_id[0])) or geom_id[0])
            return hit_height, support_name
        ray_origin[2] = hit_height - 0.002
    raise PerturbationValidationError(
        f"No collision support surface below {moving_name!r} at {origin[:2].tolist()}"
    )


def _ground_entity_on_support(
    env: Any,
    name: str,
    candidate: np.ndarray,
    quaternion: np.ndarray,
) -> tuple[np.ndarray, str]:
    """Place an entity on the highest collision surface below a candidate XY."""

    original_position, original_quaternion = _entity_pose(env, name)
    workspace = np.asarray(getattr(env, "workspace_offset", [0.0, 0.0, 0.9]))
    probe = np.asarray(candidate, dtype=np.float64).copy()
    probe[2] = max(float(workspace[2]) + 0.65, float(original_position[2]) + 0.30)
    try:
        _set_entity_pose(env, name, probe, quaternion)
        model = getattr(env.sim, "model", None)
        data = getattr(env.sim, "data", None)
        if not hasattr(model, "_model") or not hasattr(data, "_data"):
            # Lightweight test doubles do not expose MuJoCo's native ray API;
            # retain their requested pose and let their contact stubs validate it.
            _set_entity_pose(env, name, np.asarray(candidate, dtype=np.float64), quaternion)
            _zero_free_joint_velocity(env, name)
            return np.asarray(candidate, dtype=np.float64).copy(), "test-support"
        bottom_offset = _entity_bottom_offset(env, name)
        bottom = float(probe[2] - bottom_offset)
        support_height: float
        support_name = "workspace"
        try:
            import mujoco

            origin = np.array([probe[0], probe[1], bottom + 0.002])
            support_height, support_name = _collision_support_below(
                env, name, origin
            )
        except (ImportError, AttributeError):
            support_height = float(workspace[2])
        grounded = probe.copy()
        grounded[2] = support_height + bottom_offset + 0.001
        _set_entity_pose(env, name, grounded, quaternion)
        _zero_free_joint_velocity(env, name)
        if _entity_has_penetrating_contact(env, name):
            raise PerturbationValidationError(
                f"Grounded pose for {name!r} penetrates another scene entity"
            )
        return grounded, support_name
    except Exception:
        _set_entity_pose(env, name, original_position, original_quaternion)
        _zero_free_joint_velocity(env, name)
        raise


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


def _zero_free_joint_velocity(env: Any, name: str) -> None:
    """Clear stale free-joint velocity after a nonphysical pose update."""

    obj = getattr(env, "objects_dict", {}).get(name)
    joints = list(getattr(obj, "joints", []) or []) if obj is not None else []
    model = getattr(getattr(env, "sim", None), "model", None)
    data = getattr(getattr(env, "sim", None), "data", None)
    if not joints or model is None or data is None or not hasattr(data, "qvel"):
        return
    for joint in joints:
        try:
            address = model.get_joint_qvel_addr(joint)
            if isinstance(address, tuple):
                data.qvel[address[0] : address[1]] = 0.0
            else:
                data.qvel[address] = 0.0
        except Exception:
            continue


def _yaw_quaternion(yaw: float) -> np.ndarray:
    return np.array([math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)])


def _axis_angle_quaternion(axis: str, angle: float) -> np.ndarray:
    half = float(angle) / 2.0
    sine = math.sin(half)
    vectors = {
        "x": (sine, 0.0, 0.0),
        "y": (0.0, sine, 0.0),
        "z": (0.0, 0.0, sine),
    }
    if axis not in vectors:
        raise PerturbationConfigurationError(
            f"Replacement rotation axis must be x, y, or z; got {axis!r}"
        )
    return np.array([math.cos(half), *vectors[axis]], dtype=np.float64)


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
    moving_radius: float = 0.0,
) -> bool:
    x_min, x_max, y_min, y_max = _workspace_bounds(env)
    margin = max(0.0, float(moving_radius))
    if not (
        x_min + margin <= candidate_xy[0] <= x_max - margin
        and y_min + margin <= candidate_xy[1] <= y_max - margin
    ):
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


def _candidate_is_clear_of_objects(
    env: Any,
    moving_name: str,
    candidate_xy: np.ndarray,
    *,
    extra_gap: float = 0.01,
    ignored: tuple[str, ...] = (),
) -> bool:
    """Use compiled geom radii to prevent injected assets overlapping objects."""

    moving_radius = _entity_xy_radius(env, moving_name)
    for name in getattr(env, "objects_dict", {}):
        if name == moving_name or name in ignored:
            continue
        if not _entity_exists(env, name):
            continue
        other, _ = _entity_pose(env, name)
        clearance = moving_radius + _entity_xy_radius(env, name) + float(extra_gap)
        if np.linalg.norm(np.asarray(candidate_xy) - other[:2]) < clearance:
            return False
    return True


def _workspace_position_candidates(
    env: Any,
    moving_name: str,
    reference: np.ndarray,
) -> list[np.ndarray]:
    """Return deterministic whole-workspace fallbacks ordered near a reference."""

    x_min, x_max, y_min, y_max = _workspace_bounds(env)
    margin = max(0.03, _entity_xy_radius(env, moving_name) + 0.01)
    if x_min + margin >= x_max - margin or y_min + margin >= y_max - margin:
        margin = 0.02
    candidates = [
        np.array([x, y, float(reference[2])], dtype=np.float64)
        for x in np.linspace(x_min + margin, x_max - margin, 9)
        for y in np.linspace(y_min + margin, y_max - margin, 11)
    ]
    candidates.sort(
        key=lambda candidate: (
            abs(float(np.linalg.norm(candidate[:2] - reference[:2])) - 0.22),
            float(candidate[0]),
            float(candidate[1]),
        )
    )
    return candidates


def _candidate_is_geometrically_clear(
    env: Any,
    moving_name: str,
    candidate_position: np.ndarray,
    *,
    minimum_gap: float = 0.005,
    ignored: tuple[str, ...] = (),
) -> bool:
    """Reject visual overlap even when an injected asset has no collision bits."""

    moving_radius = _entity_xy_radius(env, moving_name)
    candidate = np.asarray(candidate_position, dtype=np.float64)
    for name in _scene_entity_names(env):
        if name == moving_name or name in ignored:
            continue
        try:
            other, _ = _entity_pose(env, name)
        except PerturbationValidationError:
            continue
        other_radius = _entity_xy_radius(env, name)
        if np.linalg.norm(candidate - other) < moving_radius + other_radius + minimum_gap:
            return False
    return True


def _candidate_is_clear_of_eef(
    env: Any, moving_name: str, candidate_position: np.ndarray, extra_gap: float = 0.02
) -> bool:
    """Keep injected visual assets out of the current gripper envelope."""

    try:
        eef = np.asarray(
            env.sim.data.site_xpos[env.robots[0].eef_site_id], dtype=np.float64
        )
    except Exception:
        return True
    moving_radius = _entity_xy_radius(env, moving_name)
    # The gripper fingers extend beyond the EEF site; use a conservative proxy
    # so an occluder cannot be spawned through the hand as in the review videos.
    return bool(
        np.linalg.norm(np.asarray(candidate_position) - eef)
        >= moving_radius + 0.055 + float(extra_gap)
    )


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
    env: Any,
    name: str,
    tolerance: float = -1e-4,
    ignored: tuple[str, ...] = (),
) -> bool:
    data = env.sim.data
    if int(getattr(data, "ncon", 0)) == 0:
        return False
    body_ids = set(_entity_body_ids(env, name))
    model = env.sim.model
    ignored_body_ids: set[int] = set()
    for ignored_name in (*ignored, "main_table", "floor"):
        try:
            ignored_body_ids.update(_entity_body_ids(env, ignored_name))
        except PerturbationValidationError:
            continue
    scene_body_ids: set[int] = set()
    for scene_name in _scene_entity_names(env):
        try:
            scene_body_ids.update(_entity_body_ids(env, scene_name))
        except PerturbationValidationError:
            continue
    for index in range(int(getattr(data, "ncon", 0))):
        contact = data.contact[index]
        first_body = int(model.geom_bodyid[int(contact.geom1)])
        second_body = int(model.geom_bodyid[int(contact.geom2)])
        if first_body in body_ids:
            other_body = second_body
        elif second_body in body_ids:
            other_body = first_body
        else:
            continue
        if other_body in ignored_body_ids or other_body not in scene_body_ids:
            continue
        if float(contact.dist) < float(tolerance):
            return True
    return False


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
    model = env.sim.model
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


def _entity_has_support_contact(env: Any, name: str, tolerance: float = 0.005) -> bool:
    """Return whether an object still touches a scene body after a teleport.

    Lightweight test doubles do not expose MuJoCo contacts; those callers keep
    the previous permissive behavior while real simulations validate support.
    """

    data = getattr(getattr(env, "sim", None), "data", None)
    if data is None or not hasattr(data, "ncon") or not hasattr(data, "contact"):
        return True
    ncon = int(getattr(data, "ncon", 0))
    if ncon <= 0:
        return True
    body_ids = set(_entity_body_ids(env, name))
    model = env.sim.model
    scene_body_ids: set[int] = set()
    for scene_name in _scene_entity_names(env):
        try:
            scene_body_ids.update(_entity_body_ids(env, scene_name))
        except PerturbationValidationError:
            continue
    try:
        object_position, _ = _entity_pose(env, name)
    except PerturbationValidationError:
        return False
    for index in range(ncon):
        contact = data.contact[index]
        first_body = int(model.geom_bodyid[int(contact.geom1)])
        second_body = int(model.geom_bodyid[int(contact.geom2)])
        if first_body in body_ids:
            other_body = second_body
        elif second_body in body_ids:
            other_body = first_body
        else:
            continue
        if other_body not in scene_body_ids:
            continue
        if float(contact.dist) <= float(tolerance):
            try:
                other_position = np.asarray(env.sim.data.body_xpos[other_body])
                if other_position[2] <= object_position[2] + 0.02:
                    return True
            except Exception:
                return True
    return False


def _visible_clutter_pose(
    env: Any,
    moving_name: str,
    reference_name: str,
    *,
    minimum_gap: float = 0.10,
    requested_radius: float = 0.14,
) -> np.ndarray:
    reference, _ = _entity_pose(env, reference_name)
    original_position, original_quaternion = _entity_pose(env, moving_name)
    clutter_quaternion = _yaw_quaternion(0.0)
    base_angle = math.atan2(-0.12, 0.16)
    candidates: list[np.ndarray] = []
    radius = max(0.08, float(requested_radius))
    for radius in (radius, radius * 1.25, radius * 1.55, radius * 1.90, radius * 2.20):
        for angle_offset in np.linspace(0.0, 2.0 * math.pi, 16, endpoint=False):
            angle = base_angle + float(angle_offset)
            candidate = reference.copy()
            candidate[:2] += radius * np.array([math.cos(angle), math.sin(angle)])
            candidates.append(candidate)
    candidates.extend(_workspace_position_candidates(env, moving_name, reference))

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
        if not _candidate_is_clear_of_objects(
            env, moving_name, candidate[:2], extra_gap=0.01
        ) or not _candidate_is_clear_of_eef(env, moving_name, candidate):
            continue
        try:
            grounded, _ = _ground_entity_on_support(
                env, moving_name, candidate, clutter_quaternion
            )
        except PerturbationValidationError:
            continue
        if not _entity_has_penetrating_contact(
            env, moving_name
        ) and _candidate_is_clear_of_eef(env, moving_name, grounded):
            return grounded
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
    keep_support: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    before, quat = _entity_pose(env, name)
    moving_radius = _entity_xy_radius(env, name)
    had_support = _entity_has_support_contact(env, name)
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
        if not _candidate_is_clear(
            env,
            name,
            candidate[:2],
            minimum_gap,
            ignored,
            moving_radius=moving_radius,
        ):
            continue
        _set_entity_pose(env, name, candidate, quat)
        _zero_free_joint_velocity(env, name)
        if _entity_has_penetrating_contact(env, name, ignored=ignored) or (
            keep_support and had_support and not _entity_has_support_contact(env, name)
        ):
            _set_entity_pose(env, name, before, quat)
            _zero_free_joint_velocity(env, name)
            continue
        return before, candidate, delta
    raise PerturbationValidationError(
        f"No collision-clear workspace position for {name!r} near {before[:2].tolist()}"
    )


def _safe_asset_near_reference_pose(
    env: Any,
    moving_name: str,
    reference_name: str,
    requested_offset: tuple[float, float],
    *,
    minimum_gap: float = 0.06,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Place an injected distractor near a task object without overlap or drift."""

    reference, _ = _entity_pose(env, reference_name)
    original, original_quat = _entity_pose(env, moving_name)
    upright_quaternion = _yaw_quaternion(0.0)
    requested = np.asarray(requested_offset, dtype=np.float64)
    if requested.shape != (2,) or not np.all(np.isfinite(requested)):
        raise PerturbationConfigurationError(
            "Injected asset offset must contain two finite values"
        )
    distance = max(
        float(np.linalg.norm(requested)),
        minimum_gap * 1.5,
        _entity_xy_radius(env, moving_name)
        + _entity_xy_radius(env, reference_name)
        + 0.015,
    )
    base_angle = math.atan2(float(requested[1]), float(requested[0]))
    candidates: list[np.ndarray] = []
    last_error: str | None = None
    for radius in (distance, distance * 1.20, distance * 1.45, distance * 1.80):
        for angle_offset in np.linspace(0.0, 2.0 * math.pi, 16, endpoint=False):
            angle = base_angle + float(angle_offset)
            candidate = reference.copy()
            candidate[:2] += radius * np.array([math.cos(angle), math.sin(angle)])
            candidates.append(candidate)
    candidates.extend(_workspace_position_candidates(env, moving_name, reference))
    for candidate in candidates:
        if not _candidate_is_clear(
            env,
            moving_name,
            candidate[:2],
            minimum_gap,
            ignored=("main_table", "floor"),
            moving_radius=_entity_xy_radius(env, moving_name),
        ):
            continue
        if not _candidate_is_clear_of_objects(
            env, moving_name, candidate[:2], extra_gap=0.01
        ) or not _candidate_is_clear_of_eef(env, moving_name, candidate):
            continue
        try:
            grounded, _ = _ground_entity_on_support(
                env, moving_name, candidate, upright_quaternion
            )
        except PerturbationValidationError as exc:
            last_error = str(exc)
            continue
        if _entity_has_penetrating_contact(
            env, moving_name, ignored=("main_table", "floor")
        ) or not _candidate_is_clear_of_eef(env, moving_name, grounded):
            _set_entity_pose(env, moving_name, original, original_quat)
            _zero_free_joint_velocity(env, moving_name)
            continue
        return reference, grounded, grounded - reference
    _set_entity_pose(env, moving_name, original, original_quat)
    _zero_free_joint_velocity(env, moving_name)
    raise PerturbationValidationError(
        f"No collision-clear near-reference position for {moving_name!r} near {reference_name!r}"
        + (f" ({last_error})" if last_error else "")
    )


def _safe_support_riser_layout(
    env: Any,
    target_name: str,
    riser_name: str,
    height_delta: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Raise one target on a real riser without intersecting nearby objects.

    The target and riser are searched as a coupled pair. This prevents the
    old failure mode where the target was lifted in place while the riser was
    left underneath another object, making the entire tabletop appear to
    jump or creating negative contact distances.
    """

    target_before, target_quaternion = _entity_pose(env, target_name)
    riser_before, riser_quaternion = _entity_pose(env, riser_name)
    original_target = target_before.copy()
    original_riser = riser_before.copy()
    offsets = [
        np.zeros(2, dtype=np.float64),
        np.array([0.018, 0.0]),
        np.array([-0.018, 0.0]),
        np.array([0.0, 0.018]),
        np.array([0.0, -0.018]),
        np.array([0.025, 0.018]),
        np.array([-0.025, -0.018]),
    ]
    # Temporarily remove the target so the riser can be grounded beneath it.
    staged_target = target_before.copy()
    staged_target[2] = -5.0
    _set_entity_pose(env, target_name, staged_target, target_quaternion)
    try:
        for offset in offsets:
            target_candidate = target_before.copy()
            target_candidate[:2] += offset
            riser_candidate = target_candidate.copy()
            try:
                grounded_riser, support_name = _ground_entity_on_support(
                    env, riser_name, riser_candidate, riser_quaternion
                )
            except PerturbationValidationError:
                continue
            grounded_target = target_candidate.copy()
            grounded_target[2] = (
                grounded_riser[2]
                + _entity_top_offset(env, riser_name)
                + _entity_bottom_offset(env, target_name)
                + 0.001
            )
            _set_entity_pose(env, target_name, grounded_target, target_quaternion)
            if _entity_has_penetrating_contact(env, target_name) or _entity_has_penetrating_contact(
                env, riser_name
            ):
                _set_entity_pose(env, target_name, staged_target, target_quaternion)
                continue
            return grounded_target, grounded_riser, grounded_target - target_before, support_name
    finally:
        # The successful branch has already installed both poses. On failure,
        # restore the exact original state and clear stale velocities.
        if not np.isfinite(_entity_pose(env, target_name)[0]).all() or _entity_pose(env, target_name)[0][2] < -4.0:
            _set_entity_pose(env, target_name, original_target, target_quaternion)
        if not np.isfinite(_entity_pose(env, riser_name)[0]).all() or _entity_pose(env, riser_name)[0][2] < -4.0:
            _set_entity_pose(env, riser_name, original_riser, riser_quaternion)
    _set_entity_pose(env, target_name, original_target, target_quaternion)
    _set_entity_pose(env, riser_name, original_riser, riser_quaternion)
    raise PerturbationValidationError(
        f"No collision-clear coupled support layout for {target_name!r} and {riser_name!r}"
    )


def _articulation_part_anchor(env: Any, entity_name: str, token: str) -> np.ndarray:
    """Find a named articulated part (button/handle) in world coordinates."""

    token = str(token).casefold()
    body_ids = set(_entity_body_ids(env, entity_name))
    model = env.sim.model
    data = env.sim.data
    for geom_id in range(int(model.ngeom)):
        body_id = int(model.geom_bodyid[geom_id])
        if body_id not in body_ids:
            continue
        geom_name = str(model.geom_id2name(geom_id) or "").casefold()
        if token in geom_name:
            return np.asarray(data.geom_xpos[geom_id], dtype=np.float64).copy()
    for body_id in body_ids:
        body_name = str(model.body_id2name(body_id) or "").casefold()
        if token in body_name:
            return np.asarray(data.body_xpos[body_id], dtype=np.float64).copy()
    return _functional_anchor(env, entity_name)[0]


def _safe_grounded_asset_near_point(
    env: Any,
    moving_name: str,
    anchor: np.ndarray,
    requested_offset: tuple[float, float],
) -> tuple[np.ndarray, str]:
    """Ground an injected blocker near a functional point with full clearance."""

    original_position, original_quaternion = _entity_pose(env, moving_name)
    requested = np.asarray(requested_offset, dtype=np.float64)
    distance = max(float(np.linalg.norm(requested)), 0.08)
    angle = math.atan2(float(requested[1]), float(requested[0]))
    candidates: list[np.ndarray] = []
    for radius in (distance, distance * 1.25, distance * 1.55, distance * 1.9):
        for offset in np.linspace(0.0, 2.0 * math.pi, 16, endpoint=False):
            candidate = np.asarray(anchor, dtype=np.float64).copy()
            candidate[:2] += radius * np.array(
                [math.cos(angle + float(offset)), math.sin(angle + float(offset))]
            )
            candidates.append(candidate)
    candidates.extend(_workspace_position_candidates(env, moving_name, np.asarray(anchor)))
    for candidate in candidates:
        if not _candidate_is_clear(
            env,
            moving_name,
            candidate[:2],
            0.04,
            ignored=("main_table", "floor"),
            moving_radius=_entity_xy_radius(env, moving_name),
        ):
            continue
        if not _candidate_is_clear_of_objects(
            env, moving_name, candidate[:2], extra_gap=0.01
        ) or not _candidate_is_clear_of_eef(env, moving_name, candidate):
            continue
        try:
            grounded, support_name = _ground_entity_on_support(
                env, moving_name, candidate, _yaw_quaternion(0.0)
            )
        except PerturbationValidationError:
            continue
        if not _entity_has_penetrating_contact(env, moving_name):
            return grounded, support_name
        _set_entity_pose(env, moving_name, original_position, original_quaternion)
    _set_entity_pose(env, moving_name, original_position, original_quaternion)
    raise PerturbationValidationError(
        f"No collision-clear grounded asset position for {moving_name!r} near {np.asarray(anchor)[:2].tolist()}"
    )


def _offset_goal_articulation_joint(
    env: Any, target_name: str, delta: float
) -> tuple[str, float, float]:
    """Move only the goal joint, preserving the fixture base pose."""

    goal_states = getattr(env, "parsed_problem", {}).get("goal_state", [])
    sites = getattr(env, "object_sites_dict", {})
    joints: list[str] = []
    for state in goal_states:
        if len(state) < 2:
            continue
        site = sites.get(str(state[1]))
        if site is not None and str(getattr(site, "parent_name", "")) == target_name:
            joints.extend(str(name) for name in getattr(site, "joints", ()) if name)
    if not joints:
        obj = getattr(env, "fixtures_dict", {}).get(target_name) or getattr(
            env, "objects_dict", {}
        ).get(target_name)
        joints = [str(name) for name in getattr(obj, "joints", ()) if name]
    for joint in joints:
        try:
            address = env.sim.model.get_joint_qpos_addr(joint)
            if isinstance(address, tuple):
                continue
            before = float(env.sim.data.qpos[address])
            joint_id = int(env.sim.model.joint_name2id(joint))
            low, high = np.asarray(env.sim.model.jnt_range[joint_id], dtype=np.float64)
            after = float(np.clip(before + float(delta), low + 0.005, high - 0.005))
            if abs(after - before) < 1e-5:
                after = float(np.clip(before - float(delta), low + 0.005, high - 0.005))
            env.sim.data.qpos[address] = after
            env.sim.forward()
            return joint, before, after
        except Exception:
            continue
    raise PerturbationValidationError(
        f"No goal articulation joint can be safely offset for {target_name!r}"
    )


def _rearrange_unrelated_objects(
    env: Any,
    excluded: tuple[str, ...],
    requested_offsets: tuple[tuple[float, float], ...] = (
        (0.12, -0.09),
        (-0.11, 0.10),
        (0.08, 0.13),
    ),
) -> tuple[list[dict[str, Any]], int]:
    """Move up to three non-goal tabletop objects to grounded safe poses."""

    excluded_set = set(excluded) | {"main_table", "floor"}
    candidates = [
        name
        for name in getattr(env, "objects_dict", {})
        if name not in excluded_set and _entity_exists(env, name) and _entity_is_movable(env, name)
    ]
    moved: list[dict[str, Any]] = []
    requested_count = min(3, len(candidates))
    required_count = min(2, len(candidates))
    for name in candidates:
        if len(moved) >= requested_count:
            break
        requested = requested_offsets[min(len(moved), len(requested_offsets) - 1)]
        try:
            before, after, delta, support_name = _safe_grounded_layout_offset(
                env, name, requested
            )
        except PerturbationValidationError:
            continue
        moved.append(
            {
                "target": name,
                "before": before.tolist(),
                "after": after.tolist(),
                "delta_xy": delta.tolist(),
                "support_geom": support_name,
            }
        )
    return moved, required_count


def _safe_planar_object_swap(
    env: Any,
    first_name: str,
    second_name: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Swap XY positions while grounding both objects on their destination support."""

    first_before, first_quaternion = _entity_pose(env, first_name)
    second_before, second_quaternion = _entity_pose(env, second_name)
    if np.linalg.norm(first_before[:2] - second_before[:2]) < 0.02:
        raise PerturbationValidationError(
            f"S04 targets {first_name!r} and {second_name!r} share the same XY"
        )
    try:
        staged_first = first_before.copy()
        staged_second = second_before.copy()
        staged_first[2] = -5.0
        staged_second[2] = -5.0
        _set_entity_pose(env, first_name, staged_first, first_quaternion)
        _set_entity_pose(env, second_name, staged_second, second_quaternion)

        first_candidate = first_before.copy()
        first_candidate[:2] = second_before[:2]
        if not _candidate_is_clear_of_objects(
            env,
            first_name,
            first_candidate[:2],
            extra_gap=0.005,
            ignored=(second_name,),
        ):
            raise PerturbationValidationError(
                f"S04 destination is obstructed for {first_name!r}"
            )
        first_after, _ = _ground_entity_on_support(
            env, first_name, first_candidate, first_quaternion
        )

        second_candidate = second_before.copy()
        second_candidate[:2] = first_before[:2]
        if not _candidate_is_clear_of_objects(
            env,
            second_name,
            second_candidate[:2],
            extra_gap=0.005,
            ignored=(first_name,),
        ):
            raise PerturbationValidationError(
                f"S04 destination is obstructed for {second_name!r}"
            )
        second_after, _ = _ground_entity_on_support(
            env, second_name, second_candidate, second_quaternion
        )
        return first_before, first_after, second_before, second_after
    except Exception:
        _set_entity_pose(env, first_name, first_before, first_quaternion)
        _set_entity_pose(env, second_name, second_before, second_quaternion)
        _zero_free_joint_velocity(env, first_name)
        _zero_free_joint_velocity(env, second_name)
        raise


def _safe_grounded_layout_offset(
    env: Any,
    name: str,
    requested_offset: tuple[float, float] = (0.12, 0.08),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Find a visible collision-clear layout offset on a real support surface."""

    before, quaternion = _entity_pose(env, name)
    requested = np.asarray(requested_offset, dtype=np.float64)
    distance = max(float(np.linalg.norm(requested)), 0.10)
    base_angle = math.atan2(float(requested[1]), float(requested[0]))
    candidates: list[np.ndarray] = []
    for radius in (distance, distance * 1.25, distance * 1.50, distance * 1.80):
        for angle_offset in np.linspace(0.0, 2.0 * math.pi, 16, endpoint=False):
            angle = base_angle + float(angle_offset)
            delta = radius * np.array([math.cos(angle), math.sin(angle)])
            if not any(np.allclose(delta, existing) for existing in candidates):
                candidates.append(delta)
    candidates.extend(
        candidate[:2] - before[:2]
        for candidate in _workspace_position_candidates(env, name, before)
    )
    try:
        for delta in candidates:
            candidate = before.copy()
            candidate[:2] += delta
            if not _candidate_is_clear(
                env,
                name,
                candidate[:2],
                0.08,
                moving_radius=_entity_xy_radius(env, name),
            ):
                continue
            if not _candidate_is_clear_of_objects(
                env, name, candidate[:2], extra_gap=0.01
            ):
                continue
            if not _candidate_is_clear_of_eef(
                env, name, candidate, extra_gap=0.04
            ):
                continue
            try:
                after, support_name = _ground_entity_on_support(
                    env, name, candidate, quaternion
                )
            except PerturbationValidationError:
                continue
            if _entity_has_penetrating_contact(env, name) or not _candidate_is_clear_of_eef(
                env, name, after, extra_gap=0.04
            ):
                _set_entity_pose(env, name, before, quaternion)
                _zero_free_joint_velocity(env, name)
                continue
            return before, after, delta, support_name
    except Exception:
        _set_entity_pose(env, name, before, quaternion)
        _zero_free_joint_velocity(env, name)
        raise
    _set_entity_pose(env, name, before, quaternion)
    _zero_free_joint_velocity(env, name)
    raise PerturbationValidationError(
        f"No grounded collision-clear layout offset for {name!r} near {before[:2].tolist()}"
    )


def _segment_clear_for_carried_object(
    env: Any,
    start: np.ndarray,
    end: np.ndarray,
    carried_radius: float,
    *,
    ignored: tuple[str, ...],
) -> bool:
    """Conservatively test a short transport segment against scene bodies."""

    x_min, x_max, y_min, y_max = _workspace_bounds(env)
    margin = max(0.0, float(carried_radius))
    for fraction in np.linspace(0.0, 1.0, 13):
        point = np.asarray(start, dtype=np.float64) + float(fraction) * (
            np.asarray(end, dtype=np.float64) - np.asarray(start, dtype=np.float64)
        )
        if not (
            x_min + margin <= point[0] <= x_max - margin
            and y_min + margin <= point[1] <= y_max - margin
        ):
            return False
        for name in _scene_entity_names(env):
            if name in ignored:
                continue
            try:
                other, _ = _entity_pose(env, name)
            except PerturbationValidationError:
                continue
            endpoint_body = (
                np.linalg.norm(np.asarray(start)[:2] - other[:2]) < 1e-6
                or np.linalg.norm(np.asarray(end)[:2] - other[:2]) < 1e-6
            )
            if endpoint_body:
                continue
            if np.linalg.norm(point[:2] - other[:2]) < (
                carried_radius + _entity_xy_radius(env, name) + 0.015
            ):
                return False
    return True


def _transport_detour_exists(
    env: Any,
    target_position: np.ndarray,
    receiver_position: np.ndarray,
    barrier_position: np.ndarray,
    barrier_name: str,
    *,
    carried_radius: float,
    ignored_entities: tuple[str, ...] = (),
) -> bool:
    """Check that at least one side of a path obstacle remains traversable."""

    direction = np.asarray(receiver_position[:2] - target_position[:2], dtype=np.float64)
    length = float(np.linalg.norm(direction))
    if length < 1e-6:
        return False
    direction /= length
    normal = np.array([-direction[1], direction[0]])
    obstacle_longitudinal = max(S05_BARRIER_HALF_WIDTH_M, 0.08)
    longitudinal = obstacle_longitudinal * 1.25
    lateral = (
        S05_BARRIER_HALF_THICKNESS_M
        + float(carried_radius)
        + 0.025
    )
    center = np.asarray(barrier_position, dtype=np.float64)
    for sign in (-1.0, 1.0):
        side = normal * (sign * lateral)
        first = center.copy()
        second = center.copy()
        first[:2] -= direction * longitudinal
        second[:2] += direction * longitudinal
        first[:2] += side
        second[:2] += side
        # The detour check is for the carried object versus the injected
        # barrier. Treating every unrelated tabletop object as an immutable
        # route blocker made ordinary cluttered scenes reject D05 before the
        # obstacle could ever appear. Their actual contacts remain governed by
        # MuJoCo; this conservative planner only needs to preserve the carried
        # object's clearance and workspace bounds.
        # Support surfaces are not horizontal route blockers.  The carried
        # object travels above them, and treating the table/floor's large
        # compiled radius as an obstacle rejects otherwise valid detours.
        ignored = (barrier_name, "main_table", "floor", *ignored_entities)
        if all(
            _segment_clear_for_carried_object(
                env,
                start,
                end,
                carried_radius,
                ignored=ignored,
            )
            for start, end in (
                (target_position, first),
                (first, second),
                (second, receiver_position),
            )
        ):
            return True
    return False


def _safe_transport_barrier_pose(
    env: Any,
    barrier_name: str,
    target_position: np.ndarray,
    receiver_position: np.ndarray,
    *,
    requested_lateral_offset: float = 0.025,
    carried_object_name: str | None = None,
    receiver_name: str | None = None,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Place D05 on the nominal path only when an alternate route remains."""

    direction = np.asarray(receiver_position[:2] - target_position[:2], dtype=np.float64)
    length = float(np.linalg.norm(direction))
    if length < 1e-6:
        raise PerturbationValidationError("D05 needs distinct target and receiver anchors")
    direction /= length
    normal = np.array([-direction[1], direction[0]])
    barrier_quaternion = _yaw_quaternion(
        math.atan2(direction[1], direction[0]) + math.pi / 2
    )
    base = np.asarray(target_position, dtype=np.float64) + 0.62 * (
        np.asarray(receiver_position, dtype=np.float64) - np.asarray(target_position)
    )
    if carried_object_name is None:
        carried_object_name = next(iter(_goal_interaction_targets(env)), "")
    carried_radius = max(_entity_xy_radius(env, carried_object_name), 0.05)
    carried_ignored = (carried_object_name,) if carried_object_name else ()
    requested = max(abs(float(requested_lateral_offset)), 0.0)
    offsets = []
    for magnitude in (requested, 0.05, 0.075, 0.10, 0.125, 0.15, 0.18):
        if magnitude <= 1e-6:
            continue
        for sign in (1.0, -1.0):
            value = sign * magnitude
            if not any(abs(value - existing) < 1e-9 for existing in offsets):
                offsets.append(value)
    original_position, original_quaternion = _entity_pose(env, barrier_name)
    for lateral in offsets:
        candidate = base.copy()
        candidate[:2] += normal * lateral
        if not _candidate_is_clear(
            env,
            barrier_name,
            candidate[:2],
            minimum_gap=0.01,
            ignored=("main_table", "floor"),
            moving_radius=_entity_xy_radius(env, barrier_name),
        ):
            continue
        if not _candidate_is_clear_of_objects(
            env,
            barrier_name,
            candidate[:2],
            extra_gap=0.06,
            # The barrier is intentionally placed on the carried object's
            # nominal route.  A conservative bounding-sphere precheck would
            # reject every near-path candidate because it counts the carried
            # object itself as an unrelated obstacle.  The actual MuJoCo
            # penetration check below remains authoritative for contact.
            # The sphere precheck is too conservative for a thin barrier
            # placed near a cluttered route.  Let the real contact test below
            # decide whether the candidate actually overlaps an object.
            ignored=tuple(getattr(env, "objects_dict", {}).keys()),
        ):
            continue
        if not _candidate_is_clear_of_eef(env, barrier_name, candidate):
            continue
        try:
            candidate, _ = _ground_entity_on_support(
                env, barrier_name, candidate, barrier_quaternion
            )
        except PerturbationValidationError:
            continue
        if _entity_has_penetrating_contact(
            env, barrier_name, ignored=("main_table", "floor")
        ):
            _set_entity_pose(env, barrier_name, original_position, original_quaternion)
            continue
        if _transport_detour_exists(
            env,
            target_position,
            receiver_position,
            candidate,
            barrier_name,
            carried_radius=carried_radius,
            ignored_entities=carried_ignored + tuple(
                name
                for name in _scene_entity_names(env)
                if name != carried_object_name and _entity_is_movable(env, name)
            ) + ((receiver_name,) if receiver_name else ()),
        ):
            return candidate, barrier_quaternion, lateral
        # Static S05 is evaluated before a policy has selected its exact arm
        # corridor. If the conservative scene-wide detour check rejects every
        # candidate because of decorative/tabletop clutter, retain the
        # collision-checked blocker when a free side exists around the blocker
        # itself. The actual MuJoCo contact guard above still rejects overlap.
        relaxed_ignored = carried_ignored + tuple(
                name
                for name in _scene_entity_names(env)
                if name not in {barrier_name, carried_object_name}
        ) + ((receiver_name,) if receiver_name else ())
        if _transport_detour_exists(
            env,
            target_position,
            receiver_position,
            candidate,
            barrier_name,
            carried_radius=carried_radius,
            ignored_entities=relaxed_ignored,
        ):
            return candidate, barrier_quaternion, lateral
        _set_entity_pose(env, barrier_name, original_position, original_quaternion)
    _set_entity_pose(env, barrier_name, original_position, original_quaternion)
    raise PerturbationValidationError(
        "D05 could not place a path obstacle while preserving an alternate collision-free route"
    )


def _lift_receiver_contents(
    env: Any,
    receiver_name: str,
    receiver_before: np.ndarray,
    height_delta: float,
    *,
    excluded: tuple[str, ...] = (),
) -> list[str]:
    """Carry objects resting on a raised receiver by the same height delta."""

    receiver_radius = _entity_xy_radius(env, receiver_name)
    footprint_radius = min(max(receiver_radius * 0.65, 0.08), 0.16)
    moved: list[str] = []
    excluded_names = {receiver_name, "main_table", "floor", *excluded}
    for name in _scene_entity_names(env):
        if name in excluded_names or not _entity_is_movable(env, name):
            continue
        try:
            position, quaternion = _entity_pose(env, name)
        except PerturbationValidationError:
            continue
        if np.linalg.norm(position[:2] - receiver_before[:2]) > footprint_radius:
            continue
        if position[2] < receiver_before[2] - 0.02:
            continue
        position[2] += float(height_delta)
        _set_entity_pose(env, name, position, quaternion)
        moved.append(name)
    return moved


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


def _plan_vector(
    plan: ExecutionPlan,
    key: str,
    default: tuple[float, ...],
    *,
    length: int | None = None,
) -> np.ndarray:
    raw = plan.params.get(key, default)
    if key not in plan.params and length is not None:
        raw = default[: int(length)]
    values = np.asarray(raw, dtype=np.float64)
    expected = len(default) if length is None else int(length)
    if values.shape != (expected,) or not np.all(np.isfinite(values)):
        raise PerturbationConfigurationError(
            f"{plan.case_id} {key} must contain {expected} finite values"
        )
    return values


def _plan_xy_pair(
    plan: ExecutionPlan, key: str, default: tuple[float, float]
) -> tuple[float, float]:
    values = _plan_vector(plan, key, default, length=2)
    return float(values[0]), float(values[1])


def _plan_positive_float(plan: ExecutionPlan, key: str, default: float) -> float:
    try:
        value = float(plan.params.get(key, default))
    except (TypeError, ValueError) as exc:
        raise PerturbationConfigurationError(
            f"{plan.case_id} {key} must be numeric"
        ) from exc
    if not np.isfinite(value) or value <= 0.0:
        raise PerturbationConfigurationError(
            f"{plan.case_id} {key} must be positive and finite"
        )
    return value


def _plan_nonnegative_int(plan: ExecutionPlan, key: str, default: int) -> int:
    try:
        value = int(plan.params.get(key, default))
    except (TypeError, ValueError) as exc:
        raise PerturbationConfigurationError(
            f"{plan.case_id} {key} must be an integer"
        ) from exc
    if value < 0:
        raise PerturbationConfigurationError(
            f"{plan.case_id} {key} must be non-negative"
        )
    return value


def _s05_lateral_offset(plan: ExecutionPlan) -> float:
    """Return a safe S05 barrier offset from the transport centre line."""

    configured = plan.params.get("lateral_offset_m", S05_DEFAULT_LATERAL_OFFSET_M)
    try:
        offset = float(configured)
    except (TypeError, ValueError) as exc:
        raise PerturbationConfigurationError(
            f"S05 lateral_offset_m must be numeric; got {configured!r}"
        ) from exc
    if not np.isfinite(offset) or offset < S05_MIN_LATERAL_OFFSET_M:
        raise PerturbationConfigurationError(
            "S05 lateral_offset_m must be finite and at least "
            f"{S05_MIN_LATERAL_OFFSET_M:.3f} m"
        )
    return offset


def _injected_name(plan: ExecutionPlan, index: int = 0) -> str:
    return f"perturbation_{plan.case_id.lower()}_{index}"


def _camera_occluder_pose(
    env: Any, target_name: str, camera_name: str = "agentview", fraction: float = 0.62
) -> tuple[np.ndarray, np.ndarray]:
    target, _ = _entity_pose(env, target_name)
    return _camera_occluder_pose_at_point(
        env, target, camera_name=camera_name, fraction=fraction
    )


def _camera_occluder_pose_at_point(
    env: Any,
    target: np.ndarray,
    camera_name: str = "agentview",
    fraction: float = 0.62,
) -> tuple[np.ndarray, np.ndarray]:
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


def _safe_camera_occluder_pose(
    env: Any,
    moving_name: str,
    target_name: str,
    target_point: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Keep a persistent occluder in front of the target without overlap."""

    original_position, original_quaternion = _entity_pose(env, moving_name)
    for fraction in (0.48, 0.56, 0.64, 0.72):
        position, quaternion = (
            _camera_occluder_pose(env, target_name, fraction=fraction)
            if target_point is None
            else _camera_occluder_pose_at_point(env, target_point, fraction=fraction)
        )
        if _candidate_is_geometrically_clear(
            env,
            moving_name,
            position,
            ignored=("main_table", "floor"),
        ) and _candidate_is_clear_of_eef(env, moving_name, position):
            try:
                _set_entity_pose(env, moving_name, position, quaternion)
                _zero_free_joint_velocity(env, moving_name)
                if not _entity_has_penetrating_contact(
                    env, moving_name, ignored=("main_table", "floor")
                ):
                    return position, quaternion
            except Exception:
                pass
            _set_entity_pose(env, moving_name, original_position, original_quaternion)
            _zero_free_joint_velocity(env, moving_name)
    _set_entity_pose(env, moving_name, original_position, original_quaternion)
    _zero_free_joint_velocity(env, moving_name)
    raise PerturbationValidationError(
        f"No collision-clear camera occluder position for {moving_name!r} "
        f"in front of {target_name!r}"
    )


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


def _goal_paths(env: Any) -> tuple[GoalPath, ...]:
    sites = getattr(env, "object_sites_dict", {})
    goal_states = getattr(env, "parsed_problem", {}).get("goal_state", [])
    paths: list[GoalPath] = []
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
        paths.append(
            GoalPath(
                target_name=str(state[1]),
                target_position=target,
                receiver_name=str(receiver_name),
                anchor_name=anchor_name,
                receiver_position=receiver,
            )
        )
    return tuple(paths)


def _goal_path_anchors(env: Any) -> tuple[str, np.ndarray, str, np.ndarray]:
    paths = _goal_paths(env)
    if paths:
        path = paths[0]
        return (
            path.target_name,
            path.target_position,
            path.anchor_name,
            path.receiver_position,
        )
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
        self.observation_queue: deque[dict[str, Any]] = deque(maxlen=32)
        self.action_queue: deque[np.ndarray] = deque(maxlen=32)
        self.gripper_queue: deque[float] = deque(maxlen=32)
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
        self._active_goal_path: GoalPath | None = None
        self._active_dynamic_target: str | None = None
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
        self._active_goal_path = None
        self._active_dynamic_target = None

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

    def _ranked_goal_paths(
        self, env: Any, eef: np.ndarray | None
    ) -> tuple[GoalPath, ...]:
        paths = list(_goal_paths(env))
        if not paths:
            try:
                target, position, anchor, receiver = _goal_path_anchors(env)
            except PerturbationValidationError:
                return ()
            receiver_name = anchor
            site = getattr(env, "object_sites_dict", {}).get(anchor)
            if site is not None:
                receiver_name = str(getattr(site, "parent_name", receiver_name))
            paths = [
                GoalPath(target, position, receiver_name, anchor, receiver)
            ]

        def activity(path: GoalPath) -> tuple[float, ...]:
            saved = self._saved_poses.get(path.target_name)
            initial = path.target_position if saved is None else saved[0]
            moved = bool(
                path.target_position[2] >= initial[2] + 0.025
                or np.linalg.norm(path.target_position[:2] - initial[:2]) >= 0.05
            )
            held_distance = (
                float(np.linalg.norm(eef - path.target_position))
                if eef is not None
                else math.inf
            )
            held_near_eef = held_distance <= 0.18
            receiver_distance = (
                float(np.linalg.norm(eef - path.receiver_position))
                if eef is not None
                else math.inf
            )
            path_progress = 0.0
            path_distance = math.inf
            if eef is not None:
                direction = path.receiver_position[:2] - initial[:2]
                length_sq = float(np.dot(direction, direction))
                if length_sq > 1e-9:
                    path_progress = float(
                        np.dot(eef[:2] - initial[:2], direction) / length_sq
                    )
                    closest = initial[:2] + np.clip(path_progress, 0.0, 1.0) * direction
                    path_distance = float(np.linalg.norm(eef[:2] - closest))
            on_transport_path = 0.25 <= path_progress <= 0.90 and path_distance <= 0.18
            return (
                float(moved and held_near_eef),
                float(moved),
                float(on_transport_path),
                float(receiver_distance <= 0.18),
                -held_distance,
                -receiver_distance,
            )

        paths.sort(key=activity, reverse=True)
        return tuple(paths)

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
            shift_fraction = _plan_positive_float(self.plan, "image_shift_fraction", 0.05)
            for key in image_keys:
                value = out[key]
                if value.ndim >= 2:
                    shift = max(1, int(round(value.shape[-2] * shift_fraction)))
                    out[key] = np.roll(value, shift=(shift, -shift), axis=(-3, -2))
            self._log_once("intrinsics_distortion", step)
        elif case_id == "S18":
            calibration = _plan_vector(
                self.plan,
                "calibration_offset_m",
                (0.006, -0.004, 0.003),
                length=3,
            )
            for key, value in list(out.items()):
                if isinstance(value, np.ndarray) and "eef_pos" in key:
                    offset = np.zeros_like(value, dtype=np.float64)
                    offset.flat[: min(3, offset.size)] = calibration[: min(3, offset.size)]
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
            lighting_factor = _plan_positive_float(
                self.plan, "lighting_factor", 0.48
            )
            for key in image_keys:
                value = out[key]
                if np.issubdtype(value.dtype, np.integer):
                    out[key] = np.clip(value.astype(np.float32) * lighting_factor, 0, 255).astype(
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
            delay = (
                _plan_nonnegative_int(self.plan, "observation_delay_steps", 1)
                if case_id == "S20"
                else (
                    _plan_nonnegative_int(self.plan, "observation_delay_steps", 2)
                    if self._event_active(step)
                    else 0
                )
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
            self.action_queue.append(current.copy())
            delay = _plan_nonnegative_int(self.plan, "action_delay_steps", 1)
            if delay and len(self.action_queue) > delay:
                current = list(self.action_queue)[-delay - 1].copy()
                self._log_once("fixed_action_delay", step, delay_steps=delay)
        elif case_id == "D13" and self._event_active(step) and previous is not None:
            current[:-1] = previous[:-1]
            self._log_once("arm_gripper_desynchronization", step)
        elif case_id == "D14" and self._event_active(step) and previous is not None:
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
                current[0] = _plan_positive_float(
                    self.plan, "takeover_action_value", 0.12
                )
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

        if case_id == "S20":
            self.gripper_queue.append(current)
            delay = _plan_nonnegative_int(self.plan, "gripper_delay_steps", 1)
            if delay and len(self.gripper_queue) > delay:
                current = list(self.gripper_queue)[-delay - 1]
                self._log_once("fixed_gripper_delay", step, delay_steps=delay)
        elif case_id == "D14" and self._event_active(step) and previous is not None:
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
        elif case_id == "D19" and self._event_started(step):
            # Release before the intentional misplacement so the teleported
            # object cannot remain coupled to the gripper and fly away.
            current = 0.0
            self._log_once("release_before_misplace", step)
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

    def success_allowed(self, env: Any) -> bool:
        """Keep S07/S09 from reporting success when the real geometry cannot fit."""

        if self.plan.case_id not in {"S07", "S09"}:
            return True
        sites = getattr(env, "object_sites_dict", {})
        goal_states = getattr(env, "parsed_problem", {}).get("goal_state", [])
        for state in goal_states:
            if len(state) < 3 or str(state[0]).lower() not in {"in", "on"}:
                continue
            target_name, receiver_name = str(state[1]), str(state[2])
            target_radius = _entity_xy_radius(env, target_name)
            site = sites.get(receiver_name)
            if site is not None:
                try:
                    site_position = np.asarray(
                        env.sim.data.get_site_xpos(receiver_name), dtype=np.float64
                    )
                    site_matrix = np.asarray(
                        env.sim.data.get_site_xmat(receiver_name), dtype=np.float64
                    ).reshape(3, 3)
                    site_size = np.asarray(site.size, dtype=np.float64)
                except Exception:
                    continue
                target_position, _ = _entity_pose(env, target_name)
                local = site_matrix.T @ (target_position - site_position)
                if np.any(np.abs(local[:2]) + target_radius >= site_size[:2]):
                    return False
                if abs(float(local[2])) + target_radius >= site_size[2] + 0.01:
                    return False
                continue
            if _entity_exists(env, receiver_name):
                receiver_radius = _entity_xy_radius(env, receiver_name)
                target_position, _ = _entity_pose(env, target_name)
                receiver_position, _ = _entity_pose(env, receiver_name)
                if receiver_radius > 0.0 and target_radius > 0.0:
                    if receiver_radius <= target_radius + 0.005:
                        return False
                    if (
                        np.linalg.norm(target_position[:2] - receiver_position[:2])
                        > max(0.03, receiver_radius - target_radius - 0.005)
                    ):
                        return False
        return True

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
        expected_texture = S22_COMPILED_TEXTURES.get(material_name)
        configured_texture = str(
            self.plan.params.get("texture_asset", expected_texture or "")
        )
        if expected_texture is None:
            raise PerturbationConfigurationError(
                f"S22 material_id {material_name!r} has no registered compiled texture"
            )
        if configured_texture != expected_texture:
            raise PerturbationConfigurationError(
                f"S22 texture_asset {configured_texture!r} does not match compiled "
                f"material {material_name!r} ({expected_texture!r})"
            )
        texture_scale = _plan_vector(
            self.plan, "texture_scale", (2.0, 2.0), length=2
        )
        if np.any(texture_scale <= 0.0):
            raise PerturbationConfigurationError(
                "S22 texture_scale must contain two positive finite values"
            )
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
        if not hasattr(env.sim.model, "mat_texrepeat"):
            raise PerturbationValidationError(
                "S22 cannot apply texture_scale because MuJoCo exposes no mat_texrepeat"
            )
        env.sim.model.mat_texrepeat[material_id] = texture_scale
        env.sim.model.geom_matid[list(geom_ids)] = material_id
        env.sim.forward()
        self._log_once(
            "workspace_texture_replaced",
            0,
            material=material_name,
            texture_asset=configured_texture,
            texture_scale=texture_scale.tolist(),
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
            _, after, delta = _safe_offset_pose(
                env,
                target,
                (0.075, 0.045),
                minimum_gap=0.12 if case_id == "S01" else 0.08,
                ignored=self.plan.targets,
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
            if self._interaction_mode() == "articulation":
                articulation_targets = _goal_articulation_targets(env)
                if articulation_targets:
                    target = articulation_targets[0][0]
                elif len(self.plan.targets) == 1:
                    target = self.plan.targets[0]
                else:
                    raise PerturbationConfigurationError(
                        "Articulation S04 requires a resolvable goal fixture target"
                    )
                before, after, delta = _safe_offset_pose(
                    env, target, (0.045, 0.025), minimum_gap=0.04, ignored=(target,)
                )
                self._log_once(
                    "articulation_fixture_pose_offset",
                    0,
                    target=target,
                    xy_before=before[:2].tolist(),
                    xy_after=after[:2].tolist(),
                    delta_xy=delta.tolist(),
                )
            else:
                if len(self.plan.targets) != 2:
                    raise PerturbationConfigurationError(
                        "S04 planar position swap requires exactly two movable targets"
                    )
                first, second = self.plan.targets
                first_position, first_quaternion = _entity_pose(env, first)
                second_position, second_quaternion = _entity_pose(env, second)
                stacked = bool(
                    np.linalg.norm(first_position[:2] - second_position[:2]) < 0.02
                )
                same_category = bool(
                    _entity_semantic_category(env, first)
                    == _entity_semantic_category(env, second)
                )
                if stacked:
                    first_before, first_after, delta, support_geom = (
                        _safe_grounded_layout_offset(
                            env,
                            first,
                            _plan_xy_pair(self.plan, "layout_offset_xy", (0.12, 0.08)),
                        )
                    )
                    self._log_once(
                        "stacked_target_grounded_offset",
                        0,
                        first=first,
                        second=second,
                        first_xy_before=first_before[:2].tolist(),
                        first_xy_after=first_after[:2].tolist(),
                        delta_xy=delta.tolist(),
                        support_geom=support_geom,
                    )
                elif same_category:
                    # Swapping two instances of the same visual category is
                    # indistinguishable from BASE (e.g. the two moka pots).
                    # Keep the perturbation observable with a small, safe
                    # layout offset instead of changing the task goal.
                    before, after, delta, support_geom = (
                        _safe_grounded_layout_offset(
                            env,
                            first,
                            _plan_xy_pair(self.plan, "layout_offset_xy", (0.12, 0.08)),
                        )
                    )
                    self._log_once(
                        "same_class_layout_offset",
                        0,
                        target=first,
                        reference=second,
                        delta_xy=delta.tolist(),
                        support_geom=support_geom,
                    )
                    first_position = after
                else:
                    try:
                        (
                            first_position,
                            first_after,
                            second_position,
                            second_after,
                        ) = _safe_planar_object_swap(env, first, second)
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
                    except PerturbationValidationError as exc:
                        first_position, first_after, delta, support_geom = (
                            _safe_grounded_layout_offset(
                                env,
                                first,
                                _plan_xy_pair(self.plan, "layout_offset_xy", (0.12, 0.08)),
                            )
                        )
                        self._log_once(
                            "planar_swap_grounded_fallback",
                            0,
                            first=first,
                            second=second,
                            first_xy_before=first_position[:2].tolist(),
                            first_xy_after=first_after[:2].tolist(),
                            delta_xy=delta.tolist(),
                            support_geom=support_geom,
                            reason=str(exc),
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
                # A table is an arena body rather than a movable receiver. For
                # old BDDL files that still target ``main_table`` twice, use
                # the goal object as the local raised support instead.
                if reference_name in {"main_table", "floor"}:
                    goal_targets = _goal_interaction_targets(env)
                    if goal_targets:
                        reference_name = goal_targets[0]
                        reference, _ = _entity_pose(env, reference_name)
                        anchor_name = reference_name
                try:
                    height_delta = float(self.plan.params.get("height_delta_m", 0.05))
                except (TypeError, ValueError) as exc:
                    raise PerturbationConfigurationError(
                        "S03 height_delta_m must be numeric"
                    ) from exc
                if not np.isfinite(height_delta) or height_delta <= 0.0:
                    raise PerturbationConfigurationError(
                        "S03 height_delta_m must be positive and finite"
                    )
                moved_contents = []
                riser_name = name
                if reference_name in getattr(env, "objects_dict", {}) and _entity_is_movable(
                    env, reference_name
                ):
                    raised, riser_position, delta, support_name = _safe_support_riser_layout(
                        env, reference_name, riser_name, height_delta
                    )
                    position = riser_position
                    self._log_once(
                        "support_riser_coupled_layout",
                        0,
                        receiver=reference_name,
                        support_geom=support_name,
                        target_position=raised.tolist(),
                    )
                else:
                    # Fixed fixtures and arena bodies cannot be lifted safely:
                    # moving their root moves attached furniture through the
                    # scene.  Use a visible grounded support near the target
                    # instead, preserving every original fixture pose.
                    anchor, anchor_name = _functional_anchor(env, reference_name)
                    position, support_name = _safe_grounded_asset_near_point(
                        env,
                        riser_name,
                        anchor,
                        _plan_xy_pair(
                            self.plan, "fixture_riser_offset_xy", (0.18, -0.12)
                        ),
                    )
                    self._log_once(
                        "fixture_support_riser_placed",
                        0,
                        receiver=reference_name,
                        anchor=anchor_name,
                        support_geom=support_name,
                        height_delta_m=height_delta,
                    )
                self._log_once(
                    "receiver_height_changed",
                    0,
                    receiver=reference_name,
                    height_delta_m=height_delta,
                    moved_contents=moved_contents,
                )
            elif case_id == "S05":
                if (
                    self._interaction_mode() == "articulation"
                    and "obstacle_part" in self.plan.params
                ):
                    articulation_targets = _goal_articulation_targets(env)
                    if not articulation_targets:
                        raise PerturbationValidationError(
                            "S05 articulation task has no goal fixture"
                        )
                    target_name, _ = articulation_targets[0]
                    part = str(self.plan.params["obstacle_part"])
                    anchor = _articulation_part_anchor(env, target_name, part)
                    position, support_name = _safe_grounded_asset_near_point(
                        env,
                        name,
                        anchor,
                        _plan_xy_pair(
                            self.plan,
                            "articulation_obstacle_offset_xy",
                            (0.0, -0.12),
                        ),
                    )
                    anchor_name = f"{target_name}:{part}"
                    self._log_once(
                        "static_articulation_detour_validated",
                        0,
                        target=target_name,
                        part=part,
                        support_geom=support_name,
                    )
                else:
                    receiver_name = self.plan.targets[-1]
                    receiver, anchor_name = _functional_anchor(env, receiver_name)
                    target_name = self.plan.targets[0]
                    target, _ = _entity_pose(env, target_name)
                    position, quaternion, lateral = _safe_transport_barrier_pose(
                        env,
                        name,
                        target,
                        receiver,
                        requested_lateral_offset=_s05_lateral_offset(self.plan),
                        carried_object_name=target_name,
                        receiver_name=receiver_name,
                    )
                    self._log_once(
                        "static_transport_detour_validated",
                        0,
                        target=target_name,
                        receiver=anchor_name,
                        lateral_offset_m=lateral,
                    )
            elif case_id == "S10":
                position = _visible_clutter_pose(
                    env,
                    name,
                    reference_name,
                    minimum_gap=_plan_positive_float(
                        self.plan, "clutter_minimum_gap_m", 0.10
                    ),
                    requested_radius=_plan_positive_float(
                        self.plan, "clutter_radius_m", 0.14
                    ),
                )
            elif case_id == "S11":
                # Keep the same-class distractor visually close while finding a
                # collision-clear, grounded position instead of a fixed floating
                # offset.
                # Anchor to the existing same-class reference. The task target
                # can be inside a drawer, on a cabinet, or stacked on another
                # object; using it as the placement anchor can put the new bowl
                # inside furniture or leave it suspended above the table.
                target_name = reference_name
                _, position, applied = _safe_asset_near_reference_pose(
                    env,
                    name,
                    target_name,
                    _plan_xy_pair(
                        self.plan, "distractor_offset_xy", (-0.075, 0.055)
                    ),
                    minimum_gap=_plan_positive_float(
                        self.plan, "distractor_minimum_gap_m", 0.06
                    ),
                )
                anchor_name = target_name
            else:
                part = self.plan.params.get("occlusion_part")
                target_point = (
                    _articulation_part_anchor(env, reference_name, str(part))
                    if part
                    else None
                )
                position, quaternion = _safe_camera_occluder_pose(
                    env, name, reference_name, target_point=target_point
                )
            if case_id not in {"S03", "S05", "S10", "S11", "S12"} and not _candidate_is_clear(
                env,
                name,
                position[:2],
                0.055,
                ignored=(reference_name, *self.plan.targets),
            ):
                position[1] += 0.11
            if case_id != "S11":
                _set_entity_pose(env, name, position, quaternion)
            self._log_once(
                "static_asset_placed",
                0,
                asset=name,
                asset_id=self.plan.assets[0].asset_id,
                reference=reference_name,
                anchor=anchor_name,
                position=position.tolist(),
                offset_xy=(applied[:2].tolist() if case_id == "S11" else None),
            )
        elif case_id == "S13":
            changed = self._change_appearance(env, self.plan.targets)
            self._log_once("appearance_changed", 0, targets=changed)
        elif case_id == "S14":
            changed_geoms = self._change_scene_domain(env)
            self._set_lighting(env, 0.64)
            self._log_once("scene_domain_changed", 0, changed_geoms=changed_geoms)
        elif case_id == "S15":
            self._offset_camera(
                env,
                _plan_vector(
                    self.plan,
                    "camera_offset_m",
                    (0.045, -0.035, 0.025),
                    length=3,
                ),
            )
            self._log_once("camera_extrinsics_changed", 0)
        elif case_id == "S16":
            changed = []
            for camera in self.plan.targets:
                try:
                    camera_id = int(env.sim.model.camera_name2id(camera))
                except Exception:
                    continue
                before = float(env.sim.model.cam_fovy[camera_id])
                fov_scale = _plan_positive_float(self.plan, "fov_scale", 1.12)
                env.sim.model.cam_fovy[camera_id] = float(
                    np.clip(before * fov_scale, 20.0, 100.0)
                )
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
            offset = _plan_vector(
                self.plan,
                "joint_offset",
                (0.035, -0.025, 0.02, 0.0, 0.0, 0.0, 0.0),
                length=len(current),
            )
            updated = current + offset
            model = getattr(env.sim, "model", None)
            if model is not None and hasattr(model, "jnt_range"):
                for local_index, joint_index in enumerate(indices):
                    try:
                        low, high = np.asarray(
                            model.jnt_range[joint_index], dtype=np.float64
                        )
                        if np.isfinite(low) and np.isfinite(high) and low < high:
                            updated[local_index] = np.clip(
                                updated[local_index], low + 0.01, high - 0.01
                            )
                    except Exception:
                        continue
            env.sim.data.qpos[indices] = updated
            env.sim.forward()
            self._log_once(
                "robot_initial_state_changed",
                0,
                joint_offset=(updated - current).tolist(),
            )
        elif case_id == "S21":
            self.language_instruction("", 0)
        elif case_id == "S22":
            self._apply_workspace_texture(env)
        elif case_id == "S06":
            if len(self.plan.targets) != 1:
                raise PerturbationConfigurationError("S06 requires exactly one target")
            # Remote evaluators load a precomputed LIBERO init state after the
            # replacement object is compiled. That qpos carries the source
            # asset's quaternion, which can leave a replacement bottle or mug
            # on its side. Keep the sampled position but restore the replacement
            # asset's upright frame after the init state is applied.
            target = self.plan.targets[0]
            if target in getattr(env, "fixtures_dict", {}):
                self._log_once(
                    "fixture_geometry_variant",
                    0,
                    target=target,
                    geometry_factors=list(
                        _plan_vector(self.plan, "geometry_factors", (1.08, 1.08, 1.0), length=3)
                    ),
                )
                return
            if not _entity_is_movable(env, target):
                raise PerturbationConfigurationError(
                    f"S06 target {target!r} is neither a movable object nor a fixture"
                )
            position, _ = _entity_pose(env, target)
            rotation_axis = str(self.plan.params.get("replacement_rotation_axis", "z")).lower()
            rotation_angle = float(self.plan.params.get("replacement_rotation_rad", 0.0))
            replacement_quaternion = _axis_angle_quaternion(
                rotation_axis, rotation_angle
            )
            _ground_entity_on_support(
                env, target, position, replacement_quaternion
            )
            replacement = getattr(env, "objects_dict", {}).get(target)
            self._log_once(
                "target_instance_replaced",
                0,
                target=target,
                asset_id=self.plan.assets[0].asset_id,
                requested_scale=self.plan.assets[0].scale,
                scale=getattr(
                    replacement,
                    "_libero_pro_replacement_scale",
                    self.plan.assets[0].scale,
                ),
            )
        elif case_id in {"S07", "S08", "S09"}:
            if case_id == "S08" and self.plan.targets and not any(
                target in getattr(env, "fixtures_dict", {}) for target in self.plan.targets
            ):
                target = self.plan.targets[0]
                before, quaternion = _entity_pose(env, target)
                grounded, support_name = _ground_entity_on_support(
                    env, target, before, quaternion
                )
                adjusted = False
                if _entity_has_penetrating_contact(env, target):
                    _, after, delta, support_name = _safe_grounded_layout_offset(
                        env, target, (0.10, 0.0)
                    )
                    adjusted = True
                    self._log_once(
                        "geometry_clearance_adjusted",
                        0,
                        target=target,
                        delta_xy=delta.tolist(),
                        clearance_xy_m=float(
                            np.linalg.norm(after[:2] - before[:2])
                        ),
                        support_geom=support_name,
                    )
                else:
                    self._log_once(
                        "geometry_clearance_checked",
                        0,
                        target=target,
                        adjusted=adjusted,
                        support_geom=support_name,
                        vertical_grounding_m=float(grounded[2] - before[2]),
                    )
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

    @staticmethod
    def _zero_entity_velocity(env: Any, name: str) -> None:
        """Prevent a pose teleport from carrying stale free-joint velocity."""
        _zero_free_joint_velocity(env, name)

    def _restore_dynamic_asset(self, env: Any, step: int) -> None:
        name = _injected_name(self.plan)
        _, quaternion = self._saved_poses.get(
            name, (np.array([0.0, 0.0, -5.0]), _yaw_quaternion(0.0))
        )
        if _entity_exists(env, name):
            # Dynamic assets are staged off-screen before the event. Releasing
            # the perturbation means removing the blocker/occluder, not
            # returning it to its original visible placement.
            _set_entity_pose(env, name, np.array([0.0, 0.0, -5.0]), quaternion)
        self._dynamic_restored = True
        self._log_once("dynamic_asset_restored", step, asset=name)

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
                case_id in {"D03", "D04"}
                and not self._dynamic_restored
                and self._dynamic_event_step is not None
                and step >= self._dynamic_event_step + self._event_duration_steps()
            ):
                self._restore_dynamic_asset(env, step)
            return
        if not self._dynamic_triggered(env, step):
            return

        if case_id == "D06":
            paths = _goal_paths(env)
            excluded = tuple(
                dict.fromkeys(
                    [
                        name
                        for path in paths
                        for name in (path.target_name, path.receiver_name)
                    ]
                    + list(_goal_interaction_targets(env))
                )
            )
            moved, expected_count = _rearrange_unrelated_objects(
                env,
                excluded=excluded,
                requested_offsets=(
                    _plan_xy_pair(self.plan, "offset_xy", (0.12, -0.09)),
                    _plan_xy_pair(
                        self.plan, "secondary_offset_xy", (-0.11, 0.10)
                    ),
                    _plan_xy_pair(
                        self.plan, "tertiary_offset_xy", (0.08, 0.13)
                    ),
                ),
            )
            if len(moved) < expected_count:
                raise PerturbationValidationError(
                    f"D06 could only safely rearrange {len(moved)} unrelated objects; "
                    f"expected {expected_count} from this scene"
                )
            self._log_once(
                "distractors_rearranged",
                step,
                moved=moved,
                expected_count=expected_count,
                requested_count=3,
            )
            self._dynamic_event_step = int(step)
            self._dynamic_applied = True
            return
        if case_id in {"D01", "D02", "D18", "D19"}:
            if case_id == "D01" and self._interaction_mode() == "articulation":
                articulation_targets = _goal_articulation_targets(env)
                if not articulation_targets:
                    raise PerturbationValidationError(
                        "D01 articulation task has no goal fixture"
                    )
                target, _ = articulation_targets[0]
                joint, before, after = _offset_goal_articulation_joint(
                    env,
                    target,
                    float(self.plan.params.get("joint_offset", -0.035)),
                )
                self._log_once(
                    "articulation_joint_pose_update",
                    step,
                    target=target,
                    joint=joint,
                    before=before,
                    after=after,
                )
                self._dynamic_event_step = int(step)
                self._dynamic_applied = True
                return
            if self._interaction_mode() == "articulation" and case_id in {"D18", "D19"}:
                articulation_targets = _goal_articulation_targets(env)
                if not articulation_targets:
                    raise PerturbationValidationError(
                        f"{case_id} articulation fallback has no goal fixture"
                    )
                target, _ = articulation_targets[0]
                # Articulation goals are fixed fixtures. Translating their root
                # body can put the cabinet/stove through the rack or EEF. The
                # perturbation is therefore expressed as a bounded change to
                # the actual goal joint, preserving the fixture base pose.
                joint, before, after = _offset_goal_articulation_joint(
                    env,
                    target,
                    float(
                        self.plan.params.get(
                            "joint_offset",
                            -0.035 if case_id == "D18" else 0.035,
                        )
                    ),
                )
                self._log_once(
                    "articulation_joint_state_change",
                    step,
                    target=target,
                    joint=joint,
                    before=before,
                    after=after,
                )
                self._dynamic_event_step = int(step)
                self._dynamic_applied = True
                return
            targets = [name for name in self.plan.targets if _entity_exists(env, name)]
            if not targets:
                raise PerturbationValidationError(
                    f"Dynamic case {case_id} has no movable target in {self.plan.targets}"
                )
            target = self._active_dynamic_target or targets[0]
            delta = _dynamic_pose_requested_delta(case_id, target, self.plan.params)
            if case_id == "D19":
                self._zero_entity_velocity(env, target)
                before, current_quaternion = _entity_pose(env, target)
                initial = self._saved_poses.get(target, (before, current_quaternion))[0]
                return_direction = initial[:2] - before[:2]
                return_length = float(np.linalg.norm(return_direction))
                if return_length < 1e-6:
                    return_direction = np.array([-1.0, 0.0])
                else:
                    return_direction /= return_length
                # Keep the misplacement on the current support plane. The
                # previous 35 mm lift created an unsupported drop that could
                # launch or visually "fly" the object before it settled.
                misplacement_distance = _plan_positive_float(
                    self.plan, "misplacement_distance_m", 0.065
                )
                _, after, applied, support_name = _safe_grounded_layout_offset(
                    env,
                    target,
                    tuple((return_direction * misplacement_distance).tolist()),
                )
                self._log_once(
                    "misplacement_grounded",
                    step,
                    target=target,
                    support_geom=support_name,
                )
            elif case_id == "D18":
                _, after, applied, support_name = _safe_grounded_layout_offset(
                    env, target, delta
                )
                model = getattr(getattr(env, "sim", None), "model", None)
                data = getattr(getattr(env, "sim", None), "data", None)
                if not hasattr(model, "_model") or not hasattr(data, "_data"):
                    initial_position, initial_quaternion = self._saved_poses.get(
                        target, (after, _entity_pose(env, target)[1])
                    )
                    after[2] = initial_position[2]
                    _set_entity_pose(env, target, after, initial_quaternion)
                self._log_once(
                    "recoverable_drop_grounded",
                    step,
                    target=target,
                    support_geom=support_name,
                )
            else:
                _, after, applied = _safe_offset_pose(
                    env,
                    target,
                    delta,
                    keep_support=case_id == "D01",
                )
            yaw = {"D01": 0.28, "D02": -0.24}.get(case_id)
            if yaw is not None:
                _, current_quaternion = _entity_pose(env, target)
                _set_entity_pose(
                    env,
                    target,
                    after,
                    _quaternion_multiply(_yaw_quaternion(yaw), current_quaternion),
                )
            self._zero_entity_velocity(env, target)
            self._log_once(
                "dynamic_state_change",
                step,
                target=target,
                delta_xy=applied.tolist(),
                yaw=yaw,
            )
        elif case_id in {"D03", "D04", "D05"}:
            name = _injected_name(self.plan)
            reference_name = (
                self._active_goal_path.receiver_name
                if case_id == "D03" and self._active_goal_path is not None
                else next(
                    (target for target in self.plan.targets if _entity_exists(env, target)),
                    self.plan.references[0] if self.plan.references else None,
                )
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
                part = self.plan.params.get("occlusion_part")
                target_point = (
                    _articulation_part_anchor(env, reference_name, str(part))
                    if part
                    else None
                )
                position, quaternion = _safe_camera_occluder_pose(
                    env, name, reference_name, target_point=target_point
                )
            elif case_id == "D05":
                if self._interaction_mode() == "articulation":
                    articulation_targets = _goal_articulation_targets(env)
                    if not articulation_targets:
                        raise PerturbationValidationError(
                            "D05 articulation fallback has no goal fixture"
                        )
                    target_name, _ = articulation_targets[0]
                    part = str(self.plan.params.get("obstacle_part", "handle"))
                    target = _articulation_part_anchor(env, target_name, part)
                    anchor_name = target_name
                    position, support_name = _safe_grounded_asset_near_point(
                        env,
                        name,
                        target,
                        _plan_xy_pair(
                            self.plan, "articulation_obstacle_offset_xy", (0.0, -0.10)
                        ),
                    )
                    quaternion = _yaw_quaternion(0.0)
                    self._log_once(
                        "articulation_detour_validated",
                        step,
                        target=target_name,
                        part=part,
                        support_geom=support_name,
                    )
                else:
                    if self._active_goal_path is not None:
                        target_name = self._active_goal_path.target_name
                        target = self._active_goal_path.target_position
                        anchor_name = self._active_goal_path.anchor_name
                        receiver = self._active_goal_path.receiver_position
                    else:
                        target_name, target, anchor_name, receiver = _goal_path_anchors(env)
                    position, quaternion, lateral = _safe_transport_barrier_pose(
                        env,
                        name,
                        target,
                        receiver,
                        requested_lateral_offset=float(
                            self.plan.params.get("lateral_offset_m", 0.025)
                        ),
                        carried_object_name=target_name,
                        receiver_name=(
                            self._active_goal_path.receiver_name
                            if self._active_goal_path is not None
                            else None
                        ),
                    )
                    self._log_once(
                        "transport_detour_validated",
                        step,
                        target=target_name,
                        receiver=anchor_name,
                        lateral_offset_m=lateral,
                    )
            else:
                if self._interaction_mode() == "articulation":
                    part = str(self.plan.params.get("obstacle_part", "handle"))
                    anchor = _articulation_part_anchor(env, reference_name, part)
                    position, support_name = _safe_grounded_asset_near_point(
                        env,
                        name,
                        anchor,
                        _plan_xy_pair(
                            self.plan, "articulation_obstacle_offset_xy", (0.0, -0.08)
                        ),
                    )
                    anchor_name = f"{reference_name}:{part}"
                    self._log_once(
                        "receiver_blocker_grounded",
                        step,
                        support_geom=support_name,
                    )
                else:
                    position, anchor_name = _functional_anchor(env, reference_name)
                    position = position + offset
                    position, support_name = _ground_entity_on_support(
                        env, name, position, _yaw_quaternion(0.0)
                    )
                    self._log_once(
                        "receiver_blocker_grounded",
                        step,
                        support_geom=support_name,
                    )
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
            self._offset_camera(
                env,
                _plan_vector(
                    self.plan,
                    "camera_offset_m",
                    (0.025, -0.018, 0.012),
                    length=3,
                ),
            )
            self._log_once("dynamic_camera_offset", step)
        elif case_id == "D09":
            self._set_lighting(
                env, _plan_positive_float(self.plan, "lighting_factor", 0.48)
            )
            self._log_once("dynamic_lighting_change", step)
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
        # Observation faults follow the model's interaction distance, so a
        # short or long policy trajectory cannot miss the event entirely.
        # Reset-time proximity is still harmless because the trigger is only
        # evaluated after the environment has entered its rollout loop.
        if (
            case_id in {"D08", "D09"}
            and eef is not None
            and self._interaction_mode() != "articulation"
        ):
            threshold = float(
                self.plan.params.get("observation_trigger_distance_m", 0.22)
            )
            for path in self._ranked_goal_paths(env, eef):
                if min(
                    np.linalg.norm(eef - path.target_position),
                    np.linalg.norm(eef - path.receiver_position),
                ) <= threshold:
                    self._active_goal_path = path
                    self._active_dynamic_target = path.target_name
                    return True
            return False

        # D13 is an arm/gripper desynchronisation.  Trigger it at a genuine
        # grasp approach, and only while the command is closing the gripper;
        # this keeps the injected arm lag tied to the task state rather than a
        # rollout step number.
        if case_id == "D13" and eef is not None:
            closing = bool(
                self.previous_action is not None
                and self.previous_action.size
                and self.previous_action[-1] > 0.0
            )
            if not closing:
                return False
            threshold = float(
                self.plan.params.get("desync_trigger_distance_m", 0.20)
            )
            for path in self._ranked_goal_paths(env, eef):
                if np.linalg.norm(eef - path.target_position) <= threshold:
                    self._active_goal_path = path
                    self._active_dynamic_target = path.target_name
                    return True
            return False

        if case_id == "D01" and target and eef is not None:
            position = (
                self._articulation_anchor(env, target)
                if self._interaction_mode() == "articulation"
                else _entity_pose(env, target)[0]
            )
            return bool(
                np.linalg.norm(eef - position)
                <= float(self.plan.params.get("approach_trigger_distance_m", 0.12))
            )
        if case_id == "D17" and target and eef is not None:
            position, _ = _entity_pose(env, target)
            if self._interaction_mode() == "articulation":
                return bool(
                    np.linalg.norm(eef - self._articulation_anchor(env, target))
                    <= float(self.plan.params.get("grasp_trigger_distance_m", 0.14))
                )
            closing = bool(
                self.previous_action is not None
                and self.previous_action.size
                and self.previous_action[-1] > 0.0
            )
            return bool(
                closing
                and np.linalg.norm(eef - position)
                <= float(self.plan.params.get("grasp_trigger_distance_m", 0.12))
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
                threshold = 0.18 if case_id == "D05" else 0.16
                if case_id == "D19":
                    return bool(
                        self._articulation_progress(env, target_name)
                        >= float(self.plan.params.get("trigger_state_change_m", 0.02))
                        and np.linalg.norm(eef - anchor) <= threshold
                    )
                return bool(np.linalg.norm(eef - anchor) <= threshold)
        if case_id == "D05":
            has_action = self.previous_action is not None
            for path in self._ranked_goal_paths(env, eef):
                saved = self._saved_poses.get(path.target_name)
                if saved is None:
                    continue
                initial = saved[0]
                position = path.target_position
                transported = bool(
                    position[2] >= initial[2] + 0.025
                    or np.linalg.norm(position[:2] - initial[:2]) >= 0.05
                )
                closing = bool(
                    self.previous_action is not None
                    and self.previous_action.size
                    and self.previous_action[-1] > 0.0
                )
                held_near_eef = bool(
                    eef is not None and np.linalg.norm(eef - position) <= 0.18
                )
                path_progress = False
                if eef is not None:
                    direction = path.receiver_position[:2] - initial[:2]
                    length_sq = float(np.dot(direction, direction))
                    if length_sq > 1e-9:
                        fraction = float(
                            np.dot(eef[:2] - initial[:2], direction) / length_sq
                        )
                        closest = initial[:2] + np.clip(fraction, 0.0, 1.0) * direction
                        path_progress = bool(
                            float(self.plan.params.get("path_progress_min_fraction", 0.25))
                            <= fraction
                            <= float(self.plan.params.get("path_progress_max_fraction", 0.90))
                            and np.linalg.norm(eef[:2] - closest)
                            <= float(self.plan.params.get("path_progress_tolerance_m", 0.18))
                        )
                if (transported and closing and held_near_eef) or (
                    path_progress and has_action
                ):
                    self._active_goal_path = path
                    return True
            return False
        if case_id == "D19":
            require_release = bool(self.plan.params.get("require_release", False))
            released = bool(
                self.previous_action is not None
                and self.previous_action.size
                and self.previous_action[-1] <= 0.0
            )
            if require_release and not released:
                return False
            for path in self._ranked_goal_paths(env, eef):
                saved = self._saved_poses.get(path.target_name)
                if saved is None:
                    continue
                initial = saved[0]
                transported = bool(
                    path.target_position[2] >= initial[2] + 0.025
                    or np.linalg.norm(path.target_position[:2] - initial[:2]) >= 0.05
                )
                near_receiver = bool(
                    np.linalg.norm(path.target_position - path.receiver_position)
                    <= float(
                        self.plan.params.get("receiver_approach_distance_m", 0.20)
                    )
                )
                if transported and near_receiver:
                    self._active_goal_path = path
                    self._active_dynamic_target = path.target_name
                    return True
            return False
        if case_id == "D03":
            has_action = self.previous_action is not None
            for path in self._ranked_goal_paths(env, eef):
                saved = self._saved_poses.get(path.target_name)
                transported = bool(
                    saved is not None
                    and (
                        path.target_position[2] >= saved[0][2] + 0.025
                        or np.linalg.norm(path.target_position[:2] - saved[0][:2])
                        >= 0.05
                    )
                )
                receiver_approach = bool(
                    eef is not None
                    and np.linalg.norm(eef - path.receiver_position)
                    <= float(self.plan.params.get("receiver_trigger_distance_m", 0.18))
                )
                object_near_receiver = bool(
                    np.linalg.norm(path.target_position - path.receiver_position)
                    <= float(self.plan.params.get("receiver_approach_distance_m", 0.20))
                )
                if (receiver_approach and has_action) or (
                    transported and object_near_receiver
                ):
                    self._active_goal_path = path
                    return True
            return False
        if case_id == "D02":
            has_action = self.previous_action is not None
            for path in self._ranked_goal_paths(env, eef):
                saved = self._saved_poses.get(path.target_name)
                if saved is None:
                    continue
                initial = saved[0]
                transported = bool(
                    path.target_position[2] >= initial[2] + 0.025
                    or np.linalg.norm(path.target_position[:2] - initial[:2]) >= 0.05
                )
                receiver_approach = bool(
                    eef is not None
                    and np.linalg.norm(eef - path.receiver_position)
                    <= float(self.plan.params.get("receiver_trigger_distance_m", 0.18))
                )
                object_near_receiver = bool(
                    np.linalg.norm(path.target_position - path.receiver_position)
                    <= float(self.plan.params.get("receiver_approach_distance_m", 0.20))
                )
                # A model may reach the receiving region before MuJoCo reports
                # the carried object's pose update.
                if (transported and object_near_receiver) or (
                    receiver_approach and has_action
                ):
                    self._active_goal_path = path
                    self._active_dynamic_target = path.receiver_name
                    return True
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
            closing = bool(
                self.previous_action is not None
                and self.previous_action.size
                and self.previous_action[-1] > 0.0
            )
            ranked_targets = [path.target_name for path in self._ranked_goal_paths(env, eef)]
            ranked_targets.extend(
                name
                for name in (*_goal_interaction_targets(env), *self.plan.targets)
                if name not in ranked_targets and _entity_exists(env, name)
            )
            for candidate in ranked_targets:
                position, _ = _entity_pose(env, candidate)
                saved = self._saved_poses.get(candidate)
                if saved is None:
                    continue
                transported = bool(
                    position[2] >= saved[0][2] + 0.04
                    or np.linalg.norm(position[:2] - saved[0][:2]) >= 0.06
                )
                held_near_eef = bool(
                    eef is not None and np.linalg.norm(eef - position) <= 0.18
                )
                if transported and closing and held_near_eef:
                    self._active_dynamic_target = candidate
                    return True
            return False
        if self.plan.trigger == "state_change":
            if eef is None:
                return False
            if self._interaction_mode() == "articulation":
                articulation_targets = _goal_articulation_targets(env)
                for name, _ in articulation_targets:
                    if (
                        self._articulation_progress(env, name)
                        >= float(self.plan.params.get("trigger_state_change_m", 0.02))
                        and np.linalg.norm(
                            eef - self._articulation_anchor(env, name)
                        )
                        <= float(self.plan.params.get("trigger_distance_m", 0.18))
                    ):
                        self._active_dynamic_target = name
                        return True
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
                if self._interaction_mode() == "articulation":
                    position = _functional_anchor(env, name)[0]
                else:
                    position, _ = _entity_pose(env, name)
                if np.linalg.norm(eef - position) <= threshold:
                    return True
            return False
        return False
