import time
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from libero_remote import RemoteRunClient
from libero_remote.protocol.codec import unpack_message
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "assets" / "task_manifest.json"


def test_scheduled_run_persists_manifest_default_max_steps(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            task_manifest_path=str(MANIFEST_PATH),
        )
    )
    request = {
        "episodes": [
            {
                "suite": "libero_spatial",
                "task_id": 0,
                "camera_height": 16,
                "camera_width": 16,
            }
        ]
    }

    with TestClient(app) as http_client:
        run_id = http_client.post("/v1/runs", json=request).json()["run_id"]
        episodes = http_client.get(f"/v1/runs/{run_id}/episodes").json()["episodes"]

    assert episodes[0]["spec"]["max_steps"] == 220


def test_user_can_submit_and_inspect_a_persistent_episode_run(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
        )
    )
    request = {
        "owner_id": "user-a",
        "episodes": [
            {
                "suite": "libero_goal",
                "task_id": 0,
                "init_state_id": 0,
                "seed": 42,
                "camera_height": 16,
                "camera_width": 16,
                "max_steps": 10,
            },
            {
                "suite": "libero_goal",
                "task_id": 1,
                "init_state_id": 0,
                "seed": 43,
                "camera_height": 16,
                "camera_width": 16,
                "max_steps": 10,
            },
        ],
    }

    with TestClient(app) as http_client:
        submitted = http_client.post("/v1/runs", json=request)
        run_id = submitted.json()["run_id"]
        inspected = http_client.get(f"/v1/runs/{run_id}")

    assert submitted.status_code == 201
    assert inspected.status_code == 200
    assert inspected.json() == {
        "protocol_version": "1.0",
        "run_id": run_id,
        "owner_id": "user-a",
        "status": "queued",
        "summary": {
            "total": 2,
            "queued": 2,
            "active": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "successful": 0,
            "success_rate": None,
            "by_variant": {
                "base": {
                    "total": 2,
                    "completed": 0,
                    "successful": 0,
                    "success_rate": None,
                }
            },
        },
    }


def test_claim_atomically_creates_one_session_and_is_idempotent(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=2,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
        )
    )
    request = {
        "owner_id": "user-a",
        "episodes": [
            {
                "suite": "libero_goal",
                "task_id": 0,
                "camera_height": 16,
                "camera_width": 16,
                "max_steps": 10,
            }
        ],
    }

    with TestClient(app) as http_client:
        run_id = http_client.post("/v1/runs", json=request).json()["run_id"]
        first_response = http_client.post(
            f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
        )
        retried_response = http_client.post(
            f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
        )
        snapshot = http_client.get(f"/v1/runs/{run_id}").json()
        health = http_client.get("/v1/health").json()

    first = unpack_message(first_response.content)
    retried = unpack_message(retried_response.content)
    assert first_response.status_code == 200
    assert first["status"] == "leased"
    assert first["lease_id"] == retried["lease_id"]
    assert first["session"]["session_id"] == retried["session"]["session_id"]
    assert first["session"]["observation"]["agentview_image"].shape == (16, 16, 3)
    assert snapshot["summary"]["queued"] == 0
    assert snapshot["summary"]["active"] == 1
    assert health["sessions"]["active"] == 1


def test_complete_uses_server_outcome_and_releases_the_environment_slot(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
        )
    )
    run_request = {
        "owner_id": "user-a",
        "episodes": [
            {
                "camera_height": 16,
                "camera_width": 16,
                "max_steps": 10,
            }
        ],
    }

    with TestClient(app) as http_client:
        run_id = http_client.post("/v1/runs", json=run_request).json()["run_id"]
        claimed_response = http_client.post(
            f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
        )
        claimed = unpack_message(claimed_response.content)
        session = claimed["session"]
        step_response = http_client.post(
            f"/v1/sessions/{session['session_id']}/step",
            json={
                "episode_id": session["episode_id"],
                "expected_step_index": 0,
                "request_id": "finish-episode",
                "action": [1.0, 0.0],
            },
        )
        assert unpack_message(step_response.content)["success"] is True

        completed = http_client.post(
            f"/v1/leases/{claimed['lease_id']}/complete",
            json={"runner_id": "runner-a"},
        )
        replayed = http_client.post(
            f"/v1/leases/{claimed['lease_id']}/complete",
            json={"runner_id": "runner-a"},
        )
        snapshot = http_client.get(f"/v1/runs/{run_id}").json()
        health = http_client.get("/v1/health").json()

    assert completed.status_code == 200
    assert completed.json() == replayed.json()
    assert completed.json()["result"]["success"] is True
    assert completed.json()["result"]["step_count"] == 1
    assert snapshot["status"] == "completed"
    assert snapshot["summary"]["completed"] == 1
    assert snapshot["summary"]["successful"] == 1
    assert snapshot["summary"]["success_rate"] == 1.0
    assert health["sessions"]["active"] == 0


