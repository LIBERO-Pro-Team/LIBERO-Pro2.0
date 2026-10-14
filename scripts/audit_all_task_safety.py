"""Audit every published LIBERO-Pro2.0 task without running a policy rollout."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ASSETS_ROOT = ROOT / "assets"
MANIFEST = ASSETS_ROOT / "task_manifest.json"
PARSER_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "perturbation_config.py"
)
RUNTIME_PATH = PARSER_PATH.with_name("nonphysical_perturbations.py")
ASSET_ROOT = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "assets"
    / "perturbation_assets"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "all_task_safety_audit_20260824"

SUITES = ("libero_goal", "libero_object", "libero_spatial", "libero_10")
CASE_IDS = (
    "BASE",
    *(f"S{index:02d}" for index in range(1, 23)),
    *(f"D{index:02d}" for index in range(1, 22)),
)
PUBLISHED_MANIFEST_VERSION = "libero-pro2.0-1706-v1"
PUBLISHED_TASK_COUNT = 1701
PUBLISHED_EXCLUDED = {("libero_10", 8, "S04")}
GOAL_NOT_APPLICABLE = {
    ("libero_goal", 0, "D02"),
    ("libero_goal", 0, "D18"),
    ("libero_goal", 0, "S02"),
    ("libero_goal", 5, "D02"),
    ("libero_goal", 5, "D13"),
    ("libero_goal", 5, "D17"),
    ("libero_goal", 5, "D18"),
    ("libero_goal", 5, "S02"),
    ("libero_goal", 5, "S03"),
    ("libero_goal", 5, "S09"),
    ("libero_goal", 7, "D02"),
    ("libero_goal", 7, "D18"),
    ("libero_goal", 7, "S02"),
    ("libero_goal", 0, "D05"),
    ("libero_goal", 0, "D17"),
    ("libero_goal", 7, "D03"),
    ("libero_goal", 7, "D05"),
    ("libero_goal", 7, "S05"),
}
LEGACY_CASE_IDS = (
    *(f"S{index:02d}" for index in range(1, 22)),
    *(f"D{index:02d}" for index in range(1, 20)),
    "D21",
)
EXTENDED_CASE_IDS = CASE_IDS[1:]

REQUIRED_CONSTRAINTS = {
    "S04": {"same_support_surface", "collision_free", "task_completable"},
    "S05": {"initial_collision_free", "ik_reachable", "full_path_exists"},
    "S09": {
        "real_collision_geometry",
        "full_containment",
        "positive_clearance",
        "insertion_depth",
    },
    "S22": {
        "collision_geometry_unchanged",
        "friction_unchanged",
        "object_poses_unchanged",
    },
    "D05": {"alternate_collision_free_path_exists"},
    "D16": {"no_physical_contact"},
    "D17": {"retry_remains_possible"},
    "D18": {"recovery_remains_possible"},
    "D19": {"correction_remains_possible"},
    "D20": {
        "single_trigger",
        "joint_limits",
        "collision_free",
        "no_self_collision",
        "workspace_clearance",
    },
    "D21": {"semantic_goal_unchanged"},
}

REQUIRED_PARAMS = {
    "S06": {"asset_id", "asset_scale"},
    "S07": {"geometry_factors", "goal_region_scale"},
    "S11": {"asset_id", "asset_scale"},
    "S13": {"color_rgb"},
    "S14": {"scene_color_mix", "scene_luminance_factors", "light_factor"},
    "S18": {
        "eef_offset_xyz",
        "joint_zero_offset_rad",
        "grasp_center_offset_xyz",
    },
    "S22": {"material_id", "texture_asset", "texture_scale"},
    "D17": {
        "grasp_distance_m",
        "grasp_initial_tolerance_m",
        "contact_fallback_distance_m",
        "wrapper_fallback_distance_m",
        "articulation_grasp_distance_m",
    },
    "D19": {"misplace_offset_xy", "misplace_height_m"},
    "D20": {
        "trigger_eef_motion_m",
        "trigger_action_norm",
        "joint_delta_rad",
        "min_eef_displacement_m",
        "min_workspace_clearance_m",
        "penetration_tolerance_m",
    },
}

VECTOR_LENGTHS = {
    "asset_geometry_factors": 3,
    "asset_offset_xyz": 3,
    "asset_quat": 4,
    "barrier_geometry_factors": 3,
    "camera_offset_xyz": 3,
    "camera_rotation_rpy": 3,
    "clutter_offsets_xy": None,
    "color_rgb": 3,
    "eef_offset_xyz": 3,
    "fixture_geometry_factors": 3,
    "geometry_factors": 3,
    "goal_region_scale": 3,
    "grasp_center_offset_xyz": 3,
    "image_shift_xy": 2,
    "joint_zero_offset_rad": 3,
    "misplace_offset_xy": 2,
    "occlusion_offset_xyz": 3,
    "offset_xy": 2,
    "receiver_geometry_factors": 3,
    "scene_luminance_factors": 3,
    "swap_xy": 2,
    "target_geometry_factors": 3,
    "texture_scale": 2,
}

POSITIVE_VECTOR_PARAMS = {
    "asset_geometry_factors",
    "barrier_geometry_factors",
    "fixture_geometry_factors",
    "geometry_factors",
    "goal_region_scale",
    "receiver_geometry_factors",
    "scene_luminance_factors",
    "target_geometry_factors",
    "texture_scale",
}

POSITIVE_SCALAR_PARAMS = {
    "asset_scale",
    "articulation_grasp_distance_m",
    "clutter_minimum_gap_m",
    "contact_fallback_distance_m",
    "grasp_distance_m",
    "grasp_initial_tolerance_m",
    "height_delta_m",
    "joint_delta_rad",
    "min_eef_displacement_m",
    "min_workspace_clearance_m",
    "minimum_clearance_m",
    "minimum_displacement_m",
    "misplace_minimum_gap_m",
    "penetration_tolerance_m",
    "swap_cluster_radius_m",
    "trigger_action_norm",
    "trigger_distance_m",
    "trigger_eef_motion_m",
    "wrapper_fallback_distance_m",
}

NONNEGATIVE_SCALAR_PARAMS = {
    "action_delay_steps",
    "arm_delay_steps",
    "delay_steps",
    "distortion_strength",
    "drop_count",
    "grounded_height_offset_m",
    "gripper_delay_steps",
    "lateral_offset_m",
    "observation_delay_steps",
    "recovery_retreat_m",
    "repeat_count",
    "stale_chunk_steps",
}

FRACTION_PARAMS = {
    "crop_ratio": (0.0, 1.0, False),
    "lighting_factor": (0.0, 1.0, True),
    "light_factor": (0.0, 1.0, True),
    "occlusion_fraction": (0.0, 1.0, False),
    "scene_color_mix": (0.0, 1.0, False),
}

VIRTUAL_ENTITIES = {
    "action",
    "action_chunk",
    "agentview",
    "arm",
    "control",
    "depth",
    "gripper",
    "inference",
    "observation",
    "proprioception",
    "replan",
    "rgb",
    "robot0",
    "robot0_eye_in_hand",
    "robot_future_path",
    "task_instruction",
    "workspace_surface",
}


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PARSER = _load_module("_all_task_safety_parser", PARSER_PATH)
RUNTIME = _load_module("_all_task_safety_runtime", RUNTIME_PATH)


def _canonical_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _names(value: Any) -> tuple[str, ...]:
    if value is None or isinstance(value, bool):
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return (str(value),)


def _case_fields(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fields_by_case: dict[str, dict[str, Any]] = {}
    for raw_entry in config.get("perturbations", []):
        if not isinstance(raw_entry, list) or not raw_entry:
            continue
        case_id = str(raw_entry[0]).upper()
        fields: dict[str, Any] = {}
        for value in raw_entry[1:]:
            if isinstance(value, dict):
                fields.update(value)
        fields_by_case[case_id] = fields
    return fields_by_case


def _declarations(tree: list[Any], group_name: str) -> tuple[str, ...]:
    group = next(
        (
            value
            for value in tree[2:]
            if isinstance(value, list) and value and value[0] == group_name
        ),
        None,
    )
    if group is None:
        return ()
    result: list[str] = []
    index = 1
    while index < len(group):
        names: list[str] = []
        while index < len(group) and group[index] != "-":
            names.append(str(group[index]))
            index += 1
        if index + 1 >= len(group):
            raise ValueError(f"Malformed {group_name} declaration")
        result.extend(names)
        index += 2
    return tuple(result)


def _numeric_vector(
    value: Any, key: str, errors: list[dict[str, Any]]
) -> list[float] | None:
    raw = value if isinstance(value, list) else [value]
    try:
        vector = [float(item) for item in raw]
    except (TypeError, ValueError):
        errors.append({"code": "PARAM_NOT_NUMERIC_VECTOR", "field": key, "value": value})
        return None
    if not all(math.isfinite(item) for item in vector):
        errors.append({"code": "PARAM_NOT_FINITE", "field": key, "value": value})
        return None
    expected = VECTOR_LENGTHS[key]
    if expected is not None and len(vector) != expected:
        errors.append(
            {
                "code": "PARAM_VECTOR_LENGTH",
                "field": key,
                "expected": expected,
                "actual": len(vector),
            }
        )
    if key == "clutter_offsets_xy" and len(vector) % 2:
        errors.append(
            {"code": "PARAM_VECTOR_LENGTH", "field": key, "expected": "multiple of 2", "actual": len(vector)}
        )
    return vector


def _numeric_scalar(
    value: Any, key: str, errors: list[dict[str, Any]]
) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append({"code": "PARAM_NOT_NUMERIC", "field": key, "value": value})
        return None
    if not math.isfinite(number):
        errors.append({"code": "PARAM_NOT_FINITE", "field": key, "value": value})
        return None
    return number


def _validate_params(
    case_id: str, params: dict[str, Any], errors: list[dict[str, Any]]
) -> None:
    required = REQUIRED_PARAMS.get(case_id, set())
    if case_id == "S06" and bool(params.get("fixture_variant", False)):
        required = {"fixture_variant", "fixture_geometry_factors"}
    elif case_id == "S11" and bool(params.get("fixture_distractor", False)):
        required = {"fixture_distractor", "fixture_distractor_targets"}
    missing = sorted(required - set(params))
    if missing:
        errors.append({"code": "MISSING_REQUIRED_PARAMS", "fields": missing})

    mode = str(params.get("interaction_mode", ""))
    if mode not in {"placement", "articulation"}:
        errors.append(
            {"code": "INVALID_INTERACTION_MODE", "field": "interaction_mode", "value": mode}
        )

    vectors: dict[str, list[float]] = {}
    for key, value in params.items():
        if key in VECTOR_LENGTHS:
            parsed = _numeric_vector(value, key, errors)
            if parsed is not None:
                vectors[key] = parsed

    for key in POSITIVE_VECTOR_PARAMS & set(vectors):
        if any(value <= 0.0 for value in vectors[key]):
            errors.append({"code": "PARAM_MUST_BE_POSITIVE", "field": key, "value": vectors[key]})

    if "asset_quat" in vectors and math.sqrt(sum(value * value for value in vectors["asset_quat"])) <= 1e-8:
        errors.append({"code": "ZERO_QUATERNION", "field": "asset_quat"})

    if "color_rgb" in vectors and any(
        value < 0.0 or value > 1.0 for value in vectors["color_rgb"]
    ):
        errors.append({"code": "PARAM_OUT_OF_RANGE", "field": "color_rgb", "range": "[0, 1]"})

    for key in POSITIVE_SCALAR_PARAMS & set(params):
        value = _numeric_scalar(params[key], key, errors)
        if value is not None and value <= 0.0:
            errors.append({"code": "PARAM_MUST_BE_POSITIVE", "field": key, "value": value})

    for key in NONNEGATIVE_SCALAR_PARAMS & set(params):
        value = _numeric_scalar(params[key], key, errors)
        if value is not None and value < 0.0:
            errors.append({"code": "PARAM_MUST_BE_NONNEGATIVE", "field": key, "value": value})

    for key, (lower, upper, lower_exclusive) in FRACTION_PARAMS.items():
        if key not in params:
            continue
        value = _numeric_scalar(params[key], key, errors)
        if value is None:
            continue
        valid_lower = value > lower if lower_exclusive else value >= lower
        upper_exclusive = key == "crop_ratio"
        valid_upper = value < upper if upper_exclusive else value <= upper
        if not (valid_lower and valid_upper):
            errors.append(
                {"code": "PARAM_OUT_OF_RANGE", "field": key, "value": value, "range": f"{('(' if lower_exclusive else '[')}{lower}, {upper}{')' if upper_exclusive else ']'}"}
            )

    if "event_duration_steps" in params:
        value = _numeric_scalar(params["event_duration_steps"], "event_duration_steps", errors)
        if value is not None and (value < 1 or not value.is_integer()):
            errors.append(
                {"code": "INVALID_EVENT_DURATION", "field": "event_duration_steps", "value": value}
            )

    if "asset_count" in params:
        value = _numeric_scalar(params["asset_count"], "asset_count", errors)
        if value is not None and (not value.is_integer() or not 1 <= value <= 4):
            errors.append({"code": "INVALID_ASSET_COUNT", "field": "asset_count", "value": value})

    for key in ("chunk_size", "stale_chunk_steps"):
        if key not in params:
            continue
        value = _numeric_scalar(params[key], key, errors)
        if value is not None and (value < 1 or not value.is_integer()):
            errors.append({"code": "INVALID_POSITIVE_INTEGER", "field": key, "value": value})


def _validate_entity_references(
    plan: Any,
    objects: set[str],
    fixtures: set[str],
    errors: list[dict[str, Any]],
) -> None:
    declared = objects | fixtures | VIRTUAL_ENTITIES
    referenced = set(plan.targets) | set(plan.references) | set(plan.disturbance_targets or ())
    unknown = sorted(referenced - declared)
    if unknown:
        errors.append({"code": "UNKNOWN_ENTITY_REFERENCE", "entities": unknown})

    if plan.case_id == "S04" and str(plan.params.get("interaction_mode")) != "articulation":
        invalid = sorted(set(plan.targets) - objects)
        if len(plan.targets) != 2 or len(set(plan.targets)) != 2 or invalid:
            errors.append(
                {"code": "INVALID_S04_MOVABLE_TARGETS", "targets": list(plan.targets), "non_objects": invalid}
            )
    if plan.case_id == "S06":
        valid_targets = fixtures if bool(plan.params.get("fixture_variant", False)) else objects
        if len(plan.targets) != 1 or plan.targets[0] not in valid_targets:
            errors.append({"code": "INVALID_REPLACEMENT_TARGET", "targets": list(plan.targets)})
    if plan.case_id == "D06" and plan.disturbance_targets is not None:
        values = tuple(plan.disturbance_targets)
        invalid = sorted(set(values) - objects)
        if len(values) != len(set(values)) or invalid:
            errors.append(
                {"code": "INVALID_DISTURBANCE_TARGETS", "targets": list(values), "non_objects": invalid}
            )


def _audit_entry(entry: dict[str, Any]) -> dict[str, Any]:
    suite = str(entry.get("suite", ""))
    task_id = int(entry.get("base_task_id", -1))
    case_id = str(entry.get("case_id", "")).upper()
    relative_path = str(entry.get("bddl_path", ""))
    path = ASSETS_ROOT / relative_path
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    expected_kind = "base" if case_id == "BASE" else "static" if case_id.startswith("S") else "dynamic"
    if entry.get("case_kind") != expected_kind:
        errors.append(
            {"code": "MANIFEST_CASE_KIND_MISMATCH", "expected": expected_kind, "actual": entry.get("case_kind")}
        )
    if not path.is_file():
        errors.append({"code": "MISSING_BDDL"})
        return {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": case_id,
            "bddl_path": relative_path,
            "status": "STATIC_REVIEW",
            "errors": errors,
            "warnings": warnings,
        }

    actual_hash = _canonical_hash(path)
    if entry.get("bddl_sha256") != actual_hash:
        errors.append(
            {"code": "MANIFEST_HASH_MISMATCH", "expected": entry.get("bddl_sha256"), "actual": actual_hash}
        )

    try:
        config = PARSER.parse_bddl_perturbation_config(path)
        tree = PARSER.scan_tokens(filename=str(path))
        if not isinstance(tree, list) or not tree or tree[0] != "define":
            raise ValueError("BDDL root is not a define expression")
        objects = set(_declarations(tree, ":objects"))
        fixtures = set(_declarations(tree, ":fixtures"))
    except Exception as exc:
        errors.append({"code": "BDDL_PARSE_ERROR", "error": f"{type(exc).__name__}: {exc}"})
        return {
            "suite": suite,
            "base_task_id": task_id,
            "case_id": case_id,
            "bddl_path": relative_path,
            "status": "STATIC_REVIEW",
            "errors": errors,
            "warnings": warnings,
        }

    active = tuple(value.upper() for value in _names(config.get("active_cases")))
    declared = str(config.get("case_id", "")).upper()
    expected_active = {("BASE",), ("NONE",)} if case_id == "BASE" else {(case_id,)}
    if active not in expected_active or declared != case_id:
        errors.append(
            {"code": "ACTIVE_CASE_MISMATCH", "manifest": case_id, "active_cases": list(active), "declared_case": declared}
        )
    if str(config.get("case_kind", "")) != expected_kind:
        errors.append(
            {"code": "BDDL_CASE_KIND_MISMATCH", "expected": expected_kind, "actual": config.get("case_kind")}
        )
    if str(config.get("source_suite", "")) != suite:
        errors.append(
            {"code": "SOURCE_SUITE_MISMATCH", "expected": suite, "actual": config.get("source_suite")}
        )

    source_task = path.stem.split("__", 1)[-1]
    if str(config.get("source_task", "")).casefold() != source_task.casefold():
        errors.append(
            {"code": "SOURCE_TASK_MISMATCH", "expected": source_task, "actual": config.get("source_task")}
        )

    fields_by_case = _case_fields(config)
    schema_version = int(config.get("schema_version", 0))
    expected_catalog = set(EXTENDED_CASE_IDS if schema_version >= 5 else LEGACY_CASE_IDS)
    actual_catalog = set(fields_by_case)
    if actual_catalog != expected_catalog:
        errors.append(
            {
                "code": "CASE_CATALOG_MISMATCH",
                "missing": sorted(expected_catalog - actual_catalog),
                "unexpected": sorted(actual_catalog - expected_catalog),
                "schema_version": schema_version,
            }
        )

    plan = None
    try:
        plan = RUNTIME.build_execution_plan(config, ASSET_ROOT)
    except Exception as exc:
        errors.append({"code": "EXECUTION_PLAN_ERROR", "error": f"{type(exc).__name__}: {exc}"})

    if plan is not None and case_id != "BASE":
        fields = fields_by_case.get(case_id, {})
        params = plan.params if isinstance(plan.params, dict) else {}
        constraints = set(plan.constraints)
        required_constraints = REQUIRED_CONSTRAINTS.get(case_id, set())
        missing_constraints = sorted(required_constraints - constraints)
        if missing_constraints:
            errors.append({"code": "MISSING_SAFETY_CONSTRAINTS", "constraints": missing_constraints})
        if not plan.operator or not plan.variant:
            errors.append({"code": "MISSING_OPERATOR_OR_VARIANT"})
        if case_id.startswith("D") and not fields.get("trigger"):
            errors.append({"code": "MISSING_DYNAMIC_TRIGGER"})
        _validate_params(case_id, params, errors)
        _validate_entity_references(plan, objects, fixtures, errors)

        support_surface = _names(params.get("support_surface"))
        unknown_support = sorted(
            value
            for value in support_surface
            if value not in objects
            and value not in fixtures
            and not any(token in value.casefold() for token in ("table", "floor", "counter", "stove", "cabinet", "rack", "drawer", "shelf", "tray", "plate", "basket"))
        )
        if unknown_support:
            errors.append({"code": "UNKNOWN_SUPPORT_SURFACE", "surfaces": unknown_support})

        if case_id == "S22":
            texture = ASSET_ROOT.parent / str(params.get("texture_asset", ""))
            if not texture.is_file():
                errors.append({"code": "MISSING_TEXTURE_ASSET", "path": str(texture)})

    return {
        "suite": suite,
        "base_task_id": task_id,
        "case_id": case_id,
        "bddl_path": relative_path,
        "schema_version": schema_version,
        "declared_objects": len(objects),
        "declared_fixtures": len(fixtures),
        "status": "PASS" if not errors else "STATIC_REVIEW",
        "errors": errors,
        "warnings": warnings,
    }


def _manifest_checks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    keys = [
        (str(item.get("suite")), int(item.get("base_task_id", -1)), str(item.get("case_id", "")).upper())
        for item in tasks
    ]
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    if duplicates:
        errors.append({"code": "DUPLICATE_MANIFEST_KEYS", "keys": duplicates})
    expected = {
        (suite, task_id, case_id)
        for suite in SUITES
        for task_id in range(10)
        for case_id in CASE_IDS
        if case_id != "D19"
        and (suite, task_id, case_id) not in GOAL_NOT_APPLICABLE
        and (suite, task_id, case_id) not in PUBLISHED_EXCLUDED
    }
    actual = set(keys)
    if actual != expected:
        errors.append(
            {"code": "MANIFEST_MATRIX_MISMATCH", "missing": sorted(expected - actual), "unexpected": sorted(actual - expected)}
        )
    return errors


def _summary(results: Iterable[dict[str, Any]], manifest_errors: list[dict[str, Any]]) -> dict[str, Any]:
    values = list(results)
    status_counts = Counter(str(item["status"]) for item in values)
    error_counts = Counter(
        str(error["code"])
        for item in values
        for error in item.get("errors", [])
    )
    case_reviews: dict[str, int] = defaultdict(int)
    for item in values:
        if item["status"] != "PASS":
            case_reviews[str(item["case_id"])] += 1
    return {
        "task_count": len(values),
        "manifest_errors": len(manifest_errors),
        "status_counts": dict(sorted(status_counts.items())),
        "error_counts": dict(sorted(error_counts.items())),
        "review_counts_by_case": dict(sorted(case_reviews.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tasks = list(payload.get("tasks", []))
    manifest_errors = _manifest_checks(tasks)
    if payload.get("manifest_version") != PUBLISHED_MANIFEST_VERSION:
        manifest_errors.append(
            {"code": "MANIFEST_VERSION_MISMATCH", "actual": payload.get("manifest_version")}
        )
    if payload.get("task_count") != len(tasks) or len(tasks) != PUBLISHED_TASK_COUNT:
        manifest_errors.append(
            {"code": "MANIFEST_TASK_COUNT_MISMATCH", "declared": payload.get("task_count"), "actual": len(tasks)}
        )

    results = []
    for index, entry in enumerate(tasks, start=1):
        result = _audit_entry(entry)
        results.append(result)
        if result["status"] != "PASS":
            print(
                json.dumps(
                    {
                        "index": index,
                        "key": [result["suite"], result["base_task_id"], result["case_id"]],
                        "status": result["status"],
                        "errors": result["errors"],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        elif index % 100 == 0:
            print(f"[static] {index}/{len(tasks)}", flush=True)

    summary = _summary(results, manifest_errors)
    report = {
        "audit_type": "static_non_rollout",
        "manifest": str(MANIFEST),
        "manifest_errors": manifest_errors,
        "summary": summary,
        "results": results,
    }
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "static_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    print(f"Report: {report_path}", flush=True)
    raise SystemExit(1 if manifest_errors or summary["status_counts"].get("STATIC_REVIEW") else 0)


if __name__ == "__main__":
    main()
