"""Normalize LIBERO observations to the stable phase-one schema."""

from typing import Any, Dict, Iterable

import numpy as np

STANDARD_OBSERVATION_KEYS = (
    "agentview_image",
    "robot0_eye_in_hand_image",
    "robot0_joint_pos",
    "robot0_joint_vel",
    "robot0_eef_pos",
    "robot0_eef_quat",
    "robot0_gripper_qpos",
)


def normalize_standard_observation(
    observation: Dict[str, Any], camera_names: Iterable[str]
) -> Dict[str, np.ndarray]:
    """Return only stable, unnormalized RGB and proprioception fields."""

    required = [f"{name}_image" for name in camera_names]
    required.extend(STANDARD_OBSERVATION_KEYS[2:])
    missing = [key for key in required if key not in observation]
    if missing:
        raise ValueError(f"Environment observation is missing fields: {missing}")

    normalized: Dict[str, np.ndarray] = {}
    for key in required:
        output_key = "robot0_eef_quat_xyzw" if key == "robot0_eef_quat" else key
        value = np.asarray(observation[key])
        dtype = np.uint8 if key.endswith("_image") else np.float32
        normalized[output_key] = np.ascontiguousarray(value, dtype=dtype)
    return normalized


def describe_observation(observation: Dict[str, np.ndarray]) -> Dict[str, Dict[str, Any]]:
    return {
        key: {
            "shape": list(value.shape),
            "dtype": value.dtype.name,
            "byte_order": "little",
            "layout": "C",
        }
        for key, value in observation.items()
    }
