"""Gym-style client interface for a server-hosted LIBERO environment."""

import uuid
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .transport import HttpTransport


class RemoteLiberoEnv:
    def __init__(
        self,
        base_url: str,
        timeout: float = 60.0,
        http_client: Optional[Any] = None,
    ) -> None:
        self._transport = HttpTransport(base_url, timeout, http_client)
        self.session_id: Optional[str] = None
        self.episode_id: Optional[str] = None
        self.next_step_index = 0
        self.action_schema: Optional[Dict[str, Any]] = None

    def reset(
        self,
        suite: Optional[str] = None,
        task_id: Optional[int] = None,
        init_state_id: int = 0,
        seed: int = 42,
        **options: Any,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        if self.session_id is None:
            body = {
                "protocol_version": "1.0",
                "suite": suite or "libero_goal",
                "task_id": 0 if task_id is None else task_id,
                "init_state_id": init_state_id,
                "seed": seed,
                **options,
            }
            response = self._transport.post("/v1/sessions", body)
            self.session_id = str(response["session_id"])
            self.action_schema = response.get("action_schema")
        else:
            if suite is not None or task_id is not None:
                raise ValueError("suite and task_id are fixed for the lifetime of a session")
            response = self._transport.post(
                f"/v1/sessions/{self.session_id}/reset",
                {"init_state_id": init_state_id, "seed": seed},
            )
        self.episode_id = str(response["episode_id"])
        self.next_step_index = 0
        return response["observation"], _reset_info(response)

    def step(
        self, action: np.ndarray, request_id: Optional[str] = None
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        if self.session_id is None or self.episode_id is None:
            raise RuntimeError("Call reset() before step()")
        body = {
            "episode_id": self.episode_id,
            "expected_step_index": self.next_step_index,
            "request_id": request_id or f"req_{uuid.uuid4().hex}",
            "action": np.asarray(action, dtype=np.float32).tolist(),
        }
        response = self._transport.post_idempotent(
            f"/v1/sessions/{self.session_id}/step", body
        )
        self.next_step_index = int(response["next_step_index"])
        info = dict(response.get("info", {}))
        info.update(
            {
                "request_id": response["request_id"],
                "step_index": response["step_index"],
                "success": response["success"],
                "server_step_seconds": response["server_step_seconds"],
            }
        )
        return (
            response["observation"],
            float(response["reward"]),
            bool(response["terminated"]),
            bool(response["truncated"]),
            info,
        )

    def close(self) -> None:
        session_id, self.session_id = self.session_id, None
        self.episode_id = None
        self.next_step_index = 0
        self.action_schema = None
        if session_id is not None:
            self._transport.delete(f"/v1/sessions/{session_id}")

    def close_transport(self) -> None:
        self.close()
        self._transport.close()

    def __enter__(self) -> "RemoteLiberoEnv":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close_transport()


def _reset_info(response: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: response[key]
        for key in (
            "session_id",
            "episode_id",
            "language_instruction",
            "action_schema",
            "observation_schema_version",
            "observation_schema",
        )
        if key in response
    }
