"""xVLA inference helpers for a remote LIBERO environment."""

import json
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterator

import numpy as np

REPORT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class EpisodeSpec:
    suite: str
    task_id: int
    init_state_id: int
    seed: int
    max_steps: int
    camera_height: int = 256
    camera_width: int = 256
    control_mode: str = "absolute"


@dataclass(frozen=True)
class EpisodeResult:
    status: str
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
        return asdict(self)


@dataclass(frozen=True)
class RunManifest:
    created_at: str
    protocol_version: str
    server: Dict[str, Any]
    client: Dict[str, Any]
    model: Dict[str, Any]
    evaluation: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class XVLAPolicyAdapter:
    """Keep LeRobot's xVLA preprocessing and action conversion behind one call."""

    def __init__(
        self,
        policy: Any,
        preprocess_observation: Callable[[Dict[str, Any]], Dict[str, Any]],
        env_preprocessor: Callable[[Dict[str, Any]], Dict[str, Any]],
        policy_preprocessor: Callable[[Dict[str, Any]], Dict[str, Any]],
        policy_postprocessor: Callable[[Any], Any],
        env_postprocessor: Callable[[Dict[str, Any]], Dict[str, Any]],
        inference_context: Callable[[], Any],
        action_key: str = "action",
    ) -> None:
        self._policy = policy
        self._preprocess_observation = preprocess_observation
        self._env_preprocessor = env_preprocessor
        self._policy_preprocessor = policy_preprocessor
        self._policy_postprocessor = policy_postprocessor
        self._env_postprocessor = env_postprocessor
        self._inference_context = inference_context
        self._action_key = action_key

    @classmethod
    def load(
        cls,
        model_path: str,
        device: str = "cuda",
        tokenizer_path: str = "",
    ) -> "XVLAPolicyAdapter":
        """Load xVLA and its official LeRobot processors only when requested."""

        import torch
        from lerobot.envs import preprocess_observation
        from lerobot.policies import make_pre_post_processors
        from lerobot.policies.xvla.modeling_xvla import XVLAPolicy
        from lerobot.policies.xvla.processor_xvla import (
            XVLARotation6DToAxisAngleProcessorStep,
        )
        from lerobot.processor import PolicyProcessorPipeline
        from lerobot.processor.env_processor import LiberoProcessorStep
        from lerobot.utils.constants import ACTION

        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but PyTorch cannot access a CUDA device")

        policy = XVLAPolicy.from_pretrained(model_path)
        policy.config.device = device
        policy.to(device)
        policy.eval()

        preprocessor_overrides = {"device_processor": {"device": device}}
        resolved_tokenizer = _resolve_tokenizer_path(model_path, tokenizer_path)
        if resolved_tokenizer:
            preprocessor_overrides["tokenizer_processor"] = {
                "tokenizer_name": resolved_tokenizer
            }

        policy_preprocessor, policy_postprocessor = make_pre_post_processors(
            policy_cfg=policy.config,
            pretrained_path=model_path,
            preprocessor_overrides=preprocessor_overrides,
        )
        env_preprocessor = PolicyProcessorPipeline(steps=[LiberoProcessorStep()])
        env_postprocessor = PolicyProcessorPipeline(
            steps=[XVLARotation6DToAxisAngleProcessorStep()]
        )

        if device.startswith("cuda"):
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True

        use_amp = bool(getattr(policy.config, "use_amp", False))

        @contextmanager
        def inference_context() -> Iterator[None]:
            with torch.inference_mode():
                if use_amp:
                    with torch.autocast(device_type=torch.device(device).type):
                        yield
                else:
                    yield

        return cls(
            policy=policy,
            preprocess_observation=preprocess_observation,
            env_preprocessor=env_preprocessor,
            policy_preprocessor=policy_preprocessor,
            policy_postprocessor=policy_postprocessor,
            env_postprocessor=env_postprocessor,
            inference_context=inference_context,
            action_key=ACTION,
        )

    def reset(self) -> None:
        reset = getattr(self._policy, "reset", None)
        if callable(reset):
            reset()

    def select_action(
        self, remote_observation: Dict[str, np.ndarray], instruction: str
    ) -> np.ndarray:
        raw_observation = to_lerobot_libero_observation(remote_observation)
        observation = self._preprocess_observation(raw_observation)
        observation["task"] = [instruction]
        observation = self._env_preprocessor(observation)
        observation = self._policy_preprocessor(observation)
        with self._inference_context():
            action = self._policy.select_action(observation)
        action = self._policy_postprocessor(action)
        transition = self._env_postprocessor({self._action_key: action})
        action_array = _to_numpy(transition[self._action_key])
        if action_array.ndim != 2 or action_array.shape[0] != 1:
            raise ValueError(
                "xVLA policy must return a single batched action, "
                f"got {action_array.shape}"
            )
        return _validate_libero_action(action_array[0])


