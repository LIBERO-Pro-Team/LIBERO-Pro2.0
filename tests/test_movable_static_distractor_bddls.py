import hashlib
import json
import re
from pathlib import Path

from scripts import apply_goal_review_finalization as finalizer


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
def _case_block(text: str, case_id: str) -> str:
    match = re.search(rf"(?m)^[ \t]*\({re.escape(case_id)}[ \t]*$", text)
    assert match is not None
    return text[match.start() : finalizer.group_end(text, match.start())]


def test_finalizer_opts_all_static_object_distractors_into_physics() -> None:
    for suite in finalizer.SUITES:
        for task_id in range(10):
            for case_id in ("S10", "S11"):
                params, _ = finalizer.case_updates(suite, task_id, case_id)
                assert params["clear_of_task_entities"] == ("true",)
                assert params["movable_asset"] == ("true",)
                assert params["physical_collision"] == ("true",)
                assert params["visual_only_asset"] == ("false",)
                assert params.get("weld_asset_joints") != ("true",)
                if case_id == "S10":
                    assert params["asset_contact_margin_m"] == ("0.006",)


def test_published_static_object_distractors_are_physical_and_hashed() -> None:
    manifest = json.loads((ASSETS / "task_manifest.json").read_text(encoding="utf-8"))
    entries = [
        item for item in manifest["tasks"] if item["case_id"] in {"S10", "S11"}
    ]

    assert len(entries) == 80
    for item in entries:
        path = ASSETS / item["bddl_path"]
        text = path.read_text(encoding="utf-8")
        block = _case_block(text, item["case_id"])
        assert "(:clear_of_task_entities true)" in block, path
        assert "(:movable_asset true)" in block, path
        assert "(:physical_collision true)" in block, path
        assert "(:visual_only_asset false)" in block, path
        assert "(:weld_asset_joints true)" not in block, path
        if item["case_id"] == "S10":
            assert "(:asset_contact_margin_m 0.006)" in block, path
        digest = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        ).hexdigest()
        assert item["bddl_sha256"] == digest, path
