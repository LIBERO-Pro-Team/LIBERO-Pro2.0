"""SOP acceptance metrics for protocol, policy adapter, and environment state."""

from typing import Any, Dict

import numpy as np

from libero_remote.protocol.codec import pack_message, unpack_message
from libero_remote.runner.xvla import to_lerobot_libero_observation


def validate_messagepack_roundtrip(
    observation: Dict[str, np.ndarray]
) -> Dict[str, Any]:
    """Verify keys, metadata, and C-order bytes after a MessagePack round trip."""

    payload = pack_message(observation)
    decoded = unpack_message(payload)
    if not isinstance(decoded, dict):
        return {"passed": False, "wire_bytes_equal": False, "fields": {}}

    fields: Dict[str, Dict[str, Any]] = {}
    for key in sorted(set(observation) | set(decoded)):
        source = observation.get(key)
        restored = decoded.get(key)
        if not isinstance(source, np.ndarray) or not isinstance(restored, np.ndarray):
            fields[key] = {
                "present_on_both_sides": key in observation and key in decoded,
                "dtype_equal": False,
                "shape_equal": False,
                "c_contiguous": False,
                "raw_bytes_equal": False,
            }
            continue
        fields[key] = {
            "present_on_both_sides": True,
            "dtype": str(source.dtype),
            "shape": list(source.shape),
            "dtype_equal": source.dtype == restored.dtype,
            "shape_equal": source.shape == restored.shape,
            "c_contiguous": bool(restored.flags.c_contiguous),
            "raw_bytes_equal": (
                source.tobytes(order="C") == restored.tobytes(order="C")
            ),
        }

    wire_bytes_equal = pack_message(decoded) == payload
    passed = set(observation) == set(decoded) and wire_bytes_equal and all(
        field["present_on_both_sides"]
        and field["dtype_equal"]
        and field["shape_equal"]
        and field["c_contiguous"]
        and field["raw_bytes_equal"]
        for field in fields.values()
    )
    return {
        "passed": passed,
        "encoded_bytes": len(payload),
        "wire_bytes_equal": wire_bytes_equal,
        "fields": fields,
    }


def validate_xvla_adapter_mapping(
    observation: Dict[str, np.ndarray]
) -> Dict[str, Any]:
    """Verify the xVLA input adapter preserves the five source observation arrays."""

    mapped = to_lerobot_libero_observation(observation)
    mappings = {
        "agentview_image": mapped["pixels"]["image"],
        "robot0_eye_in_hand_image": mapped["pixels"]["image2"],
        "robot0_eef_pos": mapped["robot_state"]["eef"]["pos"][0],
        "robot0_eef_quat_xyzw": mapped["robot_state"]["eef"]["quat"][0],
        "robot0_gripper_qpos": mapped["robot_state"]["gripper"]["qpos"][0],
    }
    fields = {
        source_key: {
            "source_dtype": str(observation[source_key].dtype),
            "mapped_dtype": str(np.asarray(mapped_value).dtype),
            "source_shape": list(observation[source_key].shape),
            "mapped_shape": list(np.asarray(mapped_value).shape),
            "values_equal": np.array_equal(observation[source_key], mapped_value),
        }
        for source_key, mapped_value in mappings.items()
    }
    return {
        "passed": all(field["values_equal"] for field in fields.values()),
        "fields": fields,
    }


def compare_observations(
    local: Dict[str, np.ndarray],
    remote: Dict[str, np.ndarray],
    *,
    state_rtol: float,
    state_atol: float,
    image_max_abs: float,
    image_mean_abs: float,
    image_mismatch_ratio: float,
) -> Dict[str, Any]:
    """Compare independent environment observations using declared tolerances."""

    missing_local = sorted(set(remote) - set(local))
    missing_remote = sorted(set(local) - set(remote))
    state: Dict[str, Dict[str, Any]] = {}
    images: Dict[str, Dict[str, Any]] = {}
    for key in sorted(set(local) & set(remote)):
        local_array = np.asarray(local[key])
        remote_array = np.asarray(remote[key])
        metadata_equal = (
            local_array.shape == remote_array.shape
            and local_array.dtype == remote_array.dtype
        )
        if not metadata_equal:
            metrics = {
                "passed": False,
                "local_dtype": str(local_array.dtype),
                "remote_dtype": str(remote_array.dtype),
                "local_shape": list(local_array.shape),
                "remote_shape": list(remote_array.shape),
            }
        else:
            difference = np.abs(
                local_array.astype(np.float64) - remote_array.astype(np.float64)
            )
            max_error = float(difference.max()) if difference.size else 0.0
            mean_error = float(difference.mean()) if difference.size else 0.0
            if key.endswith("_image"):
                element_mismatch = local_array != remote_array
                pixel_mismatch = (
                    np.any(element_mismatch, axis=-1)
                    if element_mismatch.ndim >= 3
                    else element_mismatch
                )
                mismatch = (
                    float(np.count_nonzero(pixel_mismatch) / pixel_mismatch.size)
                    if pixel_mismatch.size
                    else 0.0
                )
                metrics = {
                    "passed": (
                        max_error <= image_max_abs
                        and mean_error <= image_mean_abs
                        and mismatch <= image_mismatch_ratio
                    ),
                    "dtype": str(local_array.dtype),
                    "shape": list(local_array.shape),
                    "max_abs_error": max_error,
                    "mean_abs_error": mean_error,
                    "mismatched_pixel_ratio": mismatch,
                }
            else:
                metrics = {
                    "passed": bool(
                        np.allclose(
                            local_array,
                            remote_array,
                            rtol=state_rtol,
                            atol=state_atol,
                            equal_nan=False,
                        )
                    ),
                    "dtype": str(local_array.dtype),
                    "shape": list(local_array.shape),
                    "max_abs_error": max_error,
                    "mean_abs_error": mean_error,
                }
        if key.endswith("_image"):
            images[key] = metrics
        else:
            state[key] = metrics

    passed = not missing_local and not missing_remote and all(
        metrics["passed"] for metrics in [*state.values(), *images.values()]
    )
    return {
        "passed": passed,
        "missing_from_local": missing_local,
        "missing_from_remote": missing_remote,
        "state": state,
        "images": images,
    }
