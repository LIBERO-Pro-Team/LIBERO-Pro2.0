import json
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pytest

from libero_remote.runner.xvla import (
    EpisodeResult,
    EpisodeSpec,
    XVLAPolicyAdapter,
    append_episode_result,
    run_remote_episode,
    to_lerobot_libero_observation,
)


def test_remote_observation_is_mapped_to_xvla_libero_input() -> None:
    agentview = np.arange(4 * 5 * 3, dtype=np.uint8).reshape(4, 5, 3)
    wrist = np.full((4, 5, 3), 17, dtype=np.uint8)
    observation = {
        "agentview_image": agentview,
        "robot0_eye_in_hand_image": wrist,
        "robot0_eef_pos": np.array([0.1, 0.2, 0.3], dtype=np.float32),
        "robot0_eef_quat_xyzw": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        "robot0_gripper_qpos": np.array([-0.01, 0.01], dtype=np.float32),
    }

    mapped = to_lerobot_libero_observation(observation)

    np.testing.assert_array_equal(mapped["pixels"]["image"], agentview)
    np.testing.assert_array_equal(mapped["pixels"]["image2"], wrist)
    np.testing.assert_array_equal(
        mapped["robot_state"]["eef"]["pos"],
        np.array([[0.1, 0.2, 0.3]], dtype=np.float32),
    )
    np.testing.assert_array_equal(
        mapped["robot_state"]["eef"]["quat"],
        np.array([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32),
    )
    np.testing.assert_array_equal(
        mapped["robot_state"]["gripper"]["qpos"],
        np.array([[-0.01, 0.01]], dtype=np.float32),
    )


class _FakePolicy:
    def __init__(self) -> None:
        self.reset_calls = 0
        self.instructions = []

    def reset(self) -> None:
        self.reset_calls += 1

    def select_action(self, observation, instruction: str) -> np.ndarray:
        del observation
        self.instructions.append(instruction)
        return np.full(7, 0.25, dtype=np.float32)


class _FakeRemoteEnv:
    def __init__(self) -> None:
        self.reset_options = None
        self.actions = []
        self.closed = False

    def reset(self, **options):
        self.reset_options = options
        return {"frame": np.array([0], dtype=np.float32)}, {
            "session_id": "ses_test",
            "episode_id": "ep_test",
            "language_instruction": "put the bowl on the plate",
            "action_schema": {"control_mode": "absolute"},
        }

    def step(self, action: np.ndarray):
        self.actions.append(action.copy())
        success = len(self.actions) == 2
        return (
            {"frame": np.array([len(self.actions)], dtype=np.float32)},
            1.0 if success else 0.0,
            success,
            False,
            {"success": success, "step_index": len(self.actions) - 1},
        )

    def close(self) -> None:
        self.closed = True


def test_remote_episode_runs_until_success_and_closes_session() -> None:
    env = _FakeRemoteEnv()
    policy = _FakePolicy()
    spec = EpisodeSpec(
        suite="libero_goal",
        task_id=3,
        init_state_id=4,
        seed=11,
        max_steps=20,
    )

    result = run_remote_episode(env, policy, spec)

    assert env.reset_options == {
        "suite": "libero_goal",
        "task_id": 3,
        "init_state_id": 4,
        "seed": 11,
        "camera_height": 256,
        "camera_width": 256,
        "max_steps": 20,
        "control_mode": "absolute",
    }
    assert len(env.actions) == 2
    assert policy.reset_calls == 1
    assert policy.instructions == [
        "put the bowl on the plate",
        "put the bowl on the plate",
    ]
    assert result.status == "completed"
    assert result.success
    assert result.terminated
    assert not result.truncated
    assert result.steps == 2
    assert result.total_reward == 1.0
    assert result.session_id == "ses_test"
    assert result.episode_id == "ep_test"
    assert env.closed


def test_remote_episode_rejects_invalid_policy_action_and_still_closes() -> None:
    class InvalidPolicy(_FakePolicy):
        def select_action(self, observation, instruction: str) -> np.ndarray:
            del observation, instruction
            return np.zeros(6, dtype=np.float32)

    env = _FakeRemoteEnv()
    spec = EpisodeSpec("libero_goal", 0, 0, 42, 10)

    with pytest.raises(ValueError, match="7 values"):
        run_remote_episode(env, InvalidPolicy(), spec)

    assert env.actions == []
    assert env.closed


def test_episode_results_are_appended_as_json_lines(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "results.jsonl"
    first = EpisodeResult(
        status="completed",
        suite="libero_goal",
        task_id=0,
        init_state_id=0,
        seed=42,
        session_id="ses_1",
        episode_id="ep_1",
        steps=3,
        total_reward=1.0,
        success=True,
        terminated=True,
        truncated=False,
        started_at="2026-07-25T00:00:00+00:00",
        duration_seconds=1.5,
    )
    second = EpisodeResult(**{**first.to_dict(), "episode_id": "ep_2"})

    append_episode_result(output, first)
    append_episode_result(output, second)

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [record["episode_id"] for record in records] == ["ep_1", "ep_2"]
    assert records[0]["success"] is True


def test_xvla_adapter_uses_lerobot_processing_order() -> None:
    events = []

    class Policy:
        def reset(self) -> None:
            events.append("reset")

        def select_action(self, observation):
            events.append("policy")
            assert observation == {"policy_input": True}
            return "policy_action"

    def preprocess(raw):
        events.append("preprocess_observation")
        assert "pixels" in raw
        return {"raw": True}

    def env_preprocess(observation):
        events.append("env_preprocessor")
        assert observation["task"] == ["pick up the bowl"]
        return {"env_input": True}

    def policy_preprocess(observation):
        events.append("policy_preprocessor")
        assert observation == {"env_input": True}
        return {"policy_input": True}

    def policy_postprocess(action):
        events.append("policy_postprocessor")
        assert action == "policy_action"
        return "postprocessed_action"

    def env_postprocess(transition):
        events.append("env_postprocessor")
        assert transition == {"action": "postprocessed_action"}
        return {"action": np.arange(7, dtype=np.float32)[None, :]}

    adapter = XVLAPolicyAdapter(
        policy=Policy(),
        preprocess_observation=preprocess,
        env_preprocessor=env_preprocess,
        policy_preprocessor=policy_preprocess,
        policy_postprocessor=policy_postprocess,
        env_postprocessor=env_postprocess,
        inference_context=nullcontext,
    )

    adapter.reset()
    action = adapter.select_action(_xvla_observation(), "pick up the bowl")

    np.testing.assert_array_equal(action, np.arange(7, dtype=np.float32))
    assert events == [
        "reset",
        "preprocess_observation",
        "env_preprocessor",
        "policy_preprocessor",
        "policy",
        "policy_postprocessor",
        "env_postprocessor",
    ]


def _xvla_observation():
    return {
        "agentview_image": np.zeros((4, 5, 3), dtype=np.uint8),
        "robot0_eye_in_hand_image": np.zeros((4, 5, 3), dtype=np.uint8),
        "robot0_eef_pos": np.zeros(3, dtype=np.float32),
        "robot0_eef_quat_xyzw": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        "robot0_gripper_qpos": np.zeros(2, dtype=np.float32),
    }
