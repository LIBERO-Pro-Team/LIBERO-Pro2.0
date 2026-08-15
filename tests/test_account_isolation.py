import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from libero_remote.protocol.codec import unpack_message
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings

USER_A = {"Authorization": "Bearer secret-a"}
USER_B = {"Authorization": "Bearer secret-b"}


def test_direct_sessions_enforce_per_account_capacity(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=3,
            max_active_sessions_per_owner=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            authentication_required=True,
            api_key_hashes={
                hashlib.sha256(b"secret-a").hexdigest(): "account-a",
                hashlib.sha256(b"secret-b").hexdigest(): "account-b",
            },
        )
    )
    request = {
        "camera_height": 16,
        "camera_width": 16,
        "max_steps": 1,
    }

    with TestClient(app) as client:
        first_a = client.post("/v1/sessions", json=request, headers=USER_A)
        second_a = client.post("/v1/sessions", json=request, headers=USER_A)
        first_b = client.post("/v1/sessions", json=request, headers=USER_B)

    assert first_a.status_code == 201
    assert second_a.status_code == 503
    assert second_a.json()["error_code"] == "SESSION_CAPACITY_REACHED"
    assert first_b.status_code == 201


def test_authenticated_accounts_cannot_access_each_others_runs_or_sessions(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            authentication_required=True,
            api_key_hashes={
                hashlib.sha256(b"secret-a").hexdigest(): "account-a",
                hashlib.sha256(b"secret-b").hexdigest(): "account-b",
            },
        )
    )
    episode = {"camera_height": 16, "camera_width": 16, "max_steps": 10}

    with TestClient(app) as client:
        missing = client.post("/v1/runs", json={"episodes": [episode]})
        submitted = client.post(
            "/v1/runs", json={"episodes": [episode]}, headers=USER_A
        )
        run_id = submitted.json()["run_id"]

        hidden_get = client.get(f"/v1/runs/{run_id}", headers=USER_B)
        hidden_claim = client.post(
            f"/v1/runs/{run_id}/claim",
            json={"runner_id": "runner-b"},
            headers=USER_B,
        )
        hidden_cancel = client.delete(f"/v1/runs/{run_id}", headers=USER_B)

        claimed_response = client.post(
            f"/v1/runs/{run_id}/claim",
            json={"runner_id": "runner-a"},
            headers=USER_A,
        )
        claimed = unpack_message(claimed_response.content)
        session_id = claimed["session"]["session_id"]
        hidden_session = client.get(f"/v1/sessions/{session_id}", headers=USER_B)
        hidden_step = client.post(
            f"/v1/sessions/{session_id}/step",
            json={
                "episode_id": claimed["session"]["episode_id"],
                "expected_step_index": 0,
                "request_id": "cross-account-step",
                "lease_id": claimed["lease_id"],
                "lease_generation": claimed["lease_generation"],
                "action": [1.0, 0.0],
            },
            headers=USER_B,
        )
        hidden_heartbeat = client.post(
            f"/v1/leases/{claimed['lease_id']}/heartbeat",
            json={
                "runner_id": "runner-a",
                "lease_generation": claimed["lease_generation"],
            },
            headers=USER_B,
        )
        hidden_complete = client.post(
            f"/v1/leases/{claimed['lease_id']}/complete",
            json={
                "runner_id": "runner-a",
                "lease_generation": claimed["lease_generation"],
            },
            headers=USER_B,
        )
        hidden_close = client.delete(f"/v1/sessions/{session_id}", headers=USER_B)

    assert missing.status_code == 401
    assert submitted.status_code == 201
    assert submitted.json()["owner_id"] == "account-a"
    assert hidden_get.status_code == 404
    assert hidden_claim.status_code == 404
    assert hidden_cancel.status_code == 404
    assert hidden_session.status_code == 404
    assert hidden_step.status_code == 404
    assert hidden_heartbeat.status_code == 404
    assert hidden_complete.status_code == 404
    assert hidden_close.status_code == 404
