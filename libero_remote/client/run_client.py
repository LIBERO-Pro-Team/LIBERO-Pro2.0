"""User-side client for scheduled runs and leased remote episodes."""

import uuid
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np

from .transport import HttpTransport


class RemoteRunClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 60.0,
        http_client: Optional[Any] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self._transport = HttpTransport(base_url, timeout, http_client, api_key)
        self.last_retry_after_seconds: Optional[float] = None

    def submit_run(
        self,
        episodes_or_owner: Any = None,
        episodes: Optional[Sequence[Dict[str, Any]]] = None,
        *,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit episodes; authenticated servers derive owner from the API key."""

        if episodes is None:
            if episodes_or_owner is None:
                raise TypeError("episodes are required")
            selected_episodes = episodes_or_owner
            legacy_owner = owner_id
        else:
            selected_episodes = episodes
            legacy_owner = owner_id if episodes_or_owner is None else str(episodes_or_owner)
        body: Dict[str, Any] = {"episodes": list(selected_episodes)}
        if legacy_owner is not None:
            body["owner_id"] = legacy_owner
        return self._transport.post("/v1/runs", body)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._transport.get_json(f"/v1/runs/{run_id}")

    def get_episodes(self, run_id: str) -> Dict[str, Any]:
        return self._transport.get_json(f"/v1/runs/{run_id}/episodes")

    def claim(
        self, run_id: str, runner_id: str
    ) -> Optional["LeasedRemoteLiberoEnv"]:
        response = self._transport.post(
            f"/v1/runs/{run_id}/claim", {"runner_id": runner_id}
        )
        if response["status"] == "queued":
            self.last_retry_after_seconds = float(response["retry_after_seconds"])
            return None
        self.last_retry_after_seconds = None
        return LeasedRemoteLiberoEnv(self._transport, runner_id, response)

    def cancel_run(self, run_id: str) -> Dict[str, Any]:
        return self._transport.delete_json(f"/v1/runs/{run_id}")

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "RemoteRunClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class LeasedRemoteLiberoEnv:
    def __init__(
        self,
        transport: HttpTransport,
        runner_id: str,
        claim: Dict[str, Any],
    ) -> None:
        self._transport = transport
        self._runner_id = runner_id
        self._claim = claim
        self._session = claim["session"]
        self._next_step_index = int(self._session["step_index"])
        self._finished = False

    @property
    def run_id(self) -> str:
        return str(self._claim["run_id"])

    @property
    def job_id(self) -> str:
        return str(self._claim["job_id"])

    @property
    def job_index(self) -> int:
        return int(self._claim["job_index"])

    @property
    def lease_id(self) -> str:
        return str(self._claim["lease_id"])

    @property
    def action_schema(self) -> Dict[str, Any]:
        return dict(self._session["action_schema"])

    @property
    def episode_spec(self) -> Dict[str, Any]:
        return dict(self._claim["episode_spec"])

    @property
    def reproducibility(self) -> Dict[str, str]:
        return dict(self._claim["reproducibility"])

    @property
    def heartbeat_interval_seconds(self) -> float:
        return float(self._claim["heartbeat_interval_seconds"])

    def initial_observation(self) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        return self._session["observation"], {
            key: self._session[key]
            for key in (
                "session_id",
                "episode_id",
                "language_instruction",
                "action_schema",
                "observation_schema_version",
                "observation_schema",
            )
            if key in self._session
        }

    def step(
        self, action: np.ndarray, request_id: Optional[str] = None
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        if self._finished:
            raise RuntimeError("The leased episode has already been completed")
        response = self._transport.post(
            f"/v1/sessions/{self._session['session_id']}/step",
            {
                "episode_id": self._session["episode_id"],
                "expected_step_index": self._next_step_index,
                "request_id": request_id or f"req_{uuid.uuid4().hex}",
                "lease_id": self.lease_id,
                "lease_generation": int(self._claim["lease_generation"]),
                "action": np.asarray(action, dtype=np.float32).tolist(),
            },
        )
        self._next_step_index = int(response["next_step_index"])
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

    def heartbeat(self) -> Dict[str, Any]:
        if self._finished:
            raise RuntimeError("The leased episode has already been completed")
        response = self._transport.post(
            f"/v1/leases/{self.lease_id}/heartbeat",
            {
                "runner_id": self._runner_id,
                "lease_generation": int(self._claim["lease_generation"]),
            },
        )
        self._claim["lease_expires_at"] = response["lease_expires_at"]
        return response

    def complete(self) -> Dict[str, Any]:
        response = self._transport.post(
            f"/v1/leases/{self.lease_id}/complete",
            {
                "runner_id": self._runner_id,
                "lease_generation": int(self._claim["lease_generation"]),
            },
        )
        self._finished = True
        return response

    def abandon(self) -> Dict[str, Any]:
        response = self._transport.post(
            f"/v1/leases/{self.lease_id}/abandon",
            {
                "runner_id": self._runner_id,
                "lease_generation": int(self._claim["lease_generation"]),
            },
        )
        self._finished = True
        return response
