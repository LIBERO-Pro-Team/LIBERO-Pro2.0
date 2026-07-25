"""Adapter for the real LIBERO-PRO OffScreenRenderEnv."""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base import EnvironmentAdapter
from .observations import describe_observation, normalize_standard_observation

SUPPORTED_SUITES = {"libero_goal", "libero_spatial", "libero_object", "libero_10"}


class LiberoEnvironmentAdapter(EnvironmentAdapter):
    def __init__(self) -> None:
        self._env: Any = None
        self._suite: Any = None
        self._task: Any = None
        self._init_states: Any = None
        self._camera_names: List[str] = []
        self._max_steps = 0
        self._step_index = 0
        self._control_mode = "relative"

    def create(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        self._configure_import_path()
        from libero.libero import benchmark
        from libero.libero.envs import OffScreenRenderEnv

        suite_name = str(spec["suite"])
        if suite_name not in SUPPORTED_SUITES:
            raise ValueError(f"Unsupported LIBERO suite: {suite_name}")

        suite_class = benchmark.get_benchmark_dict().get(suite_name)
        if suite_class is None:
            raise ValueError(f"LIBERO suite is not registered: {suite_name}")
        self._suite = suite_class()

        task_id = int(spec["task_id"])
        if task_id >= self._suite.get_num_tasks():
            raise ValueError("task_id is outside the selected suite")
        self._task = self._suite.get_task(task_id)
        self._init_states = self._suite.get_task_init_states(task_id)
        self._camera_names = list(spec["camera_names"])
        self._max_steps = int(spec["max_steps"])
        self._control_mode = str(spec.get("control_mode", "relative"))

        try:
            self._env = OffScreenRenderEnv(
                bddl_file_name=_resolve_task_bddl_file(
                    self._suite, self._task, task_id
                ),
                camera_names=self._camera_names,
                camera_heights=int(spec["camera_height"]),
                camera_widths=int(spec["camera_width"]),
            )
            first = self.reset(int(spec["init_state_id"]), int(spec["seed"]))
        except Exception:
            self.close()
            raise

        low, high = self._env.env.action_spec
        action_low, action_high = _controller_action_bounds(
            np.asarray(low, dtype=np.float32),
            np.asarray(high, dtype=np.float32),
            self._control_mode,
        )
        first.update(
            {
                "language_instruction": self._task.language,
                "action_schema": {
                    "version": "libero_action_v1",
                    "shape": list(action_low.shape),
                    "dtype": "float32",
                    "low": action_low.tolist(),
                    "high": action_high.tolist(),
                    "controller": "OSC_POSE",
                    "control_mode": self._control_mode,
                    "control_freq": int(getattr(self._env.env, "control_freq", 20)),
                    "action_repeat": 1,
                },
                "observation_schema_version": "libero_standard_v1",
                "observation_schema": describe_observation(first["observation"]),
            }
        )
        return first

    def reset(self, init_state_id: int, seed: int) -> Dict[str, Any]:
        if self._env is None or self._init_states is None:
            raise RuntimeError("Environment has not been created")
        if init_state_id < 0 or init_state_id >= len(self._init_states):
            raise ValueError("init_state_id is outside the selected task")
        self._env.seed(seed)
        self._env.reset()
        raw = self._env.set_init_state(self._init_states[init_state_id])
        _set_controller_mode(self._env, self._control_mode)
        self._step_index = 0
        return {
            "observation": normalize_standard_observation(raw, self._camera_names),
            "worker_step_index": 0,
        }

    def step(self, action: np.ndarray) -> Dict[str, Any]:
        raw, reward, done, info = self._env.step(action)
        self._step_index += 1
        success = bool(self._env.check_success())
        terminated = bool(done or success)
        truncated = self._step_index >= self._max_steps and not terminated
        return {
            "observation": normalize_standard_observation(raw, self._camera_names),
            "reward": float(reward),
            "terminated": terminated,
            "truncated": truncated,
            "success": success,
            "info": _scalar_info(info),
            "worker_step_index": self._step_index,
        }

    def close(self) -> None:
        env, self._env = self._env, None
        if env is not None:
            try:
                env.close()
            except Exception:
                pass

    @staticmethod
    def _configure_import_path() -> None:
        root: Optional[str] = os.environ.get("LIBERO_PRO_ROOT")
        if root:
            root = os.path.abspath(root)
            if root not in sys.path:
                sys.path.insert(0, root)


def _scalar_info(info: Any) -> Dict[str, Any]:
    if not isinstance(info, dict):
        return {}
    result: Dict[str, Any] = {}
    for key, value in info.items():
        if isinstance(value, np.generic):
            result[str(key)] = value.item()
        elif isinstance(value, (str, bool, int, float)) or value is None:
            result[str(key)] = value
    return result


def _set_controller_mode(environment: Any, control_mode: str) -> None:
    if control_mode not in {"relative", "absolute"}:
        raise ValueError(f"Unsupported LIBERO control mode: {control_mode}")

    robots = getattr(environment, "robots", None)
    if robots is None:
        robots = getattr(getattr(environment, "env", None), "robots", None)
    if not robots:
        raise RuntimeError("LIBERO environment does not expose robot controllers")

    use_delta = control_mode == "relative"
    for robot in robots:
        controller = getattr(robot, "controller", None)
        if controller is None or not hasattr(controller, "use_delta"):
            raise RuntimeError("LIBERO robot controller does not expose use_delta")
        controller.use_delta = use_delta


def _controller_action_bounds(
    low: np.ndarray, high: np.ndarray, control_mode: str
) -> Tuple[np.ndarray, np.ndarray]:
    if control_mode == "relative":
        return low.copy(), high.copy()
    if control_mode != "absolute":
        raise ValueError(f"Unsupported LIBERO control mode: {control_mode}")
    if low.shape != (7,) or high.shape != (7,):
        raise RuntimeError("Absolute OSC_POSE control requires a 7-dimensional action")

    position_limit = np.float32(2.0)
    rotation_limit = np.float32(np.pi)
    absolute_low = np.array(
        [-position_limit] * 3 + [-rotation_limit] * 3 + [low[-1]],
        dtype=np.float32,
    )
    absolute_high = np.array(
        [position_limit] * 3 + [rotation_limit] * 3 + [high[-1]],
        dtype=np.float32,
    )
    return absolute_low, absolute_high


def _resolve_task_bddl_file(suite: Any, task: Any, task_id: int) -> str:
    configured_root = os.environ.get("LIBERO_REMOTE_BDDL_ROOT")
    if not configured_root:
        return str(suite.get_task_bddl_file_path(task_id))

    root = Path(configured_root).resolve()
    candidate = (root / str(task.problem_folder) / str(task.bddl_file)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Resolved BDDL path is outside LIBERO_REMOTE_BDDL_ROOT") from exc
    if not candidate.is_file():
        raise FileNotFoundError(f"Configured BDDL file does not exist: {candidate}")
    return str(candidate)
