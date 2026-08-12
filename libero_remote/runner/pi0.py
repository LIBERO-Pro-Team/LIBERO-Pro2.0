"""Pi0 adapter using only the LIBERO-Pro canonical observation/action seam."""

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator

import numpy as np

from .agent import (
    AgentCapabilities,
    CanonicalObservation,
    EpisodeContext,
)

MINIMUM_CUDA_RUNTIME_HEADROOM_BYTES = 1024**3


class Pi0PolicyAdapter:
    """Load the checkpoint's official LeRobot Pi0 processors behind the Agent seam."""

    AGENT_NAME = "pi0"
    AGENT_VERSION = "0.1.0"

    def __init__(
        self,
        policy: Any,
        preprocess_observation: Any,
        env_preprocessor: Any,
        policy_preprocessor: Any,
        policy_postprocessor: Any,
        inference_context: Any,
    ) -> None:
        self._policy = policy
        self._preprocess_observation = preprocess_observation
        self._env_preprocessor = env_preprocessor
        self._policy_preprocessor = policy_preprocessor
        self._policy_postprocessor = policy_postprocessor
        self._inference_context = inference_context

    @classmethod
    def load(
        cls,
        model_path: str,
        device: str = "cuda",
        tokenizer_path: str = "",
    ) -> "Pi0PolicyAdapter":
        """Load Pi0 and its checkpoint processors lazily in the user's model environment."""

        import torch
        from lerobot.configs import PreTrainedConfig
        from lerobot.envs import preprocess_observation
        from lerobot.policies import make_pre_post_processors
        from lerobot.policies.pi0.configuration_pi0 import PI0Config
        from lerobot.policies.pi0.modeling_pi0 import PI0Policy
        from lerobot.processor import LiberoProcessorStep, PolicyProcessorPipeline

        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but PyTorch cannot access a CUDA device")
        if device.startswith("cuda"):
            weights_path = Path(model_path) / "model.safetensors"
            if weights_path.is_file():
                free_bytes, total_bytes = torch.cuda.mem_get_info(device)
                weights_bytes = weights_path.stat().st_size
                required_bytes = weights_bytes + MINIMUM_CUDA_RUNTIME_HEADROOM_BYTES
                if required_bytes > free_bytes:
                    raise RuntimeError(
                        "Pi0 checkpoint does not fit in currently free CUDA memory with "
                        "minimum inference headroom: "
                        f"weights={weights_bytes} bytes, headroom="
                        f"{MINIMUM_CUDA_RUNTIME_HEADROOM_BYTES} bytes, "
                        f"free={free_bytes} bytes, "
                        f"total={total_bytes} bytes"
                    )
        config = PreTrainedConfig.from_pretrained(model_path)
        if not isinstance(config, PI0Config):
            raise TypeError(
                f"Pi0 adapter requires a Pi0 checkpoint, got {type(config).__name__}"
            )
        config.device = device
        # These checkpoint training settings are not required for inference.
        config.compile_model = False
        config.gradient_checkpointing = False
        policy = PI0Policy.from_pretrained(model_path, config=config)
        _verify_checkpoint_loaded(policy, Path(model_path) / "model.safetensors")
        policy.eval()
        preprocessor_overrides = {"device_processor": {"device": device}}
        if tokenizer_path:
            preprocessor_overrides["tokenizer_processor"] = {
                "tokenizer_name": tokenizer_path
            }
        policy_preprocessor, policy_postprocessor = make_pre_post_processors(
            policy_cfg=policy.config,
            pretrained_path=model_path,
            preprocessor_overrides=preprocessor_overrides,
        )
        env_preprocessor = PolicyProcessorPipeline(steps=[LiberoProcessorStep()])

        @contextmanager
        def inference_context() -> Iterator[None]:
            with torch.inference_mode():
                yield

        return cls(
            policy=policy,
            preprocess_observation=preprocess_observation,
            env_preprocessor=env_preprocessor,
            policy_preprocessor=policy_preprocessor,
            policy_postprocessor=policy_postprocessor,
            inference_context=inference_context,
        )

    def describe(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_name=self.AGENT_NAME,
            agent_version=self.AGENT_VERSION,
            required_cameras=("agentview", "robot0_eye_in_hand"),
            required_observation_fields=(
                "robot0_eef_pos",
                "robot0_eef_quat_xyzw",
                "robot0_gripper_qpos",
            ),
            control_mode="relative",
            maximum_inference_seconds=120.0,
        )

    def reset(self, episode: EpisodeContext) -> None:
        del episode
        reset = getattr(self._policy, "reset", None)
        if callable(reset):
            reset()

    def act(self, observation: CanonicalObservation) -> np.ndarray:
        raw_observation = to_lerobot_pi0_observation(observation)
        model_observation = self._preprocess_observation(raw_observation)
        model_observation["task"] = str(observation["instruction"])
        model_observation = self._env_preprocessor(model_observation)
        model_observation = self._policy_preprocessor(model_observation)
        with self._inference_context():
            action = self._policy.select_action(model_observation)
        action = self._policy_postprocessor(action)
        action_array = _to_numpy(action)
        if action_array.ndim == 2 and action_array.shape[0] == 1:
            action_array = action_array[0]
        action_array = np.ascontiguousarray(action_array, dtype=np.float32)
        if action_array.shape != (7,):
            raise ValueError(f"Pi0 LIBERO action must contain 7 values, got {action_array.shape}")
        if not np.isfinite(action_array).all():
            raise ValueError("Pi0 LIBERO action values must be finite")
        # Official action unnormalizers can produce small numerical overshoot.
        return np.ascontiguousarray(np.clip(action_array, -1.0, 1.0), dtype=np.float32)


def to_lerobot_pi0_observation(observation: Dict[str, Any]) -> Dict[str, Any]:
    """Map server-declared raw fields to the official LeRobot LIBERO structure."""

    required = (
        "agentview_image",
        "robot0_eye_in_hand_image",
        "robot0_eef_pos",
        "robot0_eef_quat_xyzw",
        "robot0_gripper_qpos",
    )
    missing = [key for key in required if key not in observation]
    if missing:
        raise ValueError(f"Remote observation is missing Pi0 fields: {missing}")
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


def _single_batch(value: Any) -> np.ndarray:
    array = np.ascontiguousarray(value, dtype=np.float32)
    return array[np.newaxis, ...]


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


def _verify_checkpoint_loaded(policy: Any, weights_path: Path) -> None:
    """Reject LeRobot's fallback policy when checkpoint loading was unsuccessful."""

    from safetensors import safe_open

    key = "model.action_out_proj.bias"
    state = policy.state_dict()
    if key not in state:
        raise RuntimeError(f"Loaded Pi0 policy is missing verification weight {key!r}")
    with safe_open(str(weights_path), framework="pt", device="cpu") as checkpoint:
        if key not in checkpoint.keys():
            raise RuntimeError(f"Pi0 checkpoint is missing verification weight {key!r}")
        expected = checkpoint.get_tensor(key)
    actual = state[key].detach().cpu()
    if actual.shape != expected.shape or not actual.equal(expected):
        raise RuntimeError(
            "Pi0 policy weights do not match model.safetensors; checkpoint loading failed"
        )