def test_heartbeat_keeps_a_slow_runner_lease_and_session_alive(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            session_idle_timeout_seconds=0.4,
            cleanup_interval_seconds=0.01,
            heartbeat_interval_seconds=0.05,
            lease_grace_period_seconds=0.4,
        )
    )
    run_request = {
        "owner_id": "slow-model-user",
        "episodes": [
            {"camera_height": 16, "camera_width": 16, "max_steps": 10}
        ],
    }

    with TestClient(app) as http_client:
        run_id = http_client.post("/v1/runs", json=run_request).json()["run_id"]
        claimed = unpack_message(
            http_client.post(
                f"/v1/runs/{run_id}/claim", json={"runner_id": "slow-runner"}
            ).content
        )
        original_expiry = claimed["lease_expires_at"]
        time.sleep(0.15)
        heartbeat = http_client.post(
            f"/v1/leases/{claimed['lease_id']}/heartbeat",
            json={"runner_id": "slow-runner"},
        )
        time.sleep(0.3)
        health = http_client.get("/v1/health").json()

    assert heartbeat.status_code == 200
    assert heartbeat.json()["status"] == "active"
    assert heartbeat.json()["lease_expires_at"] > original_expiry
    assert health["sessions"]["active"] == 1


def test_expired_lease_requeues_episode_from_reset_and_rejects_old_attempt(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            session_idle_timeout_seconds=5.0,
            cleanup_interval_seconds=0.01,
            heartbeat_interval_seconds=0.02,
            lease_grace_period_seconds=0.05,
        )
    )
    run_request = {
        "owner_id": "user-a",
        "episodes": [
            {"camera_height": 16, "camera_width": 16, "max_steps": 10}
        ],
    }

    with TestClient(app) as http_client:
        run_id = http_client.post("/v1/runs", json=run_request).json()["run_id"]
        first = unpack_message(
            http_client.post(
                f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
            ).content
        )
        time.sleep(0.12)
        expired_snapshot = http_client.get(f"/v1/runs/{run_id}").json()
        health_after_expiry = http_client.get("/v1/health").json()
        old_heartbeat = http_client.post(
            f"/v1/leases/{first['lease_id']}/heartbeat",
            json={"runner_id": "runner-a"},
        )
        old_complete = http_client.post(
            f"/v1/leases/{first['lease_id']}/complete",
            json={"runner_id": "runner-a"},
        )
        second = unpack_message(
            http_client.post(
                f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
            ).content
        )

    assert expired_snapshot["summary"]["queued"] == 1
    assert expired_snapshot["summary"]["active"] == 0
    assert health_after_expiry["sessions"]["active"] == 0
    assert old_heartbeat.status_code == 409
    assert old_heartbeat.json()["error_code"] == "LEASE_NOT_ACTIVE"
    assert old_complete.status_code == 409
    assert old_complete.json()["error_code"] == "LEASE_NOT_ACTIVE"
    assert second["status"] == "leased"
    assert second["lease_id"] != first["lease_id"]
    assert second["session"]["session_id"] != first["session"]["session_id"]
    assert second["attempt"] == 2
    assert second["session"]["step_index"] == 0


def test_waiting_runners_receive_slots_with_owner_round_robin_fairness(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            max_active_sessions_per_owner=1,
        )
    )
    episodes = [
        {
            "task_id": task_id,
            "camera_height": 16,
            "camera_width": 16,
            "max_steps": 10,
        }
        for task_id in range(2)
    ]

    with TestClient(app) as http_client:
        run_a = http_client.post(
            "/v1/runs", json={"owner_id": "user-a", "episodes": episodes}
        ).json()["run_id"]
        run_b = http_client.post(
            "/v1/runs", json={"owner_id": "user-b", "episodes": episodes}
        ).json()["run_id"]

        a1 = unpack_message(
            http_client.post(
                f"/v1/runs/{run_a}/claim", json={"runner_id": "runner-a"}
            ).content
        )
        waiting_b = unpack_message(
            http_client.post(
                f"/v1/runs/{run_b}/claim", json={"runner_id": "runner-b"}
            ).content
        )
        assert waiting_b["status"] == "queued"
        _finish_claimed_episode(http_client, a1, "runner-a", "finish-a1")

        waiting_a = unpack_message(
            http_client.post(
                f"/v1/runs/{run_a}/claim", json={"runner_id": "runner-a"}
            ).content
        )
        assert waiting_a["status"] == "queued"
        b1 = unpack_message(
            http_client.post(
                f"/v1/runs/{run_b}/claim", json={"runner_id": "runner-b"}
            ).content
        )
        assert b1["status"] == "leased"
        assert b1["job_index"] == 0
        _finish_claimed_episode(http_client, b1, "runner-b", "finish-b1")

        waiting_b_again = unpack_message(
            http_client.post(
                f"/v1/runs/{run_b}/claim", json={"runner_id": "runner-b"}
            ).content
        )
        assert waiting_b_again["status"] == "queued"
        a2 = unpack_message(
            http_client.post(
                f"/v1/runs/{run_a}/claim", json={"runner_id": "runner-a"}
            ).content
        )

    assert a1["status"] == "leased"
    assert a1["job_index"] == 0
    assert a2["status"] == "leased"
    assert a2["job_index"] == 1


