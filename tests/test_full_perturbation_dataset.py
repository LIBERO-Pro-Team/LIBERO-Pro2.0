import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"
GENERATOR_PATH = ROOT / "scripts" / "build_full_perturbation_dataset.py"
SPEC = importlib.util.spec_from_file_location("_full_perturbation_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


def test_full_manifest_covers_the_published_1701_task_set() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = payload["tasks"]

    assert payload["manifest_version"] == "libero-pro2.0-1706-v1"
    assert payload["task_count"] == len(entries) == 1701
    assert len({(entry["suite"], entry["base_task_id"]) for entry in entries}) == 40
    assert {entry["case_id"] for entry in entries} == {
        "BASE",
        *(f"S{i:02d}" for i in range(1, 23)),
        *(f"D{i:02d}" for i in range(1, 19)),
        "D20",
        "D21",
    }
    assert not any(entry["case_id"] == "D19" for entry in entries)
    assert not any(
        entry["suite"] == "libero_10"
        and entry["base_task_id"] == 8
        and entry["case_id"] == "S04"
        for entry in entries
    )
    assert not {
        ("libero_goal", 0, "D05"),
        ("libero_goal", 0, "D17"),
        ("libero_goal", 7, "D03"),
        ("libero_goal", 7, "D05"),
        ("libero_goal", 7, "S05"),
    } & {
        (str(entry["suite"]), int(entry["base_task_id"]), str(entry["case_id"]))
        for entry in entries
    }
    assert all(
        entry["bddl_path"].startswith("bddl/libero-pro2.0-1680-v1/")
        for entry in entries
    )


def test_task8_moka_cases_use_the_builtin_yellow_moka_pot() -> None:
    task8 = GENERATOR.load_profile(
        "libero_10", 8, GENERATOR.SUITE_TASKS["libero_10"][8]
    )
    task2 = GENERATOR.load_profile(
        "libero_10", 2, GENERATOR.SUITE_TASKS["libero_10"][2]
    )

    task8_s06 = GENERATOR.case_entry("S06", task8, "S06")
    task8_s11 = GENERATOR.case_entry("S11", task8, "S11")
    task8_inactive_s06 = GENERATOR.case_entry("S06", task8, "S11")
    task2_s06 = GENERATOR.case_entry("S06", task2, "S06")
    task2_s11 = GENERATOR.case_entry("S11", task2, "S11")

    for active_entry in (task8_s06, task8_s11):
        assert "(:asset_id libero/yellow_moka_pot)" in active_entry
        assert "(:asset_scale 1.0)" in active_entry
    assert "(:asset_id prl/gelatin_box)" in task8_inactive_s06
    assert "(:asset_scale 0.7)" in task8_inactive_s06
    assert (task2.s06_asset, task2.s06_scale) == ("prl/gelatin_box", 0.70)
    assert (task2.s11_asset, task2.s11_scale) == ("prl/gelatin_box", 0.70)
    for active_entry in (task2_s06, task2_s11):
        assert "(:asset_id prl/gelatin_box)" in active_entry
        assert "(:asset_scale 0.7)" in active_entry


def test_yellow_moka_pot_is_published_for_s06_and_s11() -> None:
    catalog_path = (
        ROOT
        / "simulator-source"
        / "libero"
        / "libero"
        / "assets"
        / "perturbation_assets"
        / "asset_catalog.json"
    )
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    yellow_moka = next(
        asset for asset in catalog["assets"] if asset["id"] == "libero/yellow_moka_pot"
    )

    assert yellow_moka["dimensions_m"] == [0.07919095, 0.145216175, 0.154196375]
    assert (catalog_path.parent / yellow_moka["path"]).resolve().is_file()
    for case_id in ("S06", "S11"):
        coverage = next(
            item for item in catalog["perturbation_coverage"] if item["id"] == case_id
        )
        assert "libero/yellow_moka_pot" in coverage["asset_ids"]


def test_reviewed_moka_cases_activate_only_the_yellow_moka_pot() -> None:
    dataset_root = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
    static_root = dataset_root / "libero_10" / "01_static"
    task_name = "KITCHEN_SCENE8_put_both_moka_pots_on_the_stove.bddl"
    task2_name = "KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it.bddl"
    yellow_moka_files = sorted(
        path.relative_to(dataset_root).as_posix()
        for path in dataset_root.rglob("*.bddl")
        if "libero/yellow_moka_pot" in path.read_text(encoding="utf-8")
    )
    assert yellow_moka_files == [
        f"libero_10/01_static/S06__{task_name}",
        f"libero_10/01_static/S11__{task2_name}",
        f"libero_10/01_static/S11__{task_name}",
    ]

    for case_id in ("S06", "S11"):
        text = (static_root / f"{case_id}__{task_name}").read_text(encoding="utf-8")
        tree = GENERATOR.scan_tokens(text)
        config = next(
            item
            for item in tree
            if isinstance(item, list) and item and item[0] == ":perturbation_config"
        )
        perturbations = next(item for item in config if item[0] == ":perturbations")
        active_entry = next(item for item in perturbations if item[0] == case_id)
        params = next(item for item in active_entry if item[0] == ":params")
        values = {item[0]: item[1:] for item in params[1:]}
        assert values[":asset_id"] == ["libero/yellow_moka_pot"]
        assert values[":asset_scale"] == ["1.0"]
