import hashlib
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from libero_remote import RemoteRunClient
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings


def test_two_accounts_execute_in_independent_workers_and_states(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=2,
            max_active_sessions_per_owner=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            authentication_required=True,
            api_key_hashes={
                hashlib.sha256(b"secret-a").hexdigest(): "account-a",
                hashlib.sha256(b"secret-b").hexdigest(): "account-b",
            },
            result_signing_key="receipt-secret",
        )
    )
    spec = [{"camera_height": 16, "camera_width": 16, "max_steps": 2}]

    with TestClient(app) as http_client:
        a = RemoteRunClient(
            "http://testserver", http_client=http_client, api_key="secret-a"
        )
        b = RemoteRunClient(
            "http://testserver", http_client=http_client, api_key="secret-b"
        )
        run_a = a.submit_run(spec)
        run_b = b.submit_run(spec)
        episode_a = a.claim(run_a["run_id"], "runner-a")
        episode_b = b.claim(run_b["run_id"], "runner-b")
        assert episode_a is not None and episode_b is not None

        observation_b_before, info_b = episode_b.initial_observation()
        episode_a.step(np.array([0.5, 0.0], dtype=np.float32), "a-step-0")
        snapshot_b = http_client.get(
            f"/v1/sessions/{info_b['session_id']}",
            headers={"Authorization": "Bearer secret-b"},
        ).json()
        observation_b_after, _ = episode_b.initial_observation()

        _, _, _, truncated_a, _ = episode_a.step(
            np.array([0.0, 0.0], dtype=np.float32), "a-step-1"
        )
        _, _, _, truncated_b, _ = episode_b.step(
            np.array([0.0, 0.0], dtype=np.float32), "b-step-0"
        )
        _, _, _, truncated_b, _ = episode_b.step(
            np.array([0.0, 0.0], dtype=np.float32), "b-step-1"
        )
        result_a = episode_a.complete()
        result_b = episode_b.complete()

    assert episode_a.lease_id != episode_b.lease_id
    assert info_b["session_id"] != episode_a.initial_observation()[1]["session_id"]
    assert snapshot_b["next_step_index"] == 0
    assert np.array_equal(
        observation_b_before["robot0_joint_pos"],
        observation_b_after["robot0_joint_pos"],
    )
    assert truncated_a and truncated_b
    assert result_a["result"]["account_id"] == "account-a"
    assert result_b["result"]["account_id"] == "account-b"
    assert result_a["result"]["action_chain_hash"] != result_b["result"][
        "action_chain_hash"
    ]
