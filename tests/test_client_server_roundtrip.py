import json
import logging
import time
from typing import Any

import numpy as np
from fastapi.testclient import TestClient

from libero_remote import RemoteLiberoEnv
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings


def test_client_can_reset_step_and_close_a_remote_environment() -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            worker_timeout_seconds=5.0,
        )
    )
    with TestClient(app) as http_client:
        env = RemoteLiberoEnv(
            base_url="http://testserver",
            http_client=http_client,
        )
        observation, info = env.reset(
            suite="libero_goal",
            task_id=0,
            init_state_id=0,
            seed=42,
            control_mode="absolute",
            camera_height=16,
            camera_width=16,
            max_steps=10,
        )
        assert observation["agentview_image"].shape == (16, 16, 3)
        assert info["language_instruction"] == "fake manipulation task"
        assert info["action_schema"]["control_mode"] == "absolute"

        observation, reward, terminated, truncated, info = env.step(
            np.array([0.25, 0.0], dtype=np.float32)
        )
        assert observation["robot0_joint_pos"][0] == np.float32(0.25)
        assert reward == 0.0
        assert not terminated
        assert not truncated
        assert info["step_index"] == 0

        _, reset_info = env.reset(init_state_id=1, seed=7)
        assert reset_info["language_instruction"] == "fake manipulation task"
        assert reset_info["action_schema"] == env.action_schema
        assert reset_info["observation_schema_version"] == "libero_standard_v1"

        env.close()
        assert env.session_id is None


def test_health_reports_backend_readiness_and_capacity() -> None:
    app = create_app(Settings(environment_backend="fake", max_sessions=2))

    with TestClient(app) as http_client:
        response = http_client.get("/v1/health")

    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["backend"] == {"name": "fake", "ready": True}
    assert payload["sessions"] == {
        "active": 0,
        "capacity": 2,
        "available": 2,
        "by_status": {},
    }
    assert set(payload["runtime"]) == {
        "service",
        "libero",
        "packages",
        "python",
        "os",
        "gpu",
        "egl",
    }
    assert len(payload["runtime"]["service"]["commit"]) == 40
    assert "robosuite" in payload["runtime"]["packages"]
    assert "mujoco" in payload["runtime"]["packages"]
    assert payload["runtime"]["python"]["version"]
    assert "driver_version" in payload["runtime"]["gpu"]
    assert "MUJOCO_GL" in payload["runtime"]["egl"]


def test_task_catalog_advertises_supported_control_modes() -> None:
    app = create_app(Settings(environment_backend="fake"))

    with TestClient(app) as http_client:
        response = http_client.get("/v1/tasks")

    assert response.status_code == 200
    assert response.json()["control_modes"] == ["relative", "absolute"]


def test_lifespan_cleanup_expires_an_idle_session() -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            worker_timeout_seconds=5.0,
            session_idle_timeout_seconds=0.05,
            cleanup_interval_seconds=0.01,
        )
    )

    with TestClient(app) as http_client:
        env = RemoteLiberoEnv(base_url="http://testserver", http_client=http_client)
        env.reset(camera_height=16, camera_width=16, max_steps=10)
        session_id = env.session_id
        time.sleep(0.15)

        response = http_client.get(f"/v1/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "expired"
        env.close()


def test_server_emits_structured_audit_events(caplog: Any) -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            max_sessions=1,
            worker_timeout_seconds=5.0,
        )
    )

    audit_logger = logging.getLogger("libero_remote.audit")
    audit_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="libero_remote.audit"):
            with TestClient(app) as http_client:
                env = RemoteLiberoEnv(base_url="http://testserver", http_client=http_client)
                env.reset(camera_height=16, camera_width=16, max_steps=10)
                env.step(np.array([0.25, 0.0], dtype=np.float32))
                env.close()
    finally:
        audit_logger.removeHandler(caplog.handler)

    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "libero_remote.audit"
    ]
    by_name = {event["event"]: event for event in events}
    committed = by_name["step_committed"]

    assert {"session_created", "step_committed", "session_closed"} <= set(by_name)
    assert committed["audit_schema_version"] == "1.0"
    assert committed["request_id"].startswith("req_")
    assert committed["expected_step_index"] == 0
    assert committed["step_index"] == 0
    assert len(committed["action_sha256"]) == 64
    assert committed["server_step_seconds"] >= 0.0
    assert committed["success"] is False
    assert "action" not in committed
    assert "observation" not in committed
