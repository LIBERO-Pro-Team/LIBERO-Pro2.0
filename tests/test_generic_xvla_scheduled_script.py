import json
from pathlib import Path

import numpy as np
import pytest

from libero_remote.runner.scheduled import AgentContext
from scripts import run_generic_xvla_scheduled as script

MANIFEST = Path(__file__).resolve().parents[1] / "assets" / "task_manifest.json"


def test_generic_runner_supports_extended_legacy_and_new_case_selections() -> None:
    extended = script._episodes_from_manifest(MANIFEST, 142, 256)
    legacy = script._episodes_from_manifest(MANIFEST, 142, 256, task_profile="legacy-1680")
    new_cases = script._episodes_from_manifest(MANIFEST, 142, 256, case_ids=["S22", "D20"])

    assert len(extended) == 1760
    assert len(legacy) == 1680
    assert len(new_cases) == 80
    assert {episode["variant"] for episode in new_cases} == {"S22", "D20"}


def test_generic_runner_accepts_a_self_consistent_legacy_manifest(tmp_path: Path) -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload["tasks"] = [
        entry for entry in payload["tasks"] if entry["case_id"] not in {"S22", "D20"}
    ]
    payload["task_count"] = len(payload["tasks"])
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    episodes = script._episodes_from_manifest(path, 142, 256)

    assert len(episodes) == 1680


def test_generic_runner_validates_selected_tasks_instead_of_release_count() -> None:
    episodes = [
        {
            "suite": "libero_goal",
            "task_id": 0,
            "variant": "S22",
        }
    ]
    catalog = {
        "task_count": 1,
        "tasks": [
            {
                "suite": "libero_goal",
                "task_id": 0,
                "case_id": "S22",
            }
        ],
    }

    script._validate_server_catalog(catalog, episodes)

    catalog["tasks"][0]["case_id"] = "BASE"
    with pytest.raises(RuntimeError, match="does not publish 1 selected tasks"):
        script._validate_server_catalog(catalog, episodes)


def test_generic_runner_rejects_an_inconsistent_manifest(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"task_count": 2, "tasks": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="task_count"):
        script._episodes_from_manifest(path, 142, 256)


def test_generic_runner_writes_distinct_task_and_init_state_results(tmp_path: Path) -> None:
    records = {
        "episodes": [
            {
                "spec": {
                    "suite": "libero_goal",
                    "task_id": task_id,
                    "init_state_id": init_state_id,
                    "variant": "S22",
                    "seed": 142,
                },
                "result": {"success": True},
            }
            for task_id, init_state_id in ((0, 0), (1, 0), (1, 1))
        ]
    }

    script._write_server_results(tmp_path, records)

    assert (
        tmp_path / "libero_goal" / "task_00" / "S22" / "init_000" / "seed_142" / "result.json"
    ).is_file()
    assert (
        tmp_path / "libero_goal" / "task_01" / "S22" / "init_000" / "seed_142" / "result.json"
    ).is_file()
    assert (
        tmp_path / "libero_goal" / "task_01" / "S22" / "init_001" / "seed_142" / "result.json"
    ).is_file()


def test_generic_xvla_script_composes_reference_adapter_with_generic_recorder(
    tmp_path: Path, monkeypatch
) -> None:
    events = []

    class FakeXVLAAdapter:
        def reset(self, context: AgentContext) -> None:
            events.append(("model_reset", context))

        def act(self, observation):
            events.append(("model_act", observation))
            return np.array([0.25, -0.5], dtype=np.float32)

        def close(self) -> None:
            events.append(("model_close", None))

    class FakeRecorder:
        def __init__(self, output_root, image_field, fps) -> None:
            events.append(("recorder_init", output_root, image_field, fps))

        def reset(self, context: AgentContext) -> None:
            events.append(("recorder_reset", context))

        def record(self, observation) -> None:
            events.append(("record", observation))

        def close(self) -> None:
            events.append(("recorder_close", None))

    model = FakeXVLAAdapter()

    def load(model_path, device, tokenizer_path, local_files_only):
        events.append(("load", model_path, device, tokenizer_path, local_files_only))
        return model

    monkeypatch.setattr(script.XVLAPolicyAdapter, "load", load)
    monkeypatch.setattr(script, "RolloutVideoRecorder", FakeRecorder)
    adapter = script._load_policy(
        tmp_path / "model",
        tmp_path / "tokenizer",
        "cuda",
        output_root=tmp_path / "output",
        fps=12,
    )
    context = AgentContext(
        run_id="run-test",
        job_id="job-test",
        job_index=0,
        episode_spec={"suite": "libero_goal", "task_id": 0, "seed": 142},
        reproducibility={"job_fingerprint": "job-hash"},
        language_instruction="put the bowl on the plate",
        action_schema={"shape": [2], "low": [-1.0, -1.0], "high": [1.0, 1.0]},
        observation_schema_version="libero_standard_v1",
    )
    observation = {
        "agentview_image": np.zeros((4, 5, 3), dtype=np.uint8),
        "instruction": context.language_instruction,
        "step_index": 0,
    }

    adapter.reset(context)
    action = adapter.act(observation)
    adapter.close()

    np.testing.assert_array_equal(action, np.array([0.25, -0.5], dtype=np.float32))
    assert events[0] == (
        "load",
        str((tmp_path / "model").resolve()),
        "cuda",
        str((tmp_path / "tokenizer").resolve()),
        True,
    )
    assert events[1] == ("recorder_init", tmp_path / "output", "agentview_image", 12)
    assert events[2] == ("recorder_reset", context)
    assert events[3] == ("model_reset", context)
    assert events[4] == ("record", observation)
    assert events[5] == ("model_act", observation)
    assert events[-2:] == [("recorder_close", None), ("model_close", None)]
