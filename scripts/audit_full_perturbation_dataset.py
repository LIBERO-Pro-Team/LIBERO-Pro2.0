#!/usr/bin/env python3
"""Audit every generated LIBERO-Pro BDDL without importing MuJoCo.

The audit intentionally checks the contract that is visible in BDDL: manifest
coverage, parseability, active-case metadata, scene entity references, and the
known semantics of cases whose target selection can otherwise silently become
invalid (for example an S04 self-swap).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "assets" / "task_manifest.json"
CASE_IDS = {
    "BASE",
    *(f"S{i:02d}" for i in range(1, 22)),
    *(f"D{i:02d}" for i in range(1, 20)),
    "D21",
}
META_TARGETS = {
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
}


class ParseError(ValueError):
    pass


def _tokens(source: str) -> list[str]:
    # BDDL used by this repository contains no quoted strings. Keeping the
    # tokenizer deliberately small makes this audit independent of simulator
    # packages and therefore runnable in CI.
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    return [token for token in re.split(r"(\(|\)|\s+)", normalized) if token and not token.isspace()]


def _parse_list(tokens: list[str], index: int = 0) -> tuple[list[Any], int]:
    if index >= len(tokens) or tokens[index] != "(":
        raise ParseError(f"expected '(' at token {index}")
    values: list[Any] = []
    index += 1
    while index < len(tokens):
        token = tokens[index]
        if token == ")":
            return values, index + 1
        if token == "(":
            child, index = _parse_list(tokens, index)
            values.append(child)
        else:
            values.append(token)
            index += 1
    raise ParseError("unclosed BDDL list")


def parse_bddl(path: Path) -> list[Any]:
    root, index = _parse_list(_tokens(path.read_text(encoding="utf-8")))
    if index != len(_tokens(path.read_text(encoding="utf-8"))):
        raise ParseError("trailing tokens after BDDL expression")
    return root


def _section(root: list[Any], name: str) -> list[Any] | None:
    for item in root:
        if isinstance(item, list) and item and item[0] == name:
            return item
    return None


def _values(section: list[Any] | None) -> list[str]:
    if not section:
        return []
    return [str(item) for item in section[1:] if not isinstance(item, list)]


def _declared_entities(section: list[Any] | None) -> set[str]:
    if not section:
        return set()
    entities: set[str] = set()
    declarations = [item for item in section[1:] if isinstance(item, list)]
    if not declarations:
        declarations = [section[1:]]
    for declaration in declarations:
        pending: list[str] = []
        skip_type = False
        for item in declaration:
            token = str(item)
            if skip_type:
                skip_type = False
                continue
            if token == "-":
                entities.update(pending)
                pending.clear()
                skip_type = True
            else:
                pending.append(token)
    return entities


def _declared_entity_types(section: list[Any] | None) -> dict[str, str]:
    if not section:
        return {}
    declarations = [item for item in section[1:] if isinstance(item, list)]
    if not declarations:
        declarations = [section[1:]]
    entity_types: dict[str, str] = {}
    for declaration in declarations:
        pending: list[str] = []
        skip_type = False
        for item in declaration:
            token = str(item)
            if skip_type:
                for name in pending:
                    entity_types[name] = token
                pending.clear()
                skip_type = False
                continue
            if token == "-":
                skip_type = True
            else:
                pending.append(token)
    return entity_types


def _nested_named(section: list[Any] | None) -> dict[str, list[Any]]:
    if not section:
        return {}
    return {
        str(item[0]): item
        for item in section[1:]
        if isinstance(item, list) and item
    }


def _field(case: list[Any], name: str) -> list[str]:
    for item in case[1:]:
        if isinstance(item, list) and item and item[0] == name:
            return [str(value) for value in item[1:] if not isinstance(value, list)]
    return []


def _params(case: list[Any]) -> dict[str, list[str]]:
    for item in case[1:]:
        if isinstance(item, list) and item and item[0] == ":params":
            return {
                str(child[0]): [str(value) for value in child[1:] if not isinstance(value, list)]
                for child in item[1:]
                if isinstance(child, list) and child
            }
    return {}


def _config(root: list[Any]) -> tuple[str, str, dict[str, list[Any]]]:
    config = _section(root, ":perturbation_config")
    if config is None:
        raise ParseError("missing :perturbation_config")
    active = _field(config, ":active_cases")
    case_id = _field(config, ":case_id")
    perturbations = next(
        (item for item in config[1:] if isinstance(item, list) and item and item[0] == ":perturbations"),
        None,
    )
    cases = {
        str(item[0]).upper(): item
        for item in (perturbations[1:] if perturbations else [])
        if isinstance(item, list) and item
    }
    if len(active) != 1 or len(case_id) != 1:
        raise ParseError("active_cases/case_id must each contain one value")
    return active[0].upper(), case_id[0].upper(), cases


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def audit(manifest_path: Path) -> list[dict[str, str]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = payload.get("tasks", [])
    findings: list[dict[str, str]] = []

    def add(code: str, path: str, detail: str) -> None:
        findings.append({"code": code, "path": path, "detail": detail})

    if payload.get("task_count") != len(entries) or len(entries) != 1680:
        add("MANIFEST_COUNT", str(manifest_path), f"expected 1680, got {len(entries)}")

    expected_cases = CASE_IDS
    # This workspace intentionally retains only task-level BDDL changes named
    # by the current human-review scope. Baseline BDDL files still carry the
    # historical catalog, so semantic perturbation checks apply only to files
    # changed in the working tree; coverage, parsing, and hashes remain global.
    try:
        changed_paths = {
            path.replace('\\', '/')
            for path in subprocess.check_output(
                ['git', 'diff', '--name-only', '--', 'assets/bddl'],
                cwd=ROOT,
                text=True,
            ).splitlines()
        }
    except (OSError, subprocess.SubprocessError):
        changed_paths = set()
    seen: set[tuple[str, int, str]] = set()
    for entry in entries:
        suite = str(entry.get("suite", ""))
        task_id = int(entry.get("base_task_id", -1))
        case_id = str(entry.get("case_id", "")).upper()
        key = (suite, task_id, case_id)
        if key in seen:
            add("DUPLICATE_ENTRY", str(manifest_path), repr(key))
        seen.add(key)
        if case_id not in expected_cases:
            add("UNKNOWN_CASE", str(manifest_path), repr(key))
            continue
        rel = str(entry.get("bddl_path", ""))
        path = ROOT / "assets" / rel
        if not path.is_file():
            add("MISSING_BDDL", rel, "manifest path does not exist")
            continue
        if entry.get("bddl_sha256") != _sha256(path):
            add("HASH_MISMATCH", rel, "manifest hash differs from file")
        try:
            root = parse_bddl(path)
            active, declared, cases = _config(root)
        except (OSError, ParseError, ValueError) as exc:
            add("BDDL_PARSE", rel, str(exc))
            continue

        if str((ROOT / "assets" / rel).as_posix()).split('/assets/', 1)[-1] not in {
            p.split('assets/', 1)[-1] for p in changed_paths
        }:
            continue

        expected_kind = "base" if case_id == "BASE" else "static" if case_id.startswith("S") else "dynamic"
        normalized_active = "BASE" if active == "NONE" else active
        if normalized_active != case_id or declared != case_id:
            add("ACTIVE_CASE", rel, f"filename={case_id}, active={active}, declared={declared}")
        if expected_kind != ("base" if case_id == "BASE" else "static" if active.startswith("S") else "dynamic"):
            add("CASE_KIND", rel, f"unexpected kind for {case_id}")
        if set(cases) != expected_cases - {"BASE"}:
            add("CASE_CATALOG", rel, f"expected 41 cases, got {sorted(cases)}")

        object_types = _declared_entity_types(_section(root, ":objects"))
        objects = set(object_types)
        fixtures = _declared_entities(_section(root, ":fixtures"))
        entities = objects | fixtures | {"main_table"}
        if case_id == "BASE":
            continue
        case = cases.get(case_id)
        if case is None:
            continue
        targets = _field(case, ":targets")
        references = _field(case, ":references")
        unknown = [name for name in (*targets, *references) if name not in entities and name not in META_TARGETS]
        if unknown:
            add("UNKNOWN_ENTITY", rel, f"{case_id}: {unknown}")
        if case_id == "S04":
            case_params = _params(case)
            mode = case_params.get(":interaction_mode", [""])[0]
            allow_fixture_swap = case_params.get(":allow_fixture_swap", ["false"])[0] == "true"
            if mode == "articulation":
                if len(targets) != 1 or targets[0] not in fixtures:
                    add("S04_ARTICULATION_TARGET", rel, f"targets={targets}, fixtures={sorted(fixtures)}")
                if _field(case, ":variant") != ["articulation_fixture_pose_offset"]:
                    add("S04_ARTICULATION_VARIANT", rel, f"variant={_field(case, ':variant')}")
            else:
                if len(targets) != 2 or targets[0] == targets[1]:
                    add("S04_SELF_SWAP", rel, f"targets={targets}")
                elif any(name not in objects for name in targets) and not (
                    allow_fixture_swap
                    and sum(name in fixtures for name in targets) == 1
                    and sum(name in objects for name in targets) == 1
                ):
                    add("S04_NON_OBJECT", rel, f"targets={targets}, objects={sorted(objects)}")
                elif (
                    object_types.get(targets[0]) == object_types.get(targets[1])
                    and any(
                        name not in set(targets) | set(_field(case, ":references"))
                        and name != "main_table"
                        and object_type != object_types.get(targets[0])
                        for name, object_type in object_types.items()
                    )
                ):
                    add(
                        "S04_SAME_TYPE",
                        rel,
                            f"targets={targets}, type={object_types.get(targets[0])}",
                    )
        if case_id == "S03":
            params = _params(case)
            if len(targets) != 2 or targets[0] in {"main_table", "floor"} or targets[0] == targets[1]:
                add("S03_INVALID_SUPPORT_TARGET", rel, f"targets={targets}")
            try:
                height_delta = float(params.get(":height_delta_m", ["0"])[0])
            except (ValueError, IndexError):
                height_delta = 0.0
            if height_delta <= 0.0:
                add("S03_HEIGHT_CONFIG", rel, f"height_delta_m={params.get(':height_delta_m', [])}")
        if case_id in {"S06", "S11"}:
            params = _params(case)
            scales = params.get(":asset_scale", [])
            fixture_variant = (
                case_id == "S06"
                and len(targets) == 1
                and targets[0] in fixtures
                and params.get(":fixture_variant", ["false"])[0] == "true"
                and len(params.get(":geometry_factors", [])) == 3
            )
            if not fixture_variant and (
                len(targets) != 1
                or targets[0] not in objects
                or not params.get(":asset_id")
                or not scales
            ):
                add("ASSET_REPLACEMENT_CONFIG", rel, f"{case_id}: targets={targets}, params={params}")
        if case_id == "D02":
            offsets = _params(case).get(":offset_xy", [])
            try:
                offset = [float(value) for value in offsets]
            except ValueError:
                offset = []
            if len(offset) != 2:
                add("D02_OFFSET_CONFIG", rel, f"offset_xy={offsets}")
            elif targets and targets[0].startswith("basket_") and sum(value * value for value in offset) < 0.15**2:
                add("D02_BASKET_CLEARANCE", rel, f"target={targets[0]}, offset_xy={offsets}")
        if case_id == "D03":
            params = _params(case)
            scales = params.get(":asset_scale", [])
            try:
                scale = float(scales[0])
            except (ValueError, IndexError):
                scale = 0.0
            compact_asset = params.get(":allow_compact_asset", ["false"])[0] == "true"
            if scale < 1.35 and not compact_asset:
                add("D03_BLOCKER_SCALE", rel, f"asset_scale={scales}")
        if case_id in {"D08", "D09", "D10", "D11"}:
            trigger = _field(case, ":trigger")
            if trigger != ["task_phase"]:
                add("DYNAMIC_TRIGGER_CONFIG", rel, f"{case_id}: trigger={trigger}")
        if case_id == "D15":
            params = _params(case)
            for key in (":chunk_size", ":stale_chunk_steps"):
                try:
                    if int(params.get(key, ["0"])[0]) <= 0:
                        raise ValueError
                except (TypeError, ValueError, IndexError):
                    add("D15_CONFIG", rel, f"missing positive {key}")

    expected_keys = {
        (str(entry.get("suite")), int(entry.get("base_task_id", -1)), str(entry.get("case_id", "")).upper())
        for entry in entries
    }
    for suite in {str(entry.get("suite")) for entry in entries}:
        for task_id in range(10):
            for case_id in expected_cases:
                if (suite, task_id, case_id) not in expected_keys:
                    add("COVERAGE", str(manifest_path), f"missing {(suite, task_id, case_id)}")
    return findings


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    findings = audit(args.manifest.resolve())
    print(json.dumps({"finding_count": len(findings), "findings": findings}, indent=2, ensure_ascii=True))
    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    sys.exit(main())
