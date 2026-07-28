import httpx
import numpy as np
import pytest

from libero_remote import RemoteLiberoEnv


class FlakyStepClient:
    def __init__(self) -> None:
        self.requests = []

    def post(self, path, json):
        self.requests.append((path, json))
        if len(self.requests) == 1:
            request = httpx.Request("POST", f"http://testserver{path}")
            raise httpx.RemoteProtocolError(
                "Server disconnected without sending a response.", request=request
            )
        return httpx.Response(
            200,
            json={
                "request_id": json["request_id"],
                "step_index": json["expected_step_index"],
                "next_step_index": json["expected_step_index"] + 1,
                "observation": {"robot0_joint_pos": [0.25]},
                "reward": 0.0,
                "terminated": False,
                "truncated": False,
                "success": False,
                "server_step_seconds": 0.01,
            },
        )


def test_step_retries_transport_error_with_identical_idempotency_payload() -> None:
    client = FlakyStepClient()
    env = RemoteLiberoEnv(base_url="http://testserver", http_client=client)
    env.session_id = "ses_test"
    env.episode_id = "ep_test"
    env.next_step_index = 7

    _, _, terminated, truncated, info = env.step(
        np.array([0.25, 0.0], dtype=np.float32), request_id="req_fixed"
    )

    assert not terminated
    assert not truncated
    assert info["request_id"] == "req_fixed"
    assert env.next_step_index == 8
    assert len(client.requests) == 2
    assert client.requests[0] == client.requests[1]


def test_reset_does_not_retry_a_non_idempotent_session_create() -> None:
    client = FlakyStepClient()
    env = RemoteLiberoEnv(base_url="http://testserver", http_client=client)

    with pytest.raises(httpx.RemoteProtocolError):
        env.reset()

    assert len(client.requests) == 1
