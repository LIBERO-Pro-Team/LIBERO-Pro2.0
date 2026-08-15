"""Deterministic adapter used to test the complete platform without MuJoCo."""

from typing import Any, Dict, List

import numpy as np

from libero_remote.reproducibility import (
    canonical_fingerprint,
    numerical_state_fingerprint,
)

from .base import EnvironmentAdapter
from .observations import describe_observation


class FakeEnvironmentAdapter(EnvironmentAdapter):
    def __init__(self) -> None:
        self._state = np.zeros(2, dtype=np.float32)
        self._step_index = 0
        self._max_steps = 0
        self._camera_names: List[str] = []
        self._height = 0
        self._width = 0
        self._closed = False
        self._spec: Dict[str, Any] = {}

    def create(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        self._spec = dict(spec)
        self._camera_names = list(spec["camera_names"])
        self._height = int(spec["camera_height"])
        self._width = int(spec["camera_width"])
        self._max_steps = int(spec["max_steps"])
        initial = self.reset(int(spec["init_state_id"]), int(spec["seed"]))
        initial.update(
            {
                "language_instruction": "fake manipulation task",
                "action_schema": {
                    "version": "libero_action_v1",
                    "shape": [2],
                    "dtype": "float32",
                    "low": [-1.0, -1.0],
                    "high": [1.0, 1.0],
                    "controller": "FAKE_DELTA",
                    "control_mode": str(spec.get("control_mode", "relative")),
                    "translation_frame": "world",
                    "rotation_frame": "world",
                    "rotation_representation": "axis_angle",
                    "gripper_semantics": "negative_open_positive_close_zero_hold",
                    "control_freq": 20,
                    "action_repeat": 1,
                },
                "observation_schema_version": "libero_standard_v1",
                "observation_schema": describe_observation(initial["observation"]),
            }
        )
        return initial

    def reset(self, init_state_id: int, seed: int) -> Dict[str, Any]:
        self._state = np.array([float(init_state_id), 0.0], dtype=np.float32)
        self._step_index = 0
        plan = {
            "version": "fake_plan_v1",
            "suite": self._spec.get("suite"),
            "task_id": self._spec.get("task_id"),
            "case_id": str(self._spec.get("variant", "base")).upper(),
            "seed": int(seed),
        }
        return {
            "observation": self._observation(),
            "worker_step_index": 0,
            "environment_reproducibility": {
                "initial_state_fingerprint": numerical_state_fingerprint(self._state),
                "perturbation_plan_fingerprint": canonical_fingerprint(plan),
                "perturbation_plan": plan,
            },
        }

    def step(self, action: np.ndarray) -> Dict[str, Any]:
        if self._closed:
            raise RuntimeError("Environment is closed")
        self._state += action
        self._step_index += 1
        terminated = bool(self._state[0] >= 1.0)
        truncated = self._step_index >= self._max_steps and not terminated
        return {
            "observation": self._observation(),
            "reward": float(terminated),
            "terminated": terminated,
            "truncated": truncated,
            "success": terminated,
            "info": {},
            "worker_step_index": self._step_index,
        }

    def close(self) -> None:
        self._closed = True

    def _observation(self) -> Dict[str, np.ndarray]:
        pixel = np.uint8(min(255, max(0, int(round(float(self._state[0]) * 10)))))
        observation: Dict[str, np.ndarray] = {
            "robot0_joint_pos": self._state.copy(),
            "robot0_joint_vel": np.zeros(2, dtype=np.float32),
            "robot0_eef_pos": np.array([self._state[0], 0.0, 0.0], dtype=np.float32),
            "robot0_eef_quat_xyzw": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            "robot0_gripper_qpos": np.array([self._state[1]], dtype=np.float32),
        }
        for name in self._camera_names:
            observation[f"{name}_image"] = np.full(
                (self._height, self._width, 3), pixel, dtype=np.uint8
            )
        return observation