def test_server_restart_requeues_in_flight_attempt_without_repeating_completed_jobs(
    tmp_path: Path,
) -> None:
    database = tmp_path / "scheduler.sqlite3"
    settings = Settings(
        environment_backend="fake",
        max_sessions=1,
        scheduler_db_path=str(database),
        worker_timeout_seconds=5.0,
    )
    run_request = {
        "owner_id": "user-a",
        "episodes": [
            {"camera_height": 16, "camera_width": 16, "max_steps": 10},
            {
                "task_id": 1,
                "camera_height": 16,
                "camera_width": 16,
                "max_steps": 10,
            },
        ],
    }

    with TestClient(create_app(settings)) as first_server:
        run_id = first_server.post("/v1/runs", json=run_request).json()["run_id"]
        first = unpack_message(
            first_server.post(
                f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
            ).content
        )
        _finish_claimed_episode(first_server, first, "runner-a", "finish-first")
        second_interrupted = unpack_message(
            first_server.post(
                f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
            ).content
        )

    with TestClient(create_app(settings)) as restarted_server:
        recovered = restarted_server.get(f"/v1/runs/{run_id}").json()
        old_heartbeat = restarted_server.post(
            f"/v1/leases/{second_interrupted['lease_id']}/heartbeat",
            json={"runner_id": "runner-a"},
        )
        retried = unpack_message(
            restarted_server.post(
                f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
            ).content
        )

    assert recovered["status"] == "queued"
    assert recovered["summary"]["completed"] == 1
    assert recovered["summary"]["queued"] == 1
    assert old_heartbeat.status_code == 409
    assert old_heartbeat.json()["error_code"] == "LEASE_NOT_ACTIVE"
    assert retried["job_index"] == 1
    assert retried["attempt"] == 2
    assert retried["session"]["session_id"] != second_interrupted["session"]["session_id"]


def test_cancelling_a_run_closes_active_sessions_and_cancels_pending_jobs(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=2,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
        )
    )
    run_request = {
        "owner_id": "user-a",
        "episodes": [
            {"camera_height": 16, "camera_width": 16, "max_steps": 10},
            {
                "task_id": 1,
                "camera_height": 16,
                "camera_width": 16,
                "max_steps": 10,
            },
        ],
    }

    with TestClient(app) as http_client:
        run_id = http_client.post("/v1/runs", json=run_request).json()["run_id"]
        claimed = unpack_message(
            http_client.post(
                f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
            ).content
        )
        cancelled = http_client.delete(f"/v1/runs/{run_id}")
        replayed = http_client.delete(f"/v1/runs/{run_id}")
        rejected_claim = http_client.post(
            f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
        )
        health = http_client.get("/v1/health").json()

    assert cancelled.status_code == 200
    assert cancelled.json() == replayed.json()
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["summary"]["cancelled"] == 2
    assert cancelled.json()["summary"]["active"] == 0
    assert rejected_claim.status_code == 409
    assert rejected_claim.json()["error_code"] == "RUN_NOT_ACTIVE"
    assert health["sessions"]["active"] == 0
    assert claimed["session"]["session_id"]


def test_per_owner_active_limit_reserves_capacity_for_other_users(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=2,
            max_active_sessions_per_owner=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
        )
    )
    episodes = [
        {
            "task_id": task_id,
            "camera_height": 16,
            "camera_width": 16,
            "max_steps": 10,
        }
        for task_id in range(2)
    ]

    with TestClient(app) as http_client:
        run_a = http_client.post(
            "/v1/runs", json={"owner_id": "user-a", "episodes": episodes}
        ).json()["run_id"]
        run_b = http_client.post(
            "/v1/runs", json={"owner_id": "user-b", "episodes": episodes[:1]}
        ).json()["run_id"]
        a1 = unpack_message(
            http_client.post(
                f"/v1/runs/{run_a}/claim", json={"runner_id": "runner-a1"}
            ).content
        )
        a2 = unpack_message(
            http_client.post(
                f"/v1/runs/{run_a}/claim", json={"runner_id": "runner-a2"}
            ).content
        )
        b1 = unpack_message(
            http_client.post(
                f"/v1/runs/{run_b}/claim", json={"runner_id": "runner-b1"}
            ).content
        )
        health = http_client.get("/v1/health").json()

    assert a1["status"] == "leased"
    assert a2["status"] == "queued"
    assert b1["status"] == "leased"
    assert health["sessions"]["active"] == 2


