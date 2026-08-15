from contextlib import nullcontext

import numpy as np

from libero_remote.runner.agent import EpisodeContext
from libero_remote.runner.pi0 import Pi0PolicyAdapter, to_lerobot_pi0_observation


def _observation() -> dict:
    agentview = np.arange(4 * 5 * 3, dtype=np.uint8).reshape(4, 5, 3)
    eye_in_hand = np.flip(agentview, axis=0).copy()
    return {
        "agentview_image": agentview,
        "robot0_eye_in_hand_image": eye_in_hand,
        "robot0_eef_pos": np.array([0.1, 0.2, 0.3], dtype=np.float32),
        "robot0_eef_quat_xyzw": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        "robot0_gripper_qpos": np.array([-0.01, 0.01], dtype=np.float32),
        "instruction": "pick up the bowl",
    }


def test_pi0_observation_mapping_uses_only_standard_server_fields() -> None:
    source = _observation()

    mapped = to_lerobot_pi0_observation(source)

    np.testing.assert_array_equal(mapped["pixels"]["image"], source["agentview_image"])
    np.testing.assert_array_equal(
        mapped["pixels"]["image2"], source["robot0_eye_in_hand_image"]
    )
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
    assert "mat" not in mapped["robot_state"]["eef"]


def test_pi0_adapter_uses_official_processing_order_and_unbatches_action() -> None:
    events = []

    class Policy:
        def select_action(self, observation):
            events.append("policy")
            assert observation == {"policy_input": True}
            return "model_action"

    def preprocess_observation(raw):
        events.append("preprocess_observation")
        assert "pixels" in raw
        return {"raw": True}

    def env_preprocessor(observation):
        events.append("env_preprocessor")
        assert observation["task"] == "pick up the bowl"
        return {"env_input": True}

    def policy_preprocessor(observation):
        events.append("policy_preprocessor")
        assert observation == {"env_input": True}
        return {"policy_input": True}

    def policy_postprocessor(action):
        events.append("policy_postprocessor")
        assert action == "model_action"
        return np.arange(7, dtype=np.float32)[None, :]

    adapter = Pi0PolicyAdapter(
        policy=Policy(),
        preprocess_observation=preprocess_observation,
        env_preprocessor=env_preprocessor,
        policy_preprocessor=policy_preprocessor,
        policy_postprocessor=policy_postprocessor,
        inference_context=nullcontext,
    )

    action = adapter.act(_observation())

    np.testing.assert_array_equal(
        action,
        np.clip(np.arange(7, dtype=np.float32), -1.0, 1.0),
    )
    assert events == [
        "preprocess_observation",
        "env_preprocessor",
        "policy_preprocessor",
        "policy",
        "policy_postprocessor",
    ]


def test_pi0_adapter_clips_postprocessed_action_to_libero_bounds() -> None:
    class Policy:
        def select_action(self, observation):
            del observation
            return "model_action"

    adapter = Pi0PolicyAdapter(
        policy=Policy(),
        preprocess_observation=lambda raw: raw,
        env_preprocessor=lambda observation: observation,
        policy_preprocessor=lambda observation: observation,
        policy_postprocessor=lambda action: np.array(
            [[-1.0000278, -1.0111661, -1.0228710, 0.0, 0.25, 0.5, 1.00001]],
            dtype=np.float32,
        ),
        inference_context=nullcontext,
    )

    action = adapter.act(_observation())

    np.testing.assert_array_equal(
        action,
        np.array([-1.0, -1.0, -1.0, 0.0, 0.25, 0.5, 1.0], dtype=np.float32),
    )


def test_pi0_adapter_declares_platform_v1_relative_capabilities() -> None:
    adapter = Pi0PolicyAdapter(None, None, None, None, None, nullcontext)

    capabilities = adapter.describe()

    assert capabilities.agent_name == "pi0"
    assert capabilities.protocol_version == "1.0"
    assert capabilities.control_mode == "relative"
    assert capabilities.required_cameras == ("agentview", "robot0_eye_in_hand")
    assert capabilities.required_observation_fields == (
        "robot0_eef_pos",
        "robot0_eef_quat_xyzw",
        "robot0_gripper_qpos",
    )


def test_pi0_adapter_resets_checkpoint_action_queue_for_each_episode() -> None:
    class Policy:
        def __init__(self) -> None:
            self.reset_calls = 0

        def reset(self) -> None:
            self.reset_calls += 1

    policy = Policy()
    adapter = Pi0PolicyAdapter(policy, None, None, None, None, nullcontext)
    episode = EpisodeContext(
        suite="libero_spatial",
        task_id=8,
        init_state_id=0,
        seed=142,
        max_steps=500,
        instruction="pick up the bowl",
        session_id="ses_pi0",
        episode_id="ep_pi0",
    )

    adapter.reset(episode)
    adapter.reset(episode)

    assert policy.reset_calls == 2
