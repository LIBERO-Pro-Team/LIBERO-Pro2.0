import numpy as np

from libero_remote.protocol.codec import pack_message, unpack_message


def test_observation_arrays_round_trip_without_changes() -> None:
    observation = {
        "agentview_image": np.arange(48, dtype=np.uint8).reshape(4, 4, 3),
        "robot0_joint_pos": np.array([0.1, -0.2, 0.3], dtype=np.float32),
    }

    decoded = unpack_message(pack_message({"observation": observation}))

    for key, expected in observation.items():
        actual = decoded["observation"][key]
        assert isinstance(actual, np.ndarray)
        assert actual.dtype == expected.dtype
        assert actual.shape == expected.shape
        assert actual.flags.c_contiguous
        assert actual.tobytes() == expected.tobytes()
