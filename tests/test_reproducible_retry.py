import hashlib
import sqlite3
import time
from pathlib import Path

from fastapi.testclient import TestClient

from libero_remote import RemoteRunClient
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings


def test_failed_attempt_reuses_identical_job_and_initial_state(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            cleanup_interval_seconds=0.01,
            heartbeat_interval_seconds=0.01,
            lease_grace_period_seconds=0.04,
            authentication_required=True,
            api_key_hashes={
                hashlib.sha256(b"secret-a").hexdigest(): "account-a"
            },
        )
    )
    spec = {
        "suite": "libero_goal",
        "task_id": 0,
        "init_state_id": 0,
        "seed": 142,
        "variant": "base",
        "camera_height": 16,
        "camera_width": 16,
        "max_steps": 10,
    }

    with TestClient(app) as http_client:
        client = RemoteRunClient(
            "http://testserver", http_client=http_client, api_key="secret-a"
        )
        run = client.submit_run([spec], owner_id="spoofed-account")
        first = client.claim(run["run_id"], "runner-a")
        assert first is not None
        first_spec = first.episode_spec
        first_identity = first.reproducibility
        time.sleep(0.08)

        second = client.claim(run["run_id"], "runner-a")
        assert second is not None
        second_identity = second.reproducibility
        episodes = client.get_episodes(run["run_id"])["episodes"]

    assert run["owner_id"] == "account-a"
    assert first_spec == episodes[0]["spec"]
    assert first_identity == second_identity
    assert set(first_identity) == {
        "job_fingerprint",
        "runtime_fingerprint",
        "initial_state_fingerprint",
        "initial_observation_fingerprint",
        "perturbation_plan_fingerprint",
    }
    assert all(len(value) == 64 for value in first_identity.values())
    assert episodes[0]["attempt"] == 2
    assert episodes[0]["spec"] == {
        **spec,
        "protocol_version": "1.0",
        "camera_names": ["agentview", "robot0_eye_in_hand"],
        "control_mode": "relative",
        "observation_schema_version": "libero_standard_v1",
    }
    assert episodes[0]["reproducibility"] == first_identity
    assert episodes[0]["perturbation_plan"] == {
        "case_id": "BASE",
        "seed": 142,
        "suite": "libero_goal",
        "task_id": 0,
        "version": "fake_plan_v1",
    }


def test_retry_rejects_a_changed_bound_perturbation_plan(tmp_path: Path) -> None:
    database = tmp_path / "scheduler.sqlite3"
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(database),
            worker_timeout_seconds=5.0,
            cleanup_interval_seconds=0.01,
            heartbeat_interval_seconds=0.01,
            lease_grace_period_seconds=0.04,
        )
    )

    with TestClient(app) as http_client:
        client = RemoteRunClient("http://testserver", http_client=http_client)
        run = client.submit_run(
            "user-a",
            [{"camera_height": 16, "camera_width": 16, "max_steps": 10}],
        )
        first = client.claim(run["run_id"], "runner-a")
        assert first is not None
        time.sleep(0.08)
        assert client.get_run(run["run_id"])["summary"]["queued"] == 1

        with sqlite3.connect(database) as connection:
            connection.execute(
                """
                UPDATE jobs SET perturbation_plan_fingerprint = ?
                WHERE job_id = ?
                """,
                ("0" * 64, first.job_id),
            )

        rejected = http_client.post(
            f"/v1/runs/{run['run_id']}/claim",
            json={"runner_id": "runner-a"},
        )
        snapshot = client.get_run(run["run_id"])

    assert rejected.status_code == 409
    assert rejected.json()["error_code"] == "REPRODUCIBILITY_MISMATCH"
    assert snapshot["status"] == "failed"
