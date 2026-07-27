import numpy as np
import pytest

from libero_remote.runner.agent import (
    AgentCapabilities,
    EpisodeContext,
    run_remote_agent_episode,
)
from libero_remote.runner.xvla import EpisodeSpec

ACTION_SCHEMA = {
    "control_mode": "relative",
    "shape": [7],
    "low": [-1.0] * 7,
    "high": [1.0] * 7,
    "rotation_representation": "axis_angle",
    "translation_frame": "world",
    "rotation_frame": "world",
}


def _canonical_observation() -> dict:
    return {
        "agentview_image": np.zeros((8, 8, 3), dtype=np.uint8),
        "robot0_eye_in_hand_image": np.zeros((8, 8, 3), dtype=np.uint8),
        "robot0_eef_pos": np.zeros(3, dtype=np.float32),
        "robot0_eef_quat_xyzw": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        "robot0_gripper_qpos": np.zeros(2, dtype=np.float32),
    }


class _Agent:
    def __init__(self) -> None:
        self.context = None
        self.observations = []

    def describe(self) -> AgentCapabilities:
        return AgentCapabilities(agent_name="test-agent", agent_version="1.0")

    def reset(self, episode: EpisodeContext) -> None:
        self.context = episode

    def act(self, observation: dict) -> np.ndarray:
        self.observations.append(observation)
        return np.zeros(7, dtype=np.float32)


class _RemoteEnv:
    def __init__(self) -> None:
        self.actions = []
        self.closed = False
        self.reset_options = None

    def reset(self, **options):
        self.reset_options = options
        return _canonical_observation(), {
            "session_id": "ses_agent",
            "episode_id": "ep_agent",
            "language_instruction": "pick up the bowl",
            "action_schema": ACTION_SCHEMA,
        }

    def step(self, action: np.ndarray):
        self.actions.append(action.copy())
        success = len(self.actions) == 2
        return _canonical_observation(), float(success), success, False, {"success": success}

    def close(self) -> None:
        self.closed = True


def test_agent_episode_uses_declared_relative_schema_and_closes_session() -> None:
    env = _RemoteEnv()
    agent = _Agent()
    spec = EpisodeSpec("libero_spatial", 8, 0, 142, 500)

    result = run_remote_agent_episode(env, agent, spec)

    assert env.reset_options["control_mode"] == "relative"
    assert env.reset_options["max_steps"] == 500
    assert len(env.actions) == 2
    assert agent.context.instruction == "pick up the bowl"
    assert agent.observations[0]["instruction"] == "pick up the bowl"
    assert agent.observations[0]["step_index"] == 0
    assert result.success
    assert result.steps == 2
    assert result.session_id == "ses_agent"
    assert env.closed


def test_agent_episode_rejects_missing_canonical_field_and_closes_session() -> None:
    class MissingFieldEnv(_RemoteEnv):
        def reset(self, **options):
            observation, info = super().reset(**options)
            del observation["robot0_eef_pos"]
            return observation, info

    env = MissingFieldEnv()
    agent = _Agent()

    with pytest.raises(ValueError, match="robot0_eef_pos"):
        run_remote_agent_episode(
            env,
            agent,
            EpisodeSpec("libero_spatial", 8, 0, 142, 500),
        )

    assert agent.observations == []
    assert env.actions == []
    assert env.closed


@pytest.mark.parametrize(
    ("action", "message"),
    [
        (np.zeros(6, dtype=np.float32), "shape"),
        (np.full(7, 1.5, dtype=np.float32), "outside server bounds"),
    ],
)
def test_agent_episode_rejects_invalid_action_and_closes_session(
    action: np.ndarray, message: str
) -> None:
    class InvalidActionAgent(_Agent):
        def act(self, observation: dict) -> np.ndarray:
            del observation
            return action

    env = _RemoteEnv()

    with pytest.raises(ValueError, match=message):
        run_remote_agent_episode(
            env,
            InvalidActionAgent(),
            EpisodeSpec("libero_spatial", 8, 0, 142, 500),
        )

    assert env.actions == []
    assert env.closed
