"""Session lifecycle, ordering, idempotency, and worker failure handling."""

import asyncio
import hashlib
import time
import uuid
from collections import Counter
from functools import partial
from typing import Any, Callable, Dict, Optional

import numpy as np

from libero_remote.protocol.models import (
    PROTOCOL_VERSION,
    CreateSessionRequest,
    ErrorCode,
    ResetRequest,
    SessionStatus,
    StepRequest,
)
from libero_remote.worker.process import EnvWorker, WorkerError, WorkerTimeoutError

from .errors import PlatformError
from .session import CachedStep, SessionRecord

_INACTIVE_STATUSES = {
    SessionStatus.CLOSED,
    SessionStatus.EXPIRED,
    SessionStatus.FAILED,
}
_EXPIRABLE_STATUSES = {
    SessionStatus.READY,
    SessionStatus.TERMINATED,
    SessionStatus.TRUNCATED,
}
_SESSION_METADATA_KEYS = (
    "language_instruction",
    "action_schema",
    "observation_schema_version",
    "observation_schema",
)


class SessionManager:
    def __init__(
        self,
        backend: str,
        max_sessions: int = 1,
        worker_timeout_seconds: float = 60.0,
        request_cache_size: int = 16,
        session_idle_timeout_seconds: float = 900.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._backend = backend
        self._max_sessions = max_sessions
        self._worker_timeout_seconds = worker_timeout_seconds
        self._request_cache_size = request_cache_size
        self._session_idle_timeout_seconds = session_idle_timeout_seconds
        self._clock = clock
        self._sessions: Dict[str, SessionRecord] = {}
        self._registry_lock = asyncio.Lock()

    async def create(self, request: CreateSessionRequest) -> Dict[str, Any]:
        async with self._registry_lock:
            active_count = sum(
                record.status not in _INACTIVE_STATUSES for record in self._sessions.values()
            )
            if active_count >= self._max_sessions:
                raise PlatformError(
                    ErrorCode.SESSION_CAPACITY_REACHED,
                    "The server has no available environment capacity",
                    status_code=503,
                )

            session_id = f"ses_{uuid.uuid4().hex}"
            episode_id = f"ep_{uuid.uuid4().hex}"
            worker = EnvWorker.start(self._backend, self._worker_timeout_seconds)
            record = SessionRecord(
                session_id=session_id,
                worker=worker,
                spec=request.dict(),
                episode_id=episode_id,
                status=SessionStatus.CREATING,
                last_activity_at=self._clock(),
            )
            self._sessions[session_id] = record

        try:
            created = await _run_blocking(worker.create, request.dict())
        except Exception as error:
            worker.terminate()
            async with self._registry_lock:
                self._sessions.pop(session_id, None)
            raise PlatformError(
                ErrorCode.ENVIRONMENT_CREATION_FAILED,
                "The environment could not be initialized",
                status_code=500,
                details={"cause": str(error)},
            ) from error

        record.status = SessionStatus.READY
        record.last_activity_at = self._clock()
        record.spec["_action_schema"] = created["action_schema"]
        record.spec["_session_metadata"] = {key: created[key] for key in _SESSION_METADATA_KEYS}
        record.last_committed = None
        return {
            "protocol_version": PROTOCOL_VERSION,
            "session_id": session_id,
            "episode_id": episode_id,
            "status": record.status.value,
            "step_index": 0,
            "suite": request.suite,
            "task_id": request.task_id,
            **created,
        }

    async def reset(self, session_id: str, request: ResetRequest) -> Dict[str, Any]:
        record = self._get_record(session_id)
        async with record.lock:
            self._require_usable(record)
            try:
                reset = await _run_blocking(
                    record.worker.reset, request.init_state_id, request.seed
                )
            except WorkerError as error:
                self._fail_worker(record, error)
            record.episode_id = f"ep_{uuid.uuid4().hex}"
            record.next_step_index = 0
            record.cache.clear()
            record.last_committed = None
            record.status = SessionStatus.READY
            record.last_activity_at = self._clock()
            record.spec["init_state_id"] = request.init_state_id
            record.spec["seed"] = request.seed
            return {
                "protocol_version": PROTOCOL_VERSION,
                "session_id": record.session_id,
                "episode_id": record.episode_id,
                "status": record.status.value,
                "step_index": 0,
                **record.spec["_session_metadata"],
                **reset,
            }

    async def step(self, session_id: str, request: StepRequest) -> Dict[str, Any]:
        record = self._get_record(session_id)
        async with record.lock:
            self._require_usable(record)
            if request.episode_id != record.episode_id:
                raise PlatformError(
                    ErrorCode.STALE_EPISODE,
                    "The step belongs to an inactive episode",
                    status_code=409,
                    request_id=request.request_id,
                )

            action = self._validate_action(record, request)
            action_hash = hashlib.sha256(action.tobytes(order="C")).hexdigest()
            cached = record.cache.get(request.request_id)
            if cached is not None:
                if (
                    cached.episode_id != request.episode_id
                    or cached.expected_step_index != request.expected_step_index
                    or cached.action_hash != action_hash
                ):
                    raise PlatformError(
                        ErrorCode.REQUEST_ID_CONFLICT,
                        "The request_id was already used with a different action",
                        status_code=409,
                        request_id=request.request_id,
                    )
                record.last_activity_at = self._clock()
                return cached.response

            if request.expected_step_index < record.next_step_index:
                raise PlatformError(
                    ErrorCode.DUPLICATE_OR_EXPIRED_STEP,
                    "The requested step has already been committed and is no longer cached",
                    status_code=409,
                    request_id=request.request_id,
                )
            if request.expected_step_index > record.next_step_index:
                raise PlatformError(
                    ErrorCode.OUT_OF_ORDER_STEP,
                    "The requested step is ahead of the environment",
                    status_code=409,
                    request_id=request.request_id,
                )
            if record.status in {SessionStatus.TERMINATED, SessionStatus.TRUNCATED}:
                raise PlatformError(
                    ErrorCode.EPISODE_NOT_ACTIVE,
                    "Reset the session before sending another action",
                    status_code=409,
                    request_id=request.request_id,
                )

            record.status = SessionStatus.STEPPING
            started_at = time.perf_counter()
            try:
                result = await _run_blocking(record.worker.step, action)
            except WorkerError as error:
                self._fail_worker(record, error, request.request_id)

            committed_index = record.next_step_index
            record.next_step_index += 1
            if result.get("terminated"):
                record.status = SessionStatus.TERMINATED
            elif result.get("truncated"):
                record.status = SessionStatus.TRUNCATED
            else:
                record.status = SessionStatus.READY
            response = {
                "protocol_version": PROTOCOL_VERSION,
                "session_id": record.session_id,
                "episode_id": record.episode_id,
                "request_id": request.request_id,
                "step_index": committed_index,
                "next_step_index": record.next_step_index,
                "status": record.status.value,
                "server_step_seconds": time.perf_counter() - started_at,
                **result,
            }
            cached_step = CachedStep(
                episode_id=record.episode_id,
                expected_step_index=committed_index,
                action_hash=action_hash,
                response=response,
            )
            record.cache[request.request_id] = cached_step
            record.cache.move_to_end(request.request_id)
            while len(record.cache) > self._request_cache_size:
                record.cache.popitem(last=False)
            record.last_committed = response
            record.last_activity_at = self._clock()
            return response

    async def get(self, session_id: str) -> Dict[str, Any]:
        record = self._get_record(session_id)
        async with record.lock:
            if record.status not in _INACTIVE_STATUSES:
                record.last_activity_at = self._clock()
            return record.snapshot()

    async def close(self, session_id: str) -> None:
        record = self._get_record(session_id)
        async with record.lock:
            if record.status == SessionStatus.CLOSED:
                return
            await _run_blocking(record.worker.close)
            record.status = SessionStatus.CLOSED

    async def close_all(self) -> None:
        for session_id in list(self._sessions):
            try:
                await self.close(session_id)
            except Exception:
                pass

    async def expire_idle_sessions(self) -> int:
        now = self._clock()
        expired = 0
        for record in list(self._sessions.values()):
            if record.status not in _EXPIRABLE_STATUSES:
                continue
            if now - record.last_activity_at <= self._session_idle_timeout_seconds:
                continue
            async with record.lock:
                if record.status not in _EXPIRABLE_STATUSES:
                    continue
                if now - record.last_activity_at <= self._session_idle_timeout_seconds:
                    continue
                try:
                    await _run_blocking(record.worker.close)
                except Exception:
                    record.worker.terminate()
                record.status = SessionStatus.EXPIRED
                expired += 1
        return expired

    def capacity_snapshot(self) -> Dict[str, Any]:
        by_status = Counter(record.status.value for record in self._sessions.values())
        active = sum(
            count
            for status, count in by_status.items()
            if SessionStatus(status) not in _INACTIVE_STATUSES
        )
        return {
            "active": active,
            "capacity": self._max_sessions,
            "available": max(0, self._max_sessions - active),
            "by_status": dict(sorted(by_status.items())),
        }

    def task_catalog(self) -> Dict[str, Any]:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "backend": self._backend,
            "suites": ["libero_goal", "libero_spatial", "libero_object", "libero_10"],
            "observation_schema_versions": ["libero_standard_v1"],
            "variants": ["base"],
            "control_modes": ["relative", "absolute"],
        }

    def _get_record(self, session_id: str) -> SessionRecord:
        record: Optional[SessionRecord] = self._sessions.get(session_id)
        if record is None:
            raise PlatformError(
                ErrorCode.SESSION_NOT_FOUND,
                "The requested session does not exist",
                status_code=404,
            )
        return record

    @staticmethod
    def _require_usable(record: SessionRecord) -> None:
        if record.status in _INACTIVE_STATUSES:
            raise PlatformError(
                ErrorCode.SESSION_NOT_ACTIVE,
                "The session can no longer execute environment operations",
                status_code=410 if record.status == SessionStatus.EXPIRED else 409,
            )

    @staticmethod
    def _validate_action(record: SessionRecord, request: StepRequest) -> np.ndarray:
        schema = record.last_committed.get("action_schema") if record.last_committed else None
        if schema is None:
            schema = getattr(record, "action_schema", None)
        if schema is None:
            schema = record.spec.get("action_schema")
        # Creation metadata is stored on the record after the first response.
        if schema is None:
            schema = record.spec.get("_action_schema")
        if schema is None:
            raise PlatformError(ErrorCode.INTERNAL_ERROR, "Action schema is unavailable", 500)

        action = np.ascontiguousarray(request.action, dtype=np.float32)
        expected_shape = tuple(schema["shape"])
        low = np.asarray(schema["low"], dtype=np.float32)
        high = np.asarray(schema["high"], dtype=np.float32)
        if action.shape != expected_shape or not np.isfinite(action).all():
            raise PlatformError(
                ErrorCode.INVALID_ACTION,
                "Action shape or values do not match the environment schema",
                status_code=400,
                request_id=request.request_id,
            )
        if np.any(action < low) or np.any(action > high):
            raise PlatformError(
                ErrorCode.INVALID_ACTION,
                "Action is outside the environment bounds",
                status_code=400,
                request_id=request.request_id,
            )
        return action

    @staticmethod
    def _fail_worker(
        record: SessionRecord, error: WorkerError, request_id: Optional[str] = None
    ) -> None:
        record.worker.terminate()
        record.status = SessionStatus.FAILED
        code = (
            ErrorCode.WORKER_TIMEOUT
            if isinstance(error, WorkerTimeoutError)
            else ErrorCode.WORKER_FAILED
        )
        raise PlatformError(
            code,
            "The environment worker failed; the current episode cannot be resumed",
            status_code=500,
            request_id=request_id,
            details={"cause": str(error)},
        ) from error


async def _run_blocking(function: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a worker IPC call without blocking the Python 3.8 event loop."""

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(function, *args, **kwargs))
