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
                assert ("zero_initial_asset_velocity" in params) == (
                    suite == "libero_goal" and case_id == "S10"
                )
                if case_id == "S10":
                    assert params["asset_contact_margin_m"] == (
                        "0.001" if suite == "libero_goal" else "0.006",
                    )


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
        assert ("(:zero_initial_asset_velocity true)" in block) == (
            item["suite"] == "libero_goal" and item["case_id"] == "S10"
        )
        assert "(:physical_collision true)" in block, path
        assert "(:visual_only_asset false)" in block, path
        assert "(:weld_asset_joints true)" not in block, path
        if item["case_id"] == "S10":
            margin = "0.001" if item["suite"] == "libero_goal" else "0.006"
            assert f"(:asset_contact_margin_m {margin})" in block, path
        digest = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        ).hexdigest()
        assert item["bddl_sha256"] == digest, path


def test_stable_collision_and_velocity_fields_are_exclusive_to_goal_s10():
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location("_s10_scope_parser", ROOT / "simulator-source/libero/libero/envs/perturbation_config.py")
    parser = module_from_spec(spec)
    spec.loader.exec_module(parser)
    manifest = json.loads((ASSETS / "task_manifest.json").read_text(encoding="utf-8"))
    configured = set()
    for item in manifest["tasks"]:
        config = parser.parse_bddl_perturbation_config(ASSETS / item["bddl_path"])
        for entry in config.get("perturbations", []):
            for field in entry[1:]:
                params = field.get("params", {})
                if "asset_collision_box_half_size" in params or "zero_initial_asset_velocity" in params:
                    assert str(entry[0]).upper() == item["case_id"]
                    assert params["zero_initial_asset_velocity"] is True
                    assert params["asset_collision_box_half_size"] == [0.03861756, 0.045803085, 0.02738214]
                    configured.add((item["suite"], int(item["base_task_id"]), item["case_id"]))
    assert configured == {("libero_goal", task, "S10") for task in range(10)}
