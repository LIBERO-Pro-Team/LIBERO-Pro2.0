from pathlib import Path

import numpy as np

from libero_remote.runner.scheduled import AgentContext
from scripts import run_generic_xvla_scheduled as script


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
        events.append(
            ("load", model_path, device, tokenizer_path, local_files_only)
        )
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
