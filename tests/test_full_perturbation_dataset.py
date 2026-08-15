import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"


def test_full_manifest_covers_40_base_tasks_and_41_active_cases() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = payload["tasks"]

    assert payload["manifest_version"] == "libero-pro2.0-1680-v1"
    assert payload["task_count"] == len(entries) == 1680
    assert len({(entry["suite"], entry["base_task_id"]) for entry in entries}) == 40
    assert {entry["case_id"] for entry in entries} == {
        "BASE",
        *(f"S{i:02d}" for i in range(1, 22)),
        *(f"D{i:02d}" for i in range(1, 20)),
        "D21",
    }
    assert all(
        entry["bddl_path"].startswith("bddl/libero-pro2.0-1680-v1/")
        for entry in entries
    )
