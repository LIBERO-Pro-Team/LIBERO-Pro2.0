import hashlib
import time
from pathlib import Path

from fastapi.testclient import TestClient

from libero_remote.protocol.codec import unpack_message
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings

AUTH = {"Authorization": "Bearer secret-a"}


def test_expired_lease_cannot_step_before_cleanup_closes_its_worker(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            cleanup_interval_seconds=10.0,
            heartbeat_interval_seconds=0.01,
            lease_grace_period_seconds=0.05,
            authentication_required=True,
            api_key_hashes={
                hashlib.sha256(b"secret-a").hexdigest(): "account-a"
            },
        )
    )

    with TestClient(app) as client:
        run = client.post(
            "/v1/runs",
            json={
                "episodes": [
                    {"camera_height": 16, "camera_width": 16, "max_steps": 10}
                ]
            },
            headers=AUTH,
        ).json()
        claim = unpack_message(
            client.post(
                f"/v1/runs/{run['run_id']}/claim",
                json={"runner_id": "runner-a"},
                headers=AUTH,
            ).content
        )
        time.sleep(0.08)
        session = claim["session"]
        stale_step = client.post(
            f"/v1/sessions/{session['session_id']}/step",
            json={
                "episode_id": session["episode_id"],
                "expected_step_index": 0,
                "request_id": "stale-step",
                "lease_id": claim["lease_id"],
                "lease_generation": claim["lease_generation"],
                "action": [1.0, 0.0],
            },
            headers=AUTH,
        )
        stale_heartbeat = client.post(
            f"/v1/leases/{claim['lease_id']}/heartbeat",
            json={
                "runner_id": "runner-a",
                "lease_generation": claim["lease_generation"],
            },
            headers=AUTH,
        )

    assert stale_step.status_code == 409
    assert stale_step.json()["error_code"] == "STALE_LEASE"
    assert stale_heartbeat.status_code == 409
    assert stale_heartbeat.json()["error_code"] == "STALE_LEASE"
