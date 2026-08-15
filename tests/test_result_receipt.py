import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from libero_remote import RemoteRunClient
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings


def test_server_result_has_stable_receipt_and_action_chain(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            authentication_required=True,
            api_key_hashes={
                hashlib.sha256(b"secret-a").hexdigest(): "account-a"
            },
            result_signing_key="receipt-secret",
        )
    )

    with TestClient(app) as http_client:
        client = RemoteRunClient(
            "http://testserver", http_client=http_client, api_key="secret-a"
        )
        run = client.submit_run(
            [{"camera_height": 16, "camera_width": 16, "max_steps": 10}]
        )
        episode = client.claim(run["run_id"], "runner-a")
        assert episode is not None
        episode.step([1.0, 0.0], request_id="finish")
        completed = episode.complete()
        replayed = client._transport.post(
            f"/v1/leases/{episode.lease_id}/complete",
            {
                "runner_id": "runner-a",
                "lease_generation": 1,
            },
        )

    result = completed["result"]
    assert completed == replayed
    assert len(completed["result_receipt"]) == 64
    assert result["account_id"] == "account-a"
    assert result["run_id"] == run["run_id"]
    assert result["job_id"] == episode.job_id
    assert result["attempt"] == 1
    assert result["lease_generation"] == 1
    assert result["job_fingerprint"] == episode.reproducibility["job_fingerprint"]
    assert result["initial_state_fingerprint"] == episode.reproducibility[
        "initial_state_fingerprint"
    ]
    assert result["initial_observation_fingerprint"] == episode.reproducibility[
        "initial_observation_fingerprint"
    ]
    assert result["perturbation_plan_fingerprint"] == episode.reproducibility[
        "perturbation_plan_fingerprint"
    ]
    assert len(result["action_chain_hash"]) == 64
    assert result["success"] is True


def test_completed_result_remains_durable_when_worker_cleanup_fails(
    tmp_path: Path, monkeypatch
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            result_signing_key="receipt-secret",
        )
    )

    with TestClient(app) as http_client:
        client = RemoteRunClient("http://testserver", http_client=http_client)
        run = client.submit_run(
            "account-a", [{"camera_height": 16, "camera_width": 16, "max_steps": 10}]
        )
        episode = client.claim(run["run_id"], "runner-a")
        assert episode is not None
        episode.step([1.0, 0.0], request_id="finish")

        manager = app.state.session_manager
        original_close = manager.close

        async def fail_cleanup(*args, **kwargs):
            del args, kwargs
            raise RuntimeError("injected cleanup failure")

        monkeypatch.setattr(manager, "close", fail_cleanup)
        completed = episode.complete()
        monkeypatch.setattr(manager, "close", original_close)
        replayed = client._transport.post(
            f"/v1/leases/{episode.lease_id}/complete",
            {"runner_id": "runner-a", "lease_generation": 1},
        )
        snapshot = client.get_run(run["run_id"])

    assert completed == replayed
    assert completed["result"]["success"] is True
    assert snapshot["status"] == "completed"
