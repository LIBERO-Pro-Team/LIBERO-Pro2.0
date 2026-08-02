import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pytest
from fastapi.testclient import TestClient

from libero_remote import RemoteRunClient
from libero_remote.runner.scheduled import (
    AgentContext,
    run_leased_episode,
    run_scheduled_run,
)
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings


class SlowPrivateAgent:
    def __init__(self) -> None:
        self.context: AgentContext
        self.closed = False

    def reset(self, context: AgentContext) -> None:
        self.context = context

    def act(self, observation: Dict[str, np.ndarray]) -> np.ndarray:
        assert observation["agentview_image"].shape == (16, 16, 3)
        assert observation["instruction"] == "fake manipulation task"
        assert observation["step_index"] == 0
        time.sleep(0.12)
        return np.array([1.0, 0.0], dtype=np.float32)

    def close(self) -> None:
        self.closed = True


class FailingPrivateAgent(SlowPrivateAgent):
    def act(self, observation: Dict[str, np.ndarray]) -> np.ndarray:
        del observation
        raise RuntimeError("private model inference failed")


class ReusablePrivateAgent(SlowPrivateAgent):
    def __init__(self) -> None:
        super().__init__()
        self.reset_count = 0

    def reset(self, context: AgentContext) -> None:
        super().reset(context)
        self.reset_count += 1

    def act(self, observation: Dict[str, np.ndarray]) -> np.ndarray:
        del observation
        return np.array([1.0, 0.0], dtype=np.float32)


class FakeLeasedEpisode:
    run_id = "run-test"
    job_id = "job-test"
    job_index = 0
    lease_id = "lease-test"
    heartbeat_interval_seconds = 0.02
    episode_spec = {
        "suite": "libero_goal",
        "task_id": 0,
        "init_state_id": 0,
        "seed": 142,
        "control_mode": "relative",
    }
    reproducibility = {
        "job_fingerprint": "job-hash",
        "runtime_fingerprint": "runtime-hash",
        "initial_state_fingerprint": "state-hash",
    }

    def __init__(self) -> None:
        self.heartbeat_count = 0

    def initial_observation(self) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        return {
            "agentview_image": np.zeros((16, 16, 3), dtype=np.uint8)
        }, {
            "language_instruction": "fake manipulation task",
            "action_schema": {
                "shape": [2],
                "low": [-1.0, -1.0],
                "high": [1.0, 1.0],
            },
            "observation_schema_version": "libero_standard_v1",
        }

    def step(
        self, action: np.ndarray, request_id: Optional[str] = None
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        del action, request_id
        observation, _ = self.initial_observation()
        return observation, 1.0, True, False, {"success": True}

    def heartbeat(self) -> Dict[str, Any]:
        self.heartbeat_count += 1
        return {"status": "active"}

    def complete(self) -> Dict[str, Any]:
        return {"status": "completed", "result": {"success": True}}

    def abandon(self) -> Dict[str, Any]:
        return {"status": "queued"}


def test_generic_runner_heartbeats_while_private_model_inference_is_blocked(
) -> None:
    agent = SlowPrivateAgent()
    episode = FakeLeasedEpisode()
    result = run_leased_episode(episode, agent)

    assert result["result"]["success"] is True
    assert episode.heartbeat_count >= 3
    assert agent.context.language_instruction == "fake manipulation task"
    assert agent.context.episode_spec["seed"] == 142
    assert agent.context.reproducibility["job_fingerprint"] == "job-hash"
    assert agent.closed is True


def test_generic_runner_fails_job_without_retry_when_adapter_fails(
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
    agent = FailingPrivateAgent()

    with TestClient(app) as http_client:
        client = RemoteRunClient("http://testserver", http_client=http_client)
        run = client.submit_run(
            "private-user",
            [{"camera_height": 16, "camera_width": 16, "max_steps": 10}],
        )
        episode = client.claim(run["run_id"], "private-runner")
        assert episode is not None
        with pytest.raises(RuntimeError, match="private model inference failed"):
            run_leased_episode(episode, agent)
        snapshot = client.get_run(run["run_id"])
        health = http_client.get("/v1/health").json()
        client.close()

    assert snapshot["status"] == "failed"
    assert snapshot["summary"]["failed"] == 1
    assert snapshot["summary"]["active"] == 0
    assert health["sessions"]["active"] == 0
    assert agent.closed is True


def test_generic_runner_rejects_adapter_action_outside_server_schema() -> None:
    class InvalidActionAgent(SlowPrivateAgent):
        def act(self, observation: Dict[str, np.ndarray]) -> np.ndarray:
            del observation
            return np.array([2.0, 0.0], dtype=np.float32)

    agent = InvalidActionAgent()
    episode = FakeLeasedEpisode()

    with pytest.raises(ValueError, match="outside server bounds"):
        run_leased_episode(episode, agent)

    assert agent.closed is True


def test_generic_runner_rejects_incomplete_server_action_schema() -> None:
    class IncompleteSchemaEpisode(FakeLeasedEpisode):
        def initial_observation(
            self,
        ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
            observation, info = super().initial_observation()
            info["action_schema"] = {"shape": [2]}
            return observation, info

    agent = SlowPrivateAgent()

    with pytest.raises(RuntimeError, match="missing fields"):
        run_leased_episode(IncompleteSchemaEpisode(), agent)

    assert agent.closed is True


def test_scheduled_run_reuses_one_private_adapter_for_all_episodes(
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
    agent = ReusablePrivateAgent()
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
        client = RemoteRunClient("http://testserver", http_client=http_client)
        run = client.submit_run("private-user", episodes)
        result = run_scheduled_run(client, run["run_id"], "private-runner", agent)
        client.close()

    assert result["status"] == "completed"
    assert result["summary"]["completed"] == 2
    assert agent.reset_count == 2
    assert agent.closed is True
