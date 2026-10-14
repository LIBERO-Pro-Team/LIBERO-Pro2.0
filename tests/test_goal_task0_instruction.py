"""Task0 language contracts without simulator or policy dependencies."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SPEC = importlib.util.spec_from_file_location(
    "_goal_task0_instruction_parser",
    ROOT / "simulator-source/libero/libero/envs/perturbation_config.py",
)
PARSER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PARSER)

BROWN_CASES = (
    "D01 D04 D06 D07 D08 D09 D10 D11 D12 D13 D14 D15 D16 D20 "
    "S01 S03 S04 S07 S08 S09 S10 S11 S12 S15 S16 S17 S18 S19 S20 S22"
).split()
EXCLUDED_CASES = "BASE S06 S13 S14 S21 D21".split()


@pytest.fixture(scope="module")
def task0_entries():
    manifest = json.loads((ASSETS / "task_manifest.json").read_text(encoding="utf-8"))
    return {
        entry["case_id"]: entry
        for entry in manifest["tasks"]
        if entry["suite"] == "libero_goal" and int(entry["base_task_id"]) == 0
    }


def test_task0_instruction_scope(task0_entries):
    assert set(task0_entries) == set(BROWN_CASES + EXCLUDED_CASES)


@pytest.mark.parametrize("case", BROWN_CASES + EXCLUDED_CASES)
def test_task0_language_and_middle_drawer_goal(task0_entries, case):
    entry = task0_entries[case]
    path = ASSETS / entry["bddl_path"]
    tokens = PARSER.scan_tokens(filename=str(path))
    sections = {node[0]: node[1:] for node in tokens[1:] if isinstance(node, list)}
    expected = (
        "Open the middle drawer of the brown cabinet"
        if case in BROWN_CASES else "Open the middle layer of the drawer"
    )
    assert " ".join(sections[":language"]).lower() == expected.lower()
    assert len(sections[":goal"]) == 1
    conjunction, predicate = sections[":goal"][0]
    assert conjunction.lower() == "and"
    assert [token.lower() for token in predicate] == [
        "open", "wooden_cabinet_1_middle_region"
    ]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["bddl_sha256"]
