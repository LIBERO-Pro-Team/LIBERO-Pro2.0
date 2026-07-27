"""Stable LIBERO-Pro Agent seam for user-provided model adapters."""

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Protocol, Tuple

import numpy as np

from libero_remote.protocol.models import PROTOCOL_VERSION

CANONICAL_CAMERA_KEYS: Tuple[str, ...] = (
    "agentview",
    "robot0_eye_in_hand",
)
CANONICAL_OBSERVATION_FIELDS: Tuple[str, ...] = (
    "robot0_eef_pos",
    "robot0_eef_quat_xyzw",
    "robot0_gripper_qpos",
)


@dataclass(frozen=True)
class AgentCapabilities:
    """The capabilities an adapter requires from the remote LIBERO service."""

    agent_name: str
    agent_version: str
    protocol_version: str = PROTOCOL_VERSION
    required_cameras: Tuple[str, ...] = CANONICAL_CAMERA_KEYS
    required_observation_fields: Tuple[str, ...] = CANONICAL_OBSERVATION_FIELDS
    control_mode: str = "relative"
    maximum_inference_seconds: float = 120.0


@dataclass(frozen=True)
class EpisodeContext:
    """Immutable context supplied to an adapter at episode reset."""

    suite: str
    task_id: int
    init_state_id: int
    seed: int
    max_steps: int
    instruction: str
    session_id: str
    episode_id: str


CanonicalObservation = Dict[str, Any]
CanonicalAction = np.ndarray


class LiberoProAgent(Protocol):
    """Minimal interface implemented by a user-side model adapter."""

    def describe(self) -> AgentCapabilities:
        """Return the server capabilities required by this adapter."""

    def reset(self, episode: EpisodeContext) -> None:
        """Clear model state before a new episode starts."""

    def act(self, observation: CanonicalObservation) -> CanonicalAction:
        """Map one canonical observation to one canonical action."""


@dataclass(frozen=True)
class AgentEpisodeResult:
    status: str
    agent_name: str
    agent_version: str
    suite: str
    task_id: int
    init_state_id: int
    seed: int
    session_id: str
    episode_id: str
    steps: int
    total_reward: float
    success: bool
    terminated: bool
    truncated: bool
    started_at: str
    duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "suite": self.suite,
            "task_id": self.task_id,
            "init_state_id": self.init_state_id,
            "seed": self.seed,
            "session_id": self.session_id,
            "episode_id": self.episode_id,
            "steps": self.steps,
            "total_reward": self.total_reward,
            "success": self.success,
            "terminated": self.terminated,
            "truncated": self.truncated,
            "started_at": self.started_at,
            "duration_seconds": self.duration_seconds,
        }


def validate_observation(
    observation: Mapping[str, Any], capabilities: AgentCapabilities
) -> None:
    """Reject missing canonical fields before a model sees an episode."""

    missing_fields = [
        key for key in capabilities.required_observation_fields if key not in observation
    ]
    missing_cameras = [
        f"{camera}_image"
        for camera in capabilities.required_cameras
        if f"{camera}_image" not in observation
    ]
    missing = missing_fields + missing_cameras
    if missing:
        raise ValueError(
            "Agent requires observation fields that the server did not provide: "
            f"{missing}"
        )


def validate_action_schema(
    action_schema: Mapping[str, Any], capabilities: AgentCapabilities
) -> None:
    """Validate server action semantics against the adapter declaration."""

    if action_schema.get("control_mode") != capabilities.control_mode:
        raise RuntimeError(
            "Remote action control mode does not match Agent capabilities: "
            f"agent={capabilities.control_mode!r}, server={action_schema.get('control_mode')!r}"
        )
    if list(action_schema.get("shape", [])) != [7]:
        raise RuntimeError(
            "LIBERO-Pro V1 Agent adapters require a 7D action; "
            f"server advertised {action_schema.get('shape')!r}"
        )
    expected = {
        "rotation_representation": "axis_angle",
        "translation_frame": "world",
        "rotation_frame": "world",
    }
    mismatches = {
        key: (expected_value, action_schema.get(key))
        for key, expected_value in expected.items()
        if action_schema.get(key) != expected_value
    }
    if mismatches:
        raise RuntimeError(f"Remote action schema is incompatible with LIBERO-Pro V1: {mismatches}")


def validate_action(action: Any, action_schema: Mapping[str, Any]) -> np.ndarray:
    """Validate and normalize a user adapter's canonical action."""

    array = np.ascontiguousarray(action, dtype=np.float32)
    shape = tuple(int(value) for value in action_schema.get("shape", [7]))
    if array.shape != shape:
        raise ValueError(f"Agent must return action shape {shape}, got {array.shape}")
    if not np.isfinite(array).all():
        raise ValueError("Agent action must contain only finite values")
    low = np.asarray(action_schema.get("low", [-np.inf] * len(array)), dtype=np.float32)
    high = np.asarray(action_schema.get("high", [np.inf] * len(array)), dtype=np.float32)
    if np.any(array < low) or np.any(array > high):
        raise ValueError(
            f"Agent action is outside server bounds: action={array}, low={low}, high={high}"
        )
    return array


def run_remote_agent_episode(env: Any, agent: LiberoProAgent, spec: Any) -> AgentEpisodeResult:
    """Run one canonical Agent episode and always close its remote session."""

    capabilities = agent.describe()
    if capabilities.protocol_version != PROTOCOL_VERSION:
        raise RuntimeError(
            f"Agent protocol {capabilities.protocol_version!r} is not supported; "
            f"expected {PROTOCOL_VERSION!r}"
        )
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    steps = 0
    total_reward = 0.0
    success = False
    terminated = False
    truncated = False
    try:
        observation, reset_info = env.reset(
            suite=spec.suite,
            task_id=spec.task_id,
            init_state_id=spec.init_state_id,
            seed=spec.seed,
            camera_height=spec.camera_height,
            camera_width=spec.camera_width,
            max_steps=spec.max_steps,
            control_mode=capabilities.control_mode,
            variant=spec.variant,
        )
        action_schema = reset_info.get("action_schema", {})
        validate_action_schema(action_schema, capabilities)
        instruction = str(reset_info["language_instruction"])
        episode = EpisodeContext(
            suite=spec.suite,
            task_id=spec.task_id,
            init_state_id=spec.init_state_id,
            seed=spec.seed,
            max_steps=spec.max_steps,
            instruction=instruction,
            session_id=str(reset_info.get("session_id", "")),
            episode_id=str(reset_info.get("episode_id", "")),
        )
        agent.reset(episode)
        while steps < spec.max_steps:
            canonical_observation = dict(observation)
            canonical_observation["instruction"] = instruction
            canonical_observation["step_index"] = steps
            validate_observation(canonical_observation, capabilities)
            action = validate_action(agent.act(canonical_observation), action_schema)
            observation, reward, terminated, truncated, step_info = env.step(action)
            steps += 1
            total_reward += float(reward)
            success = success or bool(step_info.get("success", False))
            if success or terminated or truncated:
                break
        return AgentEpisodeResult(
            status="completed",
            agent_name=capabilities.agent_name,
            agent_version=capabilities.agent_version,
            suite=spec.suite,
            task_id=spec.task_id,
            init_state_id=spec.init_state_id,
            seed=spec.seed,
            session_id=episode.session_id,
            episode_id=episode.episode_id,
            steps=steps,
            total_reward=total_reward,
            success=success,
            terminated=terminated,
            truncated=truncated,
            started_at=started_at,
            duration_seconds=time.perf_counter() - started,
        )
    finally:
        env.close()
