from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINALIZER_PATH = ROOT / "scripts" / "apply_goal_review_finalization.py"
FINALIZER_SPEC = importlib.util.spec_from_file_location(
    "_goal_review_round3_finalizer", FINALIZER_PATH
)
assert FINALIZER_SPEC is not None and FINALIZER_SPEC.loader is not None
FINALIZER = importlib.util.module_from_spec(FINALIZER_SPEC)
sys.modules[FINALIZER_SPEC.name] = FINALIZER
FINALIZER_SPEC.loader.exec_module(FINALIZER)

PARSER_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "perturbation_config.py"
)
PARSER_SPEC = importlib.util.spec_from_file_location(
    "_goal_review_round3_parser", PARSER_PATH
)
assert PARSER_SPEC is not None and PARSER_SPEC.loader is not None
PARSER = importlib.util.module_from_spec(PARSER_SPEC)
PARSER_SPEC.loader.exec_module(PARSER)


def _active_fields(path: Path, case_id: str) -> dict[str, object]:
    config = PARSER.parse_bddl_perturbation_config(path)
    active = next(
        entry
        for entry in config["perturbations"]
        if isinstance(entry, list) and str(entry[0]).upper() == case_id
    )
    fields: dict[str, object] = {}
    for field in active[1:]:
        if isinstance(field, dict):
            fields.update(field)
    return fields


def _typed(values: tuple[str, ...]) -> object:
    parsed: list[object] = []
    for value in values:
        lowered = value.lower()
        if lowered in {"true", "false"}:
            parsed.append(lowered == "true")
            continue
        try:
            parsed.append(float(value))
        except ValueError:
            parsed.append(value)
    return parsed[0] if len(parsed) == 1 else parsed


def _published_entries() -> tuple[dict[str, object], dict[tuple[str, int, str], dict[str, object]]]:
    manifest = json.loads(FINALIZER.MANIFEST.read_text(encoding="utf-8"))
    entries = {
        (str(item["suite"]), int(item["base_task_id"]), str(item["case_id"])): item
        for item in manifest["tasks"]
    }
    return manifest, entries


def test_round3_scope_matches_the_52_reviewed_goal_combinations() -> None:
    assert len(FINALIZER.GOAL_REVIEW_ROUND3_FEEDBACK_KEYS) == 52
    assert FINALIZER.GOAL_REVIEW_ROUND3_DELETIONS == {
        (0, "D05"),
        (0, "D17"),
        (7, "D03"),
        (7, "D05"),
        (7, "S05"),
    }
    assert FINALIZER.GOAL_REVIEW_ROUND3_DELETIONS < (
        FINALIZER.GOAL_REVIEW_ROUND3_FEEDBACK_KEYS
    )
    assert {
        ("libero_goal", task_id, case_id)
        for task_id, case_id in FINALIZER.GOAL_REVIEW_ROUND3_DELETIONS
    } <= FINALIZER.GOAL_NOT_APPLICABLE


def test_round3_publication_contains_only_the_requested_goal_changes() -> None:
    manifest, entries = _published_entries()
    assert manifest["task_count"] == len(entries) == 1701

    for task_id, case_id in FINALIZER.GOAL_REVIEW_ROUND3_DELETIONS:
        assert ("libero_goal", task_id, case_id) not in entries

    for (task_id, case_id), expected in FINALIZER.GOAL_REVIEW_ROUND3_PARAMS.items():
        item = entries[("libero_goal", task_id, case_id)]
        fields = _active_fields(ROOT / "assets" / str(item["bddl_path"]), case_id)
        params = fields["params"]
        for name, values in expected.items():
            assert params[name] == _typed(values), (task_id, case_id, name, params)

    assert FINALIZER.GOAL_REVIEW_ROUND3_PARAMS[(2, "S02")]["offset_xy"] == (
        "-0.12",
        "-0.09",
    )
    assert FINALIZER.GOAL_REVIEW_ROUND3_PARAMS[(4, "S02")]["offset_xy"] == (
        "-0.12",
        "-0.09",
    )
    assert FINALIZER.GOAL_REVIEW_ROUND3_PARAMS[(6, "S03")][
        "asset_geometry_factors"
    ] == ("0.60", "0.60", "2.0")

    for (task_id, case_id), expected in FINALIZER.GOAL_REVIEW_ROUND3_FIELDS.items():
        item = entries[("libero_goal", task_id, case_id)]
        fields = _active_fields(ROOT / "assets" / str(item["bddl_path"]), case_id)
        for name, values in expected.items():
            assert fields[name] == _typed(values), (task_id, case_id, name, fields)


def test_round3_runtime_opt_ins_are_task_local() -> None:
    _, entries = _published_entries()
    trigger_anchors: set[tuple[str, int, str]] = set()
    articulation_scales: set[tuple[str, int, str]] = set()
    goal_dynamic_barrier_fractions: set[tuple[str, int, str]] = set()
    goal_s12_offsets: set[tuple[str, int, str]] = set()

    for key, item in entries.items():
        case_id = key[2]
        if case_id == "BASE":
            continue
        fields = _active_fields(ROOT / "assets" / str(item["bddl_path"]), case_id)
        params = fields.get("params", {})
        if "trigger_anchor" in params:
            trigger_anchors.add(key)
        if "articulation_joint_range_scale" in params:
            articulation_scales.add(key)
        if key[0] == "libero_goal" and case_id == "D05" and "barrier_path_fraction" in params:
            goal_dynamic_barrier_fractions.add(key)
        if key[0] == "libero_goal" and case_id == "S12" and "occlusion_offset_xyz" in params:
            goal_s12_offsets.add(key)

    assert trigger_anchors == {
        ("libero_goal", 0, case_id)
        for case_id in ("D04", "D08", "D09", "D10", "D11", "D12", "D16")
    }
    assert articulation_scales == {
        ("libero_goal", 3, "S07"),
        ("libero_goal", 3, "S09"),
    }
    assert goal_dynamic_barrier_fractions == {
        ("libero_goal", 1, "D05"),
        ("libero_goal", 6, "D05"),
    }
    assert goal_s12_offsets == {("libero_goal", 0, "S12")}


def test_round3_reuses_existing_grounded_s04_and_persistent_d03_fixes() -> None:
    _, entries = _published_entries()
    for task_id in (0, 7):
        item = entries[("libero_goal", task_id, "S04")]
        params = _active_fields(
            ROOT / "assets" / str(item["bddl_path"]), "S04"
        )["params"]
        assert params["ground_support_from_declared_surface"] is True

    task1_d03 = entries[("libero_goal", 1, "D03")]
    fields = _active_fields(
        ROOT / "assets" / str(task1_d03["bddl_path"]), "D03"
    )
    assert fields["variant"] == "persistent_triggered_receiver_occupation"
    assert fields["params"]["persistent_existing_obstacle"] is True


def test_round3_deleted_bddl_files_are_absent() -> None:
    goal = FINALIZER.DATASET / "libero_goal"
    expected_absent = {
        goal / "02_dynamic" / "D05__open_the_middle_drawer_of_the_cabinet.bddl",
        goal / "02_dynamic" / "D17__open_the_middle_drawer_of_the_cabinet.bddl",
        goal / "02_dynamic" / "D03__turn_on_the_stove.bddl",
        goal / "02_dynamic" / "D05__turn_on_the_stove.bddl",
        goal / "01_static" / "S05__turn_on_the_stove.bddl",
    }
    assert not any(path.exists() for path in expected_absent)
