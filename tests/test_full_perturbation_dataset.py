import json
import importlib.util
import runpy
from pathlib import Path

_AUDIT_SPEC = importlib.util.spec_from_file_location(
    "full_perturbation_audit",
    Path(__file__).resolve().parents[1] / "scripts" / "audit_full_perturbation_dataset.py",
)
assert _AUDIT_SPEC and _AUDIT_SPEC.loader
_AUDIT_MODULE = importlib.util.module_from_spec(_AUDIT_SPEC)
_AUDIT_SPEC.loader.exec_module(_AUDIT_MODULE)
audit = _AUDIT_MODULE.audit


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"
ASSET_ROOT = (
    ROOT
    / "simulator-source"
    / "libero"
    / "libero"
    / "assets"
    / "perturbation_assets"
)
ASSET_CATALOG = ASSET_ROOT / "asset_catalog.json"


def test_full_manifest_covers_40_base_tasks_and_43_perturbations() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = payload["tasks"]

    assert payload["manifest_version"] == "libero-pro2.0-1760-v1"
    assert payload["task_count"] == len(entries) == 1760
    assert len({(entry["suite"], entry["base_task_id"]) for entry in entries}) == 40
    assert {entry["case_id"] for entry in entries} == {
        "BASE",
        *(f"S{i:02d}" for i in range(1, 23)),
        *(f"D{i:02d}" for i in range(1, 22)),
    }
    assert all(
        entry["bddl_path"].startswith("bddl/libero-pro2.0-1680-v1/")
        for entry in entries
    )


def test_full_bddl_audit_has_no_semantic_findings() -> None:
    findings = audit(MANIFEST)
    assert findings == []


def test_spatial_s04_swaps_different_object_types() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = [
        entry
        for entry in payload["tasks"]
        if entry["suite"] == "libero_spatial" and entry["case_id"] == "S04"
    ]
    # Only task/case combinations named by the review files remain modified.
    entries = [entry for entry in entries if entry["base_task_id"] in {1, 3, 7, 9}]
    assert len(entries) == 4
    for entry in entries:
        path = ROOT / "assets" / entry["bddl_path"]
        source = path.read_text(encoding="utf-8")
        assert "(:targets akita_black_bowl_1 akita_black_bowl_2)" not in source


def test_generator_maps_libero_mugs_to_same_class_assets() -> None:
    namespace = runpy.run_path(str(ROOT / "scripts" / "build_full_perturbation_dataset.py"))
    asset_for_type = namespace["asset_for_type"]

    assert asset_for_type("porcelain_mug") == ("libero/white_porcelain_mug", 1.0)
    assert asset_for_type("red_coffee_mug") == ("libero/porcelain_mug", 1.0)
    assert asset_for_type("white_yellow_mug") == ("libero/red_coffee_mug", 1.0)


def test_reviewed_dense_basket_d03_uses_compact_blocker() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = next(
        entry
        for entry in payload["tasks"]
        if entry["suite"] == "libero_10"
        and entry["base_task_id"] == 0
        and entry["case_id"] == "D03"
    )
    source = (ROOT / "assets" / entry["bddl_path"]).read_text(encoding="utf-8")

    assert "(:asset_id prl/fuze_bottle)" in source
    assert "(:asset_scale 0.70)" in source
    assert "(:allow_compact_asset true)" in source


def test_active_mug_replacement_cases_use_libero_mug_assets() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_by_task = {
        "LIVING_ROOM_SCENE5": "libero/white_porcelain_mug",
        "LIVING_ROOM_SCENE6": "libero/white_porcelain_mug",
    }
    entries = [
        entry
        for entry in payload["tasks"]
        if entry["suite"] == "libero_10"
        and entry["case_id"] in {"S06", "S11"}
        and any(marker in entry["bddl_path"] for marker in expected_by_task)
    ]

    assert len(entries) == 4
    for entry in entries:
        source = (ROOT / "assets" / entry["bddl_path"]).read_text(encoding="utf-8")
        expected_asset = next(
            asset_id
            for marker, asset_id in expected_by_task.items()
            if marker in entry["bddl_path"]
        )
        assert f"(:asset_id {expected_asset})" in source
        assert "(:asset_id prl/plastic_glass)" not in source
        assert "(:asset_scale 1.0)" in source


def test_asset_catalog_summary_and_local_paths_are_consistent() -> None:
    catalog = json.loads(ASSET_CATALOG.read_text(encoding="utf-8"))
    assets = catalog["assets"]
    summary = catalog["summary"]
    generated = [asset for asset in assets if asset["id"].startswith("generated/")]

    assert summary["ready_mjcf_assets"] == sum(
        asset["readiness"] == "ready_mjcf" for asset in assets
    )
    assert summary["generated_parametric_assets"] == len(generated)
    assert summary["external_adapted_assets"] == len(assets) - len(generated)
    assert {
        "libero/porcelain_mug",
        "libero/red_coffee_mug",
        "libero/white_porcelain_mug",
    } <= {asset["id"] for asset in assets}
    assert all((ASSET_ROOT / asset["path"]).is_file() for asset in assets)
