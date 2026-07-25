"""Mutable session record protected by a per-session lock."""

import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from libero_remote.protocol.models import SessionStatus
from libero_remote.worker.process import EnvWorker


@dataclass
class CachedStep:
    episode_id: str
    expected_step_index: int
    action_hash: str
    response: Dict[str, Any]


@dataclass
class SessionRecord:
    session_id: str
    worker: EnvWorker
    spec: Dict[str, Any]
    episode_id: str
    status: SessionStatus
    last_activity_at: float
    next_step_index: int = 0
    last_committed: Optional[Dict[str, Any]] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cache: "OrderedDict[str, CachedStep]" = field(default_factory=OrderedDict)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "worker_pid": self.worker.pid,
            "status": self.status.value,
            "episode_id": self.episode_id,
            "next_step_index": self.next_step_index,
            "suite": self.spec["suite"],
            "task_id": self.spec["task_id"],
            "last_request_id": (
                self.last_committed.get("request_id") if self.last_committed else None
            ),
        }
