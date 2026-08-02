"""Session lifecycle, ordering, idempotency, and worker failure handling."""

import asyncio
import hashlib
import time
import uuid
from collections import Counter
from functools import partial
from typing import Any, Callable, Dict, Optional

import numpy as np

from libero_remote.environment.task_manifest import TaskManifest
from libero_remote.protocol.models import (
    PROTOCOL_VERSION,
    CreateSessionRequest,
    ErrorCode,
    ResetRequest,
    SessionStatus,
    StepRequest,
)
from libero_remote.worker.process import EnvWorker, WorkerError, WorkerTimeoutError

from .audit import emit_audit
from .errors import PlatformError
from .session import CachedError, CachedStep, SessionRecord

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
        max_active_sessions_per_owner: Optional[int] = None,
        task_manifest: Optional[TaskManifest] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._backend = backend
        self._max_sessions = max_sessions
        self._worker_timeout_seconds = worker_timeout_seconds
        self._request_cache_size = request_cache_size
        self._session_idle_timeout_seconds = session_idle_timeout_seconds
        self._max_active_sessions_per_owner = max_active_sessions_per_owner
        self._task_manifest = task_manifest
        self._clock = clock
        self._sessions: Dict[str, SessionRecord] = {}
        self._registry_lock = asyncio.Lock()

    async def create(
        self, request: CreateSessionRequest, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        worker_spec = request.dict()
        if self._task_manifest is not None:
            worker_spec["_bddl_path"] = str(
                self._task_manifest.resolve_bddl(
                    request.suite, request.task_id, request.variant
                )
            )
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
            if owner_id is not None and self._max_active_sessions_per_owner is not None:
                owner_active = sum(
                    record.owner_id == owner_id
                    and record.status not in _INACTIVE_STATUSES
                    for record in self._sessions.values()
                )
                if owner_active >= self._max_active_sessions_per_owner:
                    raise PlatformError(
                        ErrorCode.SESSION_CAPACITY_REACHED,
                        "The account has reached its active environment quota",
                        status_code=503,
                    )

            session_id = f"ses_{uuid.uuid4().hex}"
            episode_id = f"ep_{uuid.uuid4().hex}"
            worker = EnvWorker.start(self._backend, self._worker_timeout_seconds)
            record = SessionRecord(
                session_id=session_id,
                owner_id=owner_id,
                worker=worker,
                spec=request.dict(),
                episode_id=episode_id,
                status=SessionStatus.CREATING,
                last_activity_at=self._clock(),
            )
            self._sessions[session_id] = record

        try:
            created = await _run_blocking(worker.create, worker_spec)
        except Exception as error:
            worker.terminate()
            async with self._registry_lock:
                self._sessions.pop(session_id, None)
            emit_audit(
                "environment_creation_failed",
                session_id=session_id,
                episode_id=episode_id,
                worker_pid=worker.pid,
                suite=request.suite,
                task_id=request.task_id,
                error_code=ErrorCode.ENVIRONMENT_CREATION_FAILED.value,
                cause=str(error),
                status=SessionStatus.FAILED.value,
            )
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
        response = {
            "protocol_version": PROTOCOL_VERSION,
            "session_id": session_id,
            "episode_id": episode_id,
            "status": record.status.value,
            "step_index": 0,
            "suite": request.suite,
            "task_id": request.task_id,
            **created,
        }
        emit_audit(
            "session_created",
            session_id=session_id,
            episode_id=episode_id,
            worker_pid=worker.pid,
            suite=request.suite,
            task_id=request.task_id,
            init_state_id=request.init_state_id,
            seed=request.seed,
            variant=request.variant,
            control_mode=request.control_mode,
            observation_schema_version=created["observation_schema_version"],
            action_schema_version=created["action_schema"]["version"],
            status=record.status.value,
        )
        return response

    async def reset(
        self, session_id: str, request: ResetRequest, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        record = self._get_record(session_id, owner_id)
        async with record.lock:
            self._require_usable(record)
            previous_episode_id = record.episode_id
            try:
                reset = await _run_blocking(
                    record.worker.reset, request.init_state_id, request.seed
                )
            except WorkerError as error:
                platform_error = self._mark_worker_failed(record, error, operation="reset")
                raise platform_error from error
            record.episode_id = f"ep_{uuid.uuid4().hex}"
            record.next_step_index = 0
            record.cache.clear()
            record.last_committed = None
            record.action_chain_hash = hashlib.sha256(
                b"libero-action-chain-v1"
            ).hexdigest()
            record.status = SessionStatus.READY
            record.last_activity_at = self._clock()
            record.spec["init_state_id"] = request.init_state_id
            record.spec["seed"] = request.seed
            response = {
                "protocol_version": PROTOCOL_VERSION,
                "session_id": record.session_id,
                "episode_id": record.episode_id,
                "status": record.status.value,
                "step_index": 0,
                **record.spec["_session_metadata"],
                **reset,
            }
            emit_audit(
                "session_reset",
                session_id=record.session_id,
                previous_episode_id=previous_episode_id,
                episode_id=record.episode_id,
                worker_pid=record.worker.pid,
                suite=record.spec["suite"],
                task_id=record.spec["task_id"],
                init_state_id=request.init_state_id,
                seed=request.seed,
                status=record.status.value,
            )
            return response

    async def step(
        self, session_id: str, request: StepRequest, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        record = self._get_record(session_id, owner_id)
        async with record.lock:
            self._require_current_lease(
                record, request, require_identity=owner_id is not None
            )
            if record.status in {SessionStatus.CLOSED, SessionStatus.EXPIRED}:
                try:
                    self._require_usable(record, request.request_id)
                except PlatformError as inactive_error:
                    self._audit_step_rejected(record, request, inactive_error)
                    raise
            if request.episode_id != record.episode_id:
                rejection = PlatformError(
                    ErrorCode.STALE_EPISODE,
                    "The step belongs to an inactive episode",
                    status_code=409,
                    request_id=request.request_id,
                )
                self._audit_step_rejected(record, request, rejection)
                raise rejection

            action = np.ascontiguousarray(request.action, dtype=np.float32)
            action_hash = hashlib.sha256(action.tobytes(order="C")).hexdigest()
            cached = record.cache.get(request.request_id)
            if cached is not None:
                if (
                    cached.episode_id != request.episode_id
                    or cached.expected_step_index != request.expected_step_index
                    or cached.action_hash != action_hash
                ):
                    rejection = PlatformError(
                        ErrorCode.REQUEST_ID_CONFLICT,
                        "The request_id was already used with a different action",
                        status_code=409,
                        request_id=request.request_id,
                    )
                    self._audit_step_rejected(record, request, rejection, action_hash)
                    raise rejection
                record.last_activity_at = self._clock()
                emit_audit(
                    "step_replayed",
                    session_id=record.session_id,
                    episode_id=record.episode_id,
                    worker_pid=record.worker.pid,
                    suite=record.spec["suite"],
                    task_id=record.spec["task_id"],
                    request_id=request.request_id,
                    expected_step_index=request.expected_step_index,
                    action_sha256=action_hash,
                    cached_produced_at=cached.produced_at,
                    cached_outcome="error" if cached.error is not None else "response",
                    cached_error_code=(
                        cached.error.code.value if cached.error is not None else None
                    ),
                    status=record.status.value,
                )
                return cached.replay()

            try:
                self._require_usable(record, request.request_id)
            except PlatformError as unusable_error:
                self._audit_step_rejected(record, request, unusable_error, action_hash)
                raise

            if request.expected_step_index < record.next_step_index:
                rejection = PlatformError(
                    ErrorCode.DUPLICATE_OR_EXPIRED_STEP,
                    "The requested step has already been committed and is no longer cached",
                    status_code=409,
                    request_id=request.request_id,
                )
                self._cache_error(record, request, action_hash, rejection)
                self._audit_step_rejected(record, request, rejection, action_hash)
                raise rejection
            if request.expected_step_index > record.next_step_index:
                rejection = PlatformError(
                    ErrorCode.OUT_OF_ORDER_STEP,
                    "The requested step is ahead of the environment",
                    status_code=409,
                    request_id=request.request_id,
                )
                self._audit_step_rejected(record, request, rejection, action_hash)
                raise rejection
            if record.status in {SessionStatus.TERMINATED, SessionStatus.TRUNCATED}:
                rejection = PlatformError(
                    ErrorCode.EPISODE_NOT_ACTIVE,
                    "Reset the session before sending another action",
                    status_code=409,
                    request_id=request.request_id,
                )
                self._cache_error(record, request, action_hash, rejection)
                self._audit_step_rejected(record, request, rejection, action_hash)
                raise rejection

            try:
                self._validate_action(record, request, action)
            except PlatformError as invalid_action_error:
                self._cache_error(record, request, action_hash, invalid_action_error)
                self._audit_step_rejected(
                    record, request, invalid_action_error, action_hash
                )
                raise

            record.status = SessionStatus.STEPPING
            started_at = time.perf_counter()
            try:
                result = await _run_blocking(record.worker.step, action)
            except WorkerError as error:
                platform_error = self._mark_worker_failed(
                    record, error, operation="step", request_id=request.request_id
                )
                self._cache_error(record, request, action_hash, platform_error)
                self._audit_step_rejected(
                    record, request, platform_error, action_hash
                )
                raise platform_error from error

            committed_index = record.next_step_index
            record.next_step_index += 1
            record.action_chain_hash = hashlib.sha256(
                bytes.fromhex(record.action_chain_hash)
                + bytes.fromhex(action_hash)
                + committed_index.to_bytes(8, byteorder="big", signed=False)
            ).hexdigest()
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
            emit_audit(
                "step_committed",
                session_id=record.session_id,
                episode_id=record.episode_id,
                worker_pid=record.worker.pid,
                suite=record.spec["suite"],
                task_id=record.spec["task_id"],
                request_id=request.request_id,
                expected_step_index=request.expected_step_index,
                step_index=committed_index,
                next_step_index=record.next_step_index,
                action_sha256=action_hash,
                server_step_seconds=response["server_step_seconds"],
                reward=float(response["reward"]),
                success=bool(response["success"]),
                terminated=bool(response["terminated"]),
                truncated=bool(response["truncated"]),
                status=record.status.value,
            )
            cached_step = CachedStep(
                episode_id=record.episode_id,
                expected_step_index=committed_index,
                action_hash=action_hash,
                produced_at=time.time(),
                response=response,
            )
            self._store_cache_entry(record, request.request_id, cached_step)
            record.last_committed = response
            record.last_activity_at = self._clock()
            return response

    async def get(
        self, session_id: str, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        record = self._get_record(session_id, owner_id)
        async with record.lock:
            if record.status not in _INACTIVE_STATUSES:
                record.last_activity_at = self._clock()
            return record.snapshot()

    async def episode_outcome(
        self, session_id: str, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        record = self._get_record(session_id, owner_id)
        async with record.lock:
            committed = record.last_committed
            finished = committed is not None and bool(
                committed.get("terminated") or committed.get("truncated")
            )
            if not finished:
                raise PlatformError(
                    ErrorCode.EPISODE_NOT_FINISHED,
                    "The episode must terminate or truncate before completion",
                    status_code=409,
                )
            assert committed is not None
            return {
                "session_id": record.session_id,
                "episode_id": record.episode_id,
                "status": (
                    SessionStatus.TERMINATED.value
                    if committed["terminated"]
                    else SessionStatus.TRUNCATED.value
                ),
                "success": bool(committed["success"]),
                "terminated": bool(committed["terminated"]),
                "truncated": bool(committed["truncated"]),
                "reward": float(committed["reward"]),
                "step_count": record.next_step_index,
                "action_chain_hash": record.action_chain_hash,
                "last_request_id": committed["request_id"],
            }

    async def keep_alive(
        self, session_id: str, owner_id: Optional[str] = None
    ) -> None:
        record = self._get_record(session_id, owner_id)
        async with record.lock:
            self._require_usable(record)
            record.last_activity_at = self._clock()

    async def bind_lease(
        self,
        session_id: str,
        owner_id: str,
        lease_id: str,
        generation: int,
        expires_at: float,
    ) -> None:
        record = self._get_record(session_id, owner_id)
        async with record.lock:
            self._require_usable(record)
            record.lease_id = lease_id
            record.lease_generation = generation
            record.lease_expires_at = expires_at

    async def extend_lease(
        self,
        session_id: str,
        owner_id: str,
        lease_id: str,
        generation: int,
        expires_at: float,
    ) -> None:
        record = self._get_record(session_id, owner_id)
        async with record.lock:
            self._require_lease_identity(record, lease_id, generation)
            if record.lease_expires_at is not None and time.time() > record.lease_expires_at:
                raise PlatformError(
                    ErrorCode.STALE_LEASE,
                    "The episode lease has expired",
                    status_code=409,
                )
            record.lease_expires_at = expires_at
            record.last_activity_at = self._clock()

    async def close(
        self,
        session_id: str,
        reason: str = "client_request",
        owner_id: Optional[str] = None,
    ) -> None:
        record = self._get_record(session_id, owner_id)
        async with record.lock:
            if record.status == SessionStatus.CLOSED:
                return
            previous_status = record.status
            await _run_blocking(record.worker.close)
            record.status = SessionStatus.CLOSED
            emit_audit(
                "session_closed",
                session_id=record.session_id,
                episode_id=record.episode_id,
                worker_pid=record.worker.pid,
                suite=record.spec["suite"],
                task_id=record.spec["task_id"],
                next_step_index=record.next_step_index,
                previous_status=previous_status.value,
                close_reason=reason,
                status=record.status.value,
            )

    async def close_all(self) -> None:
        for session_id in list(self._sessions):
            try:
                await self.close(session_id, reason="server_shutdown")
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
                idle_seconds = now - record.last_activity_at
                close_succeeded = True
                try:
                    await _run_blocking(record.worker.close)
                except Exception:
                    close_succeeded = False
                    record.worker.terminate()
                record.status = SessionStatus.EXPIRED
                emit_audit(
                    "session_expired",
                    session_id=record.session_id,
                    episode_id=record.episode_id,
                    worker_pid=record.worker.pid,
                    suite=record.spec["suite"],
                    task_id=record.spec["task_id"],
                    next_step_index=record.next_step_index,
                    idle_seconds=idle_seconds,
                    close_succeeded=close_succeeded,
                    status=record.status.value,
                )
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
        result = {
            "protocol_version": PROTOCOL_VERSION,
            "backend": self._backend,
            "suites": ["libero_goal", "libero_spatial", "libero_object", "libero_10"],
            "observation_schema_versions": ["libero_standard_v1"],
            "variants": ["base"],
            "control_modes": ["relative", "absolute"],
        }
        if self._task_manifest is not None:
            result.update(self._task_manifest.catalog())
        return result

    def _get_record(
        self, session_id: str, owner_id: Optional[str] = None
    ) -> SessionRecord:
        record: Optional[SessionRecord] = self._sessions.get(session_id)
        if record is None or (owner_id is not None and record.owner_id != owner_id):
            raise PlatformError(
                ErrorCode.SESSION_NOT_FOUND,
                "The requested session does not exist",
                status_code=404,
            )
        return record

    def _require_current_lease(
        self,
        record: SessionRecord,
        request: StepRequest,
        require_identity: bool,
    ) -> None:
        if record.lease_id is None:
            return
        if request.lease_id is None or request.lease_generation is None:
            if not require_identity:
                return
            raise PlatformError(
                ErrorCode.STALE_LEASE,
                "Scheduled steps require the active lease identity",
                status_code=409,
                request_id=request.request_id,
            )
        self._require_lease_identity(
            record, request.lease_id, request.lease_generation, request.request_id
        )
        if record.lease_expires_at is not None and time.time() > record.lease_expires_at:
            raise PlatformError(
                ErrorCode.STALE_LEASE,
                "The episode lease has expired",
                status_code=409,
                request_id=request.request_id,
            )

    @staticmethod
    def _require_lease_identity(
        record: SessionRecord,
        lease_id: str,
        generation: int,
        request_id: Optional[str] = None,
    ) -> None:
        if record.lease_id != lease_id or record.lease_generation != generation:
            raise PlatformError(
                ErrorCode.STALE_LEASE,
                "The episode lease is no longer current",
                status_code=409,
                request_id=request_id,
            )

    @staticmethod
    def _require_usable(
        record: SessionRecord, request_id: Optional[str] = None
    ) -> None:
        if record.status in _INACTIVE_STATUSES:
            raise PlatformError(
                ErrorCode.SESSION_NOT_ACTIVE,
                "The session can no longer execute environment operations",
                status_code=410 if record.status == SessionStatus.EXPIRED else 409,
                request_id=request_id,
            )

    @staticmethod
    def _validate_action(
        record: SessionRecord, request: StepRequest, action: np.ndarray
    ) -> None:
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

    def _cache_error(
        self,
        record: SessionRecord,
        request: StepRequest,
        action_hash: str,
        error: PlatformError,
    ) -> None:
        self._store_cache_entry(
            record,
            request.request_id,
            CachedStep(
                episode_id=record.episode_id,
                expected_step_index=request.expected_step_index,
                action_hash=action_hash,
                produced_at=time.time(),
                error=CachedError.from_exception(error),
            ),
        )

    def _store_cache_entry(
        self, record: SessionRecord, request_id: str, entry: CachedStep
    ) -> None:
        record.cache[request_id] = entry
        record.cache.move_to_end(request_id)
        while len(record.cache) > self._request_cache_size:
            record.cache.popitem(last=False)

    @staticmethod
    def _audit_step_rejected(
        record: SessionRecord,
        request: StepRequest,
        error: PlatformError,
        action_hash: Optional[str] = None,
    ) -> None:
        emit_audit(
            "step_rejected",
            session_id=record.session_id,
            episode_id=record.episode_id,
            worker_pid=record.worker.pid,
            suite=record.spec["suite"],
            task_id=record.spec["task_id"],
            request_id=request.request_id,
            requested_episode_id=request.episode_id,
            expected_step_index=request.expected_step_index,
            next_step_index=record.next_step_index,
            action_sha256=action_hash,
            error_code=error.code.value,
            status_code=error.status_code,
            status=record.status.value,
        )

    @staticmethod
    def _mark_worker_failed(
        record: SessionRecord,
        error: WorkerError,
        operation: str,
        request_id: Optional[str] = None,
    ) -> PlatformError:
        record.worker.terminate()
        record.status = SessionStatus.FAILED
        code = (
            ErrorCode.WORKER_TIMEOUT
            if isinstance(error, WorkerTimeoutError)
            else ErrorCode.WORKER_FAILED
        )
        emit_audit(
            "worker_failed",
            session_id=record.session_id,
            episode_id=record.episode_id,
            worker_pid=record.worker.pid,
            suite=record.spec["suite"],
            task_id=record.spec["task_id"],
            request_id=request_id,
            operation=operation,
            error_code=code.value,
            cause=str(error),
            status=record.status.value,
        )
        return PlatformError(
            code,
            "The environment worker failed; the current episode cannot be resumed",
            status_code=500,
            request_id=request_id,
            details={"cause": str(error)},
        )


async def _run_blocking(function: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a worker IPC call without blocking the Python 3.8 event loop."""

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(function, *args, **kwargs))
