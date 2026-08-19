import json
from pathlib import Path

import pytest

from libero_remote.environment.task_manifest import TaskManifest

ASSETS_ROOT = Path(__file__).resolve().parents[1] / "assets"
MANIFEST_PATH = ASSETS_ROOT / "task_manifest.json"


def test_published_bddl_tree_excludes_legacy_perturbation_categories() -> None:
    bddl_root = ASSETS_ROOT / "bddl"
    directory_names = {path.name for path in bddl_root.iterdir() if path.is_dir()}
    legacy_prefixes = tuple(f"{index:02d}_" for index in range(1, 8))

    assert (bddl_root / "00_original").is_dir()
    assert (bddl_root / "libero-pro2.0-1680-v1").is_dir()
    assert not any(name.startswith(legacy_prefixes) for name in directory_names)


def test_published_manifest_contains_all_40_tasks_and_43_perturbations() -> None:
    manifest = TaskManifest.load(str(MANIFEST_PATH))

    assert manifest.version == "libero-pro2.0-1760-v1"
    assert len(manifest.entries) == 1760
    assert sum(entry["case_id"] == "BASE" for entry in manifest.entries) == 40
    assert sum(str(entry["case_id"]).startswith("S") for entry in manifest.entries) == 880
    assert sum(str(entry["case_id"]).startswith("D") for entry in manifest.entries) == 840
    assert {
        (entry["suite"], entry["base_task_id"])
        for entry in manifest.entries
        if entry["case_id"] == "BASE"
    } == {
        (suite, task_id)
        for suite in ("libero_spatial", "libero_object", "libero_goal", "libero_10")
        for task_id in range(10)
    }


def test_manifest_rejects_a_tampered_bddl(tmp_path: Path) -> None:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entry = dict(payload["tasks"][0])
    copied = tmp_path / "task.bddl"
    copied.write_bytes((ASSETS_ROOT / entry["bddl_path"]).read_bytes() + b"\n")
    entry["bddl_path"] = copied.name
    payload["tasks"] = [entry]
    payload["task_count"] = 1
    manifest_path = tmp_path / "task_manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="hash mismatch"):
        TaskManifest.load(str(manifest_path))


def test_manifest_accepts_a_crlf_checkout_of_a_published_bddl(tmp_path: Path) -> None:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entry = dict(payload["tasks"][0])
    source = ASSETS_ROOT / entry["bddl_path"]
    copied = tmp_path / "task.bddl"
    canonical = source.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    copied.write_bytes(canonical.replace(b"\n", b"\r\n"))
    entry["bddl_path"] = copied.name
    payload["tasks"] = [entry]
    payload["task_count"] = 1
    manifest_path = tmp_path / "task_manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    manifest = TaskManifest.load(str(manifest_path))

    assert manifest.require(entry["suite"], entry["base_task_id"], entry["case_id"])[
        "bddl_path"
    ] == copied.name
