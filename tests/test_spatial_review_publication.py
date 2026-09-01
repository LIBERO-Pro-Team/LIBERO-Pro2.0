from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SELECTED_TASKS = {
    "S03": {0},
    "S06": {0, 2, 4, 5, 8},
    "S10": {0, 4, 7, 9},
    "S11": {0, 1, 3, 4, 5, 7, 8, 9},
    "D01": {3},
}


def _case_block(text: str, case_id: str) -> str:
    match = re.search(rf"(?m)^[ \t]*\({re.escape(case_id)}[ \t]*$", text)
    assert match is not None
    depth = 0
    for index in range(match.start(), len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise AssertionError(f"Unterminated {case_id} block")


def _param(block: str, name: str) -> tuple[str, ...]:
    match = re.search(rf"\(:{re.escape(name)}\s+([^)]+)\)", block)
    assert match is not None, name
    return tuple(match.group(1).split())


def _selected_entries() -> dict[tuple[str, int], dict[str, object]]:
    manifest = json.loads(
        (ASSETS / "task_manifest.json").read_text(encoding="utf-8")
    )
    return {
        (str(item["case_id"]), int(item["base_task_id"])): item
        for item in manifest["tasks"]
        if item["suite"] == "libero_spatial"
        and int(item["base_task_id"])
        in SELECTED_TASKS.get(str(item["case_id"]), set())
    }


def _selected_blocks() -> dict[tuple[str, int], str]:
    blocks: dict[tuple[str, int], str] = {}
    for key, item in _selected_entries().items():
        path = ASSETS / str(item["bddl_path"])
        blocks[key] = _case_block(path.read_text(encoding="utf-8"), key[0])
        digest = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        ).hexdigest()
        assert item["bddl_sha256"] == digest, path
    return blocks


def test_spatial_review_publication_contains_exactly_19_selected_tasks() -> None:
    expected = {
        (case_id, task_id)
        for case_id, task_ids in SELECTED_TASKS.items()
        for task_id in task_ids
    }
    assert set(_selected_entries()) == expected
    assert len(expected) == 19


def test_spatial_review_parameters_match_validated_values() -> None:
    blocks = _selected_blocks()

    assert _param(blocks[("S03", 0)], "asset_geometry_factors") == (
        "0.70",
        "0.70",
        "2.0",
    )
    assert _param(blocks[("S03", 0)], "height_delta_m") == ("0.055",)

    for task_id in SELECTED_TASKS["S06"]:
        assert _param(blocks[("S06", task_id)], "asset_id") == (
            "github/object_sim_bowl",
        )
        assert _param(blocks[("S06", task_id)], "asset_scale") == ("0.70",)

    for task_id in SELECTED_TASKS["S10"]:
        block = blocks[("S10", task_id)]
        assert _param(block, "movable_asset") == ("true",)
        assert _param(block, "physical_collision") == ("true",)
        assert _param(block, "visual_only_asset") == ("false",)
        assert _param(block, "clear_of_task_entities") == ("true",)
        assert _param(block, "asset_contact_margin_m") == ("0.006",)

    for task_id in SELECTED_TASKS["S11"]:
        block = blocks[("S11", task_id)]
        assert _param(block, "movable_asset") == ("true",)
        assert _param(block, "physical_collision") == ("true",)
        assert _param(block, "visual_only_asset") == ("false",)
        assert _param(block, "clear_of_task_entities") == ("true",)

    for task_id in {0, 1, 3, 5, 7, 8}:
        assert _param(blocks[("S11", task_id)], "asset_id") == (
            "github/object_sim_bowl",
        )
        assert _param(blocks[("S11", task_id)], "asset_scale") == ("0.70",)

    assert _param(blocks[("S11", 4)], "asset_id") == ("prl/plastic_bowl",)
    assert _param(blocks[("S11", 4)], "asset_scale") == ("0.60",)
    assert _param(blocks[("S11", 4)], "clutter_offsets_xy") == ("0.12", "0.10")
    assert _param(blocks[("S11", 4)], "support_surface") == ("main_table",)

    assert _param(blocks[("S11", 9)], "asset_id") == ("prl/plastic_bowl",)
    assert _param(blocks[("S11", 9)], "asset_scale") == ("0.60",)
    assert _param(blocks[("S11", 9)], "clutter_offsets_xy") == ("0.17", "0.10")
    assert _param(blocks[("S11", 9)], "support_surface") == ("table",)
    assert _param(blocks[("S11", 9)], "asset_contact_margin_m") == ("0.004",)

    d01 = blocks[("D01", 3)]
    assert _param(d01, "offset_xy") == ("0.020", "-0.015")
    assert _param(d01, "yaw_rad") == ("0.28",)
    assert _param(d01, "support_surface") == ("cookies_1",)
    assert _param(d01, "preserve_original_support_relation") == ("true",)
    assert _param(d01, "support_relation_clearance_m") == ("0.018",)


def test_object_sim_bowl_is_published_as_an_explicit_asset() -> None:
    catalog = json.loads(
        (
            ROOT
            / "simulator-source"
            / "libero"
            / "libero"
            / "assets"
            / "perturbation_assets"
            / "asset_catalog.json"
        ).read_text(encoding="utf-8")
    )
    bowl = next(
        asset for asset in catalog["assets"] if asset["id"] == "github/object_sim_bowl"
    )
    xml_path = (
        ROOT
        / "simulator-source"
        / "libero"
        / "libero"
        / "assets"
        / "perturbation_assets"
        / bowl["path"]
    )
    assert bowl["license"] == "Apache-2.0"
    assert xml_path.is_file()
