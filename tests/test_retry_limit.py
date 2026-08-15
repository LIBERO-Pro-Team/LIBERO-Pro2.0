from pathlib import Path

from fastapi.testclient import TestClient

from libero_remote import RemoteRunClient
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings


def test_agent_failure_is_terminal_even_when_retry_budget_remains(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            max_attempts=3,
        )
    )

    with TestClient(app) as http_client:
        client = RemoteRunClient("http://testserver", http_client=http_client)
        run = client.submit_run(
            "user-a",
            [{"camera_height": 16, "camera_width": 16, "max_steps": 10}],
        )
        episode = client.claim(run["run_id"], "runner-a")
        assert episode is not None
        abandoned = episode.abandon()
        snapshot = client.get_run(run["run_id"])
        jobs = client.get_episodes(run["run_id"])["episodes"]

    assert abandoned["status"] == "failed"
    assert snapshot["status"] == "failed"
    assert jobs[0]["attempt"] == 1
    assert jobs[0]["result"]["failure_class"] == "AGENT_FAILURE"


def test_server_restart_cannot_bypass_retry_limit(tmp_path: Path) -> None:
    database = tmp_path / "scheduler.sqlite3"
    settings = Settings(
        environment_backend="fake",
        max_sessions=1,
        scheduler_db_path=str(database),
        worker_timeout_seconds=5.0,
        max_attempts=1,
    )

    with TestClient(create_app(settings)) as first_server:
        first_client = RemoteRunClient(
            "http://testserver", http_client=first_server
        )
        run = first_client.submit_run(
            "user-a",
            [{"camera_height": 16, "camera_width": 16, "max_steps": 10}],
        )
        episode = first_client.claim(run["run_id"], "runner-a")
        assert episode is not None

    with TestClient(create_app(settings)) as restarted_server:
        restarted_client = RemoteRunClient(
            "http://testserver", http_client=restarted_server
        )
        snapshot = restarted_client.get_run(run["run_id"])
        jobs = restarted_client.get_episodes(run["run_id"])["episodes"]

    assert snapshot["status"] == "failed"
    assert snapshot["summary"]["failed"] == 1
    assert jobs[0]["attempt"] == 1
    assert jobs[0]["result"]["failure_class"] == "SERVER_RESTART"
