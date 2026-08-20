import json
import sys
from types import SimpleNamespace

import numpy as np

from libero_remote.runner.recording import RecordingAgentAdapter, RolloutVideoRecorder
from libero_remote.runner.scheduled import AgentContext


class _PrivateModelAdapter:
    def __init__(self) -> None:
        self.context = None
        self.observation = None
        self.closed = False

    def reset(self, context: AgentContext) -> None:
        self.context = context

    def act(self, observation):
        self.observation = observation
        return np.array([0.25, -0.5], dtype=np.float32)

    def close(self) -> None:
        self.closed = True


class _ObservationRecorder:
    def __init__(self) -> None:
        self.context = None
        self.observation = None
        self.closed = False

    def reset(self, context: AgentContext) -> None:
        self.context = context

    def record(self, observation) -> None:
        self.observation = observation

    def close(self) -> None:
        self.closed = True


def test_recording_adapter_preserves_model_neutral_observation() -> None:
    model = _PrivateModelAdapter()
    recorder = _ObservationRecorder()
    adapter = RecordingAgentAdapter(model, recorder)
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
        "private_state": np.array([1.0, 2.0], dtype=np.float32),
        "instruction": context.language_instruction,
        "step_index": 0,
    }

    adapter.reset(context)
    action = adapter.act(observation)
    adapter.close()

    assert model.context is context
    assert recorder.context is context
    assert model.observation is observation
    assert recorder.observation is observation
    assert "pixels" not in observation
    assert "robot_state" not in observation
    assert "domain_id" not in observation
    np.testing.assert_array_equal(action, np.array([0.25, -0.5], dtype=np.float32))
    assert model.closed is True
    assert recorder.closed is True


def test_rollout_recorder_writes_model_neutral_episode_artifacts(tmp_path, monkeypatch) -> None:
    writers = []

    class FakeWriter:
        def __init__(self, path, fourcc, fps, size) -> None:
            self.path = path
            self.fourcc = fourcc
            self.fps = fps
            self.size = size
            self.frames = []
            self.released = False

        def isOpened(self) -> bool:
            return True

        def write(self, frame) -> None:
            self.frames.append(frame.copy())

        def release(self) -> None:
            self.released = True

    def video_writer(path, fourcc, fps, size):
        writer = FakeWriter(path, fourcc, fps, size)
        writers.append(writer)
        return writer

    fake_cv2 = SimpleNamespace(
        COLOR_RGB2BGR=1,
        VideoWriter=video_writer,
        VideoWriter_fourcc=lambda *codec: "".join(codec),
        cvtColor=lambda frame, code: frame[..., ::-1],
        imwrite=lambda path, frame: True,
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    context = AgentContext(
        run_id="run-test",
        job_id="job-test",
        job_index=3,
        episode_spec={
            "suite": "libero_goal",
            "task_id": 2,
            "seed": 142,
            "variant": "D03",
        },
        reproducibility={"job_fingerprint": "job-hash"},
        language_instruction="put the bowl on the plate",
        action_schema={"shape": [2], "low": [-1.0, -1.0], "high": [1.0, 1.0]},
        observation_schema_version="libero_standard_v1",
    )
    recorder = RolloutVideoRecorder(
        output_root=tmp_path,
        image_field="custom_camera_image",
        fps=12,
    )
    frame = np.arange(4 * 5 * 3, dtype=np.uint8).reshape(4, 5, 3)

    recorder.reset(context)
    recorder.record({"custom_camera_image": frame})
    recorder.close()

    episode_dir = tmp_path / "libero_goal" / "task_02" / "D03" / "init_000" / "seed_142"
    metadata = json.loads((episode_dir / "adapter.json").read_text(encoding="utf-8"))
    assert len(writers) == 1
    assert writers[0].size == (5, 4)
    assert writers[0].fps == 12
    assert len(writers[0].frames) == 2
    assert writers[0].released is True
    assert metadata["frame_count_before_terminal_duplicate"] == 1
    assert metadata["recorded_observation_field"] == "custom_camera_image"
    assert "xvla" not in json.dumps(metadata).lower()
