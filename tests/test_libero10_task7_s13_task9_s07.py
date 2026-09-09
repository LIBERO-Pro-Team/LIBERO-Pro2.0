from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARSER_PATH = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "envs"
    / "perturbation_config.py"
)
SPEC = importlib.util.spec_from_file_location("_libero10_two_task_parser", PARSER_PATH)
assert SPEC is not None and SPEC.loader is not None
PARSER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PARSER)

SUITE_ROOT = (
    ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1" / "libero_10"
)
TASK7_S13 = (
    SUITE_ROOT
    / "01_static"
    / "S13__LIVING_ROOM_SCENE1_put_both_the_alphabet_soup_and_the_cream_cheese_box_in_the_basket.bddl"
)
TASK7_BASE = (
    SUITE_ROOT
    / "00_base"
    / "BASE__LIVING_ROOM_SCENE1_put_both_the_alphabet_soup_and_the_cream_cheese_box_in_the_basket.bddl"
)
TASK9_S07 = (
    SUITE_ROOT
    / "01_static"
    / "S07__KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it.bddl"
)
TASK9_BASE = (
    SUITE_ROOT
    / "00_base"
    / "BASE__KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it.bddl"
)


def _case_fields(path: Path, case_id: str) -> dict[str, object]:
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


def test_task7_s13_recolors_both_manipulated_objects_without_changing_base() -> None:
    task_fields = _case_fields(TASK7_S13, "S13")
    base_fields = _case_fields(TASK7_BASE, "S13")

    assert task_fields["targets"] == [
        "alphabet_soup_1",
        "cream_cheese_1",
        "basket_1",
    ]
    assert task_fields["params"]["color_rgb"] == [0.18, 0.72, 0.38]
    assert base_fields["targets"] == ["alphabet_soup_1", "basket_1"]


def test_task9_s07_opts_into_compiled_door_scaling_without_changing_base() -> None:
    task_params = _case_fields(TASK9_S07, "S07")["params"]
    base_params = _case_fields(TASK9_BASE, "S07")["params"]

    assert task_params["geometry_factors"] == [1.0, 0.64, 1.20]
    assert task_params["goal_region_scale"] == [1.0, 1.0, 1.0]
    assert task_params["scale_compiled_geometry"] is True
    assert "scale_compiled_geometry" not in base_params


def test_only_task9_s07_enables_compiled_scaling_among_libero10_s07_cases() -> None:
    opted_in = []
    for path in sorted((SUITE_ROOT / "01_static").glob("S07__*.bddl")):
        params = _case_fields(path, "S07")["params"]
        if params.get("scale_compiled_geometry") is True:
            opted_in.append(path)

    assert opted_in == [TASK9_S07]
