"""Model-agnostic runner for server-scheduled remote episodes."""

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, Tuple

import numpy as np

from libero_remote.client.run_client import RemoteRunClient
from libero_remote.runner.agent import validate_action


@dataclass(frozen=True)
class AgentContext:
    run_id: str
    job_id: str
    job_index: int
    episode_spec: Dict[str, Any]
    reproducibility: Dict[str, str]
    language_instruction: str
    action_schema: Dict[str, Any]
    observation_schema_version: str


class AgentAdapter(Protocol):
    def reset(self, context: AgentContext) -> None:
        """Prepare model state for one independently reset episode."""

    def act(self, observation: Dict[str, np.ndarray]) -> np.ndarray:
        """Convert one platform observation into one platform action."""

    def close(self) -> None:
        """Release model-side resources owned by the adapter."""


class LeasedEpisode(Protocol):
    @property
    def run_id(self) -> str:
        ...

    @property
    def job_id(self) -> str:
        ...

    @property
    def job_index(self) -> int:
        ...

    @property
    def lease_id(self) -> str:
        ...

    @property
    def heartbeat_interval_seconds(self) -> float:
        ...

    @property
    def episode_spec(self) -> Dict[str, Any]:
        ...

    @property
    def reproducibility(self) -> Dict[str, str]:
        ...

    def initial_observation(self) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        ...

    def step(
        self, action: np.ndarray, request_id: Optional[str] = None
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        ...

    def heartbeat(self) -> Dict[str, Any]:
        ...

    def complete(self) -> Dict[str, Any]:
        ...

    def abandon(self) -> Dict[str, Any]:
        ...


def run_leased_episode(
    episode: LeasedEpisode,
    adapter: AgentAdapter,
    close_adapter: bool = True,
) -> Dict[str, Any]:
    """Run one lease while heartbeat traffic is independent of model latency."""

    observation, info = episode.initial_observation()
    instruction = str(info["language_instruction"])
    context = AgentContext(
        run_id=episode.run_id,
        job_id=episode.job_id,
        job_index=episode.job_index,
        episode_spec=episode.episode_spec,
        reproducibility=episode.reproducibility,
        language_instruction=instruction,
        action_schema=dict(info["action_schema"]),
        observation_schema_version=str(info["observation_schema_version"]),
    )
    heartbeat = _HeartbeatLoop(episode)
    heartbeat.start()
    try:
        adapter.reset(context)
        step_index = 0
        while True:
            heartbeat.raise_if_failed()
            adapter_observation = dict(observation)
            adapter_observation["instruction"] = instruction
            adapter_observation["step_index"] = step_index
            action = validate_action(
                adapter.act(adapter_observation), context.action_schema
            )
            heartbeat.raise_if_failed()
            observation, _, terminated, truncated, step_info = episode.step(action)
            instruction = str(
                step_info.get("language_instruction", instruction)
            )
            step_index += 1
            if terminated or truncated:
                break
        heartbeat.stop()
        heartbeat.raise_if_failed()
        return episode.complete()
    except BaseException:
        heartbeat.stop()
        try:
            episode.abandon()
        except BaseException:
            pass
        raise
    finally:
        heartbeat.stop()
        if close_adapter:
            adapter.close()


def run_scheduled_run(
    client: RemoteRunClient,
    run_id: str,
    runner_id: str,
    adapter: AgentAdapter,
    poll_interval_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    """Claim a run's remaining work while loading one model adapter only once."""

    terminal_statuses = {"completed", "failed", "cancelled"}
    try:
        while True:
            snapshot = client.get_run(run_id)
            if snapshot["status"] in terminal_statuses:
                return snapshot
            episode = client.claim(run_id, runner_id)
            if episode is None:
                delay = poll_interval_seconds
                if delay is None:
                    delay = client.last_retry_after_seconds or 1.0
                time.sleep(delay)
                continue
            run_leased_episode(episode, adapter, close_adapter=False)
    finally:
        adapter.close()


class _HeartbeatLoop:
    def __init__(self, episode: LeasedEpisode) -> None:
        self._episode = episode
        self._stop = threading.Event()
        self._failure: Optional[BaseException] = None
        self._thread = threading.Thread(
            target=self._run,
            name=f"libero-lease-heartbeat-{episode.lease_id}",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=max(1.0, self._episode.heartbeat_interval_seconds * 2))

    def raise_if_failed(self) -> None:
        if self._failure is not None:
            raise RuntimeError("The episode lease heartbeat failed") from self._failure

    def _run(self) -> None:
        interval = self._episode.heartbeat_interval_seconds
        while not self._stop.wait(interval):
            try:
                self._episode.heartbeat()
            except BaseException as error:
                self._failure = error
                self._stop.set()
                return
