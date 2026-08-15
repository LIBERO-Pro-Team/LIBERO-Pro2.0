import numpy as np

from libero_remote.validation.equivalence import (
    compare_observations,
    validate_messagepack_roundtrip,
    validate_xvla_adapter_mapping,
)


def test_messagepack_and_xvla_adapter_layers_preserve_observation_values() -> None:
    observation = _observation()

    protocol = validate_messagepack_roundtrip(observation)
    adapter = validate_xvla_adapter_mapping(observation)

    assert protocol["passed"] is True
    assert protocol["wire_bytes_equal"] is True
    assert all(field["raw_bytes_equal"] for field in protocol["fields"].values())
    assert adapter["passed"] is True
    assert all(field["values_equal"] for field in adapter["fields"].values())


def test_observation_comparison_reports_state_and_image_metrics() -> None:
    local = _observation()
    remote = {key: value.copy() for key, value in local.items()}
    remote["robot0_eef_pos"][0] += np.float32(5e-7)
    remote["agentview_image"][0, 0, 0] += np.uint8(1)

    result = compare_observations(
        local,
        remote,
        state_rtol=1e-5,
        state_atol=1e-6,
        image_max_abs=1.0,
        image_mean_abs=0.1,
        image_mismatch_ratio=0.25,
    )

    assert result["passed"] is True
    assert result["state"]["robot0_eef_pos"]["max_abs_error"] > 0.0
    image = result["images"]["agentview_image"]
    assert image["max_abs_error"] == 1.0
    assert image["mismatched_pixel_ratio"] == 1 / 4


def _observation():
    return {
        "agentview_image": np.zeros((2, 2, 3), dtype=np.uint8),
        "robot0_eye_in_hand_image": np.full((2, 2, 3), 17, dtype=np.uint8),
        "robot0_joint_pos": np.arange(7, dtype=np.float32),
        "robot0_joint_vel": np.arange(7, dtype=np.float32) / 10,
        "robot0_eef_pos": np.array([0.1, 0.2, 0.3], dtype=np.float32),
        "robot0_eef_quat_xyzw": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        "robot0_gripper_qpos": np.array([-0.01, 0.01], dtype=np.float32),
    }