def append_episode_result(path: Path, result: EpisodeResult) -> None:
    """Append one durable, independently parseable episode result."""

    _append_report_record(path, "episode_result", result.to_dict())


def append_run_manifest(path: Path, manifest: RunManifest) -> None:
    """Append the reproducibility metadata for one evaluation invocation."""

    _append_report_record(path, "run_manifest", manifest.to_dict())


def _append_report_record(path: Path, record_type: str, payload: Dict[str, Any]) -> None:
    record = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "record_type": record_type,
        **payload,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        json.dump(record, stream, sort_keys=True)
        stream.write("\n")


def run_remote_episode(env: Any, policy: Any, spec: EpisodeSpec) -> EpisodeResult:
    """Run one xVLA episode and always release its remote session."""

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
            control_mode=spec.control_mode,
        )
        action_schema = reset_info.get("action_schema", {})
        confirmed_mode = action_schema.get("control_mode")
        if confirmed_mode != spec.control_mode:
            raise RuntimeError(
                "Remote server did not confirm the requested control mode: "
                f"requested={spec.control_mode!r}, confirmed={confirmed_mode!r}"
            )

        instruction = str(reset_info["language_instruction"])
        policy.reset()
        while steps < spec.max_steps:
            action = _validate_libero_action(policy.select_action(observation, instruction))
            observation, reward, terminated, truncated, step_info = env.step(action)
            steps += 1
            total_reward += float(reward)
            success = success or bool(step_info.get("success", False))
            if success or terminated or truncated:
                break

        return EpisodeResult(
            status="completed",
            suite=spec.suite,
            task_id=spec.task_id,
            init_state_id=spec.init_state_id,
            seed=spec.seed,
            session_id=str(reset_info.get("session_id", "")),
            episode_id=str(reset_info.get("episode_id", "")),
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


def to_lerobot_libero_observation(
    observation: Dict[str, np.ndarray],
) -> Dict[str, Any]:
    """Map the remote protocol schema to LeRobot's LIBERO observation shape."""

    required = (
        "agentview_image",
        "robot0_eye_in_hand_image",
        "robot0_eef_pos",
        "robot0_eef_quat_xyzw",
        "robot0_gripper_qpos",
    )
    missing = [key for key in required if key not in observation]
    if missing:
        raise ValueError(f"Remote observation is missing xVLA fields: {missing}")

    return {
        "pixels": {
            "image": np.ascontiguousarray(observation["agentview_image"], dtype=np.uint8),
            "image2": np.ascontiguousarray(
                observation["robot0_eye_in_hand_image"], dtype=np.uint8
            ),
        },
        "robot_state": {
            "eef": {
                "pos": _single_batch(observation["robot0_eef_pos"]),
                "quat": _single_batch(observation["robot0_eef_quat_xyzw"]),
            },
            "gripper": {
                "qpos": _single_batch(observation["robot0_gripper_qpos"]),
            },
        },
    }


def _single_batch(value: np.ndarray) -> np.ndarray:
    array = np.ascontiguousarray(value, dtype=np.float32)
    return array[np.newaxis, ...]


def _validate_libero_action(value: Any) -> np.ndarray:
    action = np.ascontiguousarray(value, dtype=np.float32)
    if action.shape != (7,):
        raise ValueError(f"xVLA LIBERO action must contain 7 values, got {action.shape}")
    if not np.isfinite(action).all():
        raise ValueError("xVLA LIBERO action values must be finite")
    return action


def _to_numpy(value: Any) -> np.ndarray:
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    numpy = getattr(value, "numpy", None)
    if callable(numpy):
        value = numpy()
    return np.asarray(value)


def _resolve_tokenizer_path(model_path: str, tokenizer_path: str) -> str:
    if tokenizer_path:
        path = Path(tokenizer_path).expanduser().resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"xVLA tokenizer directory does not exist: {path}")
        return str(path)

    sibling = Path(model_path).expanduser().resolve().parent / "facebook-bart-large-tokenizer"
    return str(sibling) if sibling.is_dir() else ""