def test_health_reports_scheduler_queue_and_fairness_capacity(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=4,
            max_active_sessions_per_owner=2,
            scheduler_queue_capacity=3,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
        )
    )
    request = {
        "owner_id": "user-a",
        "episodes": [
            {"camera_height": 16, "camera_width": 16},
            {"task_id": 1, "camera_height": 16, "camera_width": 16},
        ],
    }

    with TestClient(app) as http_client:
        http_client.post("/v1/runs", json=request)
        health = http_client.get("/v1/health").json()

    assert health["scheduler"] == {
        "queue": {"pending": 2, "capacity": 3, "available": 1},
        "active_leases": 0,
        "waiting_runners": 0,
        "max_active_sessions_per_owner": 2,
        "direct_sessions_enabled": True,
        "persistence": "sqlite",
    }


def test_remote_run_client_executes_a_leased_episode_without_protocol_code(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
        )
    )

    with TestClient(app) as http_client:
        client = RemoteRunClient("http://testserver", http_client=http_client)
        submitted = client.submit_run(
            owner_id="private-model-user",
            episodes=[{"camera_height": 16, "camera_width": 16, "max_steps": 10}],
        )
        episode = client.claim(submitted["run_id"], runner_id="runner-1")
        assert episode is not None
        observation, info = episode.initial_observation()
        assert observation["agentview_image"].shape == (16, 16, 3)
        assert info["language_instruction"] == "fake manipulation task"

        _, _, terminated, truncated, step_info = episode.step(
            np.array([1.0, 0.0], dtype=np.float32)
        )
        completed = episode.complete()
        episode_records = client.get_episodes(submitted["run_id"])
        client.close()

    assert terminated is True
    assert truncated is False
    assert step_info["success"] is True
    assert completed["result"]["success"] is True
    assert episode_records["episodes"] == [
        {
            "job_id": episode.job_id,
            "job_index": 0,
            "status": "completed",
            "attempt": 1,
            "spec": {
                "protocol_version": "1.0",
                "suite": "libero_goal",
                "task_id": 0,
                "init_state_id": 0,
                "seed": 42,
                "variant": "base",
                "control_mode": "relative",
                "camera_names": ["agentview", "robot0_eye_in_hand"],
                "camera_height": 16,
                "camera_width": 16,
                "max_steps": 10,
                "observation_schema_version": "libero_standard_v1",
                },
                "result": completed["result"],
                "reproducibility": episode.reproducibility,
                "perturbation_plan": {
                    "case_id": "BASE",
                    "seed": 42,
                    "suite": "libero_goal",
                    "task_id": 0,
                    "version": "fake_plan_v1",
                },
            }
        ]


def test_disabling_direct_sessions_prevents_bypassing_the_scheduler(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            scheduler_db_path=str(tmp_path / "scheduler.sqlite3"),
            worker_timeout_seconds=5.0,
            allow_direct_sessions=False,
        )
    )
    episode_spec = {"camera_height": 16, "camera_width": 16, "max_steps": 10}

    with TestClient(app) as http_client:
        direct = http_client.post("/v1/sessions", json=episode_spec)
        run_id = http_client.post(
            "/v1/runs", json={"owner_id": "user-a", "episodes": [episode_spec]}
        ).json()["run_id"]
        scheduled = http_client.post(
            f"/v1/runs/{run_id}/claim", json={"runner_id": "runner-a"}
        )

    assert direct.status_code == 403
    assert direct.json()["error_code"] == "DIRECT_SESSIONS_DISABLED"
    assert scheduled.status_code == 200
    assert unpack_message(scheduled.content)["status"] == "leased"


def _finish_claimed_episode(
    http_client: TestClient,
    claimed: dict,
    runner_id: str,
    request_id: str,
) -> None:
    session = claimed["session"]
    stepped = http_client.post(
        f"/v1/sessions/{session['session_id']}/step",
        json={
            "episode_id": session["episode_id"],
            "expected_step_index": 0,
            "request_id": request_id,
            "action": [1.0, 0.0],
        },
    )
    assert stepped.status_code == 200
    completed = http_client.post(
        f"/v1/leases/{claimed['lease_id']}/complete",
        json={"runner_id": runner_id},
    )
    assert completed.status_code == 200
