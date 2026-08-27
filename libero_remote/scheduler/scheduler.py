"""Deep scheduling module for persistent evaluation runs."""

import asyncio
import hashlib
import hmac
import time
import uuid
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Callable, Deque, Dict, Optional, Tuple

from libero_remote.protocol.codec import pack_message, unpack_message
from libero_remote.protocol.models import PROTOCOL_VERSION, CreateSessionRequest, ErrorCode
from libero_remote.server.audit import emit_audit
from libero_remote.server.errors import PlatformError
from libero_remote.server.session_manager import SessionManager

from .fingerprints import (
    canonical_fingerprint,
    initial_environment_reproducibility,
)
from .models import (
    ClaimRequest,
    JobStatus,
    LeaseCommandRequest,
    LeaseStatus,
    RunStatus,
    SubmitRunRequest,
)
from .store import SQLiteRunStore


@dataclass
class _ClaimIntent:
    run_id: str
    owner_id: str
    runner_id: str
    requested_at: float
    expires_at: float


class RunScheduler:
    def __init__(
        self,
        db_path: str,
        queue_capacity: int,
        max_attempts: int,
        session_manager: SessionManager,
        heartbeat_interval_seconds: float,
        lease_grace_period_seconds: float,
        max_active_sessions_per_owner: int,
        claim_intent_ttl_seconds: float,
        allow_direct_sessions: bool,
        runtime_identity: Optional[Dict[str, Any]] = None,
        result_signing_key: str = "",
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._db_path = db_path
        self._queue_capacity = queue_capacity
        self._max_attempts = max_attempts
        self._session_manager = session_manager
        self._heartbeat_interval_seconds = heartbeat_interval_seconds
        self._lease_grace_period_seconds = lease_grace_period_seconds
        self._max_active_sessions_per_owner = max_active_sessions_per_owner
        self._claim_intent_ttl_seconds = claim_intent_ttl_seconds
        self._allow_direct_sessions = allow_direct_sessions
        self._runtime_fingerprint = canonical_fingerprint(runtime_identity or {})
        self._result_signing_key = result_signing_key.encode("utf-8")
        self._clock = clock
        self._store: Optional[SQLiteRunStore] = None
        self._lock = asyncio.Lock()
        self._intents: Dict[Tuple[str, str], _ClaimIntent] = {}
        self._owner_turns: Deque[str] = deque()

    async def start(self) -> None:
        if self._store is None:
            self._store = SQLiteRunStore(self._db_path)
            recovered = self._store.recover_interrupted(
                self._clock(), self._max_attempts
            )
            if recovered:
                emit_audit("scheduler_recovered", requeued_episodes=recovered)

    async def submit(
        self, request: SubmitRunRequest, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        async with self._lock:
            store = self._require_store()
            resolved_owner = owner_id or request.owner_id or "anonymous"
            if store.count_pending_jobs() + len(request.episodes) > self._queue_capacity:
                raise PlatformError(
                    ErrorCode.RUN_QUEUE_FULL,
                    "The episode queue has reached its configured capacity",
                    status_code=503,
                )
            run_id = f"run_{uuid.uuid4().hex}"
            created_at = self._clock()
            resolved_episodes = [
                self._session_manager.resolve_session_request(episode)
                for episode in request.episodes
            ]
            jobs = [
                {
                    "job_id": f"job_{uuid.uuid4().hex}",
                    "ordinal": ordinal,
                    "status": JobStatus.QUEUED.value,
                    "spec": episode.dict(),
                    "job_fingerprint": canonical_fingerprint(episode.dict()),
                    "runtime_fingerprint": self._runtime_fingerprint,
                }
                for ordinal, episode in enumerate(resolved_episodes)
            ]
            store.create_run(
                run_id,
                resolved_owner,
                RunStatus.QUEUED.value,
                created_at,
                jobs,
            )
            emit_audit(
                "run_submitted",
                run_id=run_id,
                owner_id=resolved_owner,
                episode_count=len(jobs),
                status=RunStatus.QUEUED.value,
            )
            return self._snapshot(run_id)

    async def get(
        self, run_id: str, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        async with self._lock:
            return self._snapshot(run_id, owner_id)

    async def list_episodes(
        self, run_id: str, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        async with self._lock:
            store = self._require_store()
            self._require_run(store, run_id, owner_id)
            jobs = store.list_jobs(run_id)
            return {
                "protocol_version": PROTOCOL_VERSION,
                "run_id": run_id,
                "episodes": [
                    {
                        "job_id": job["job_id"],
                        "job_index": job["ordinal"],
                        "status": job["status"],
                        "attempt": job["attempt"],
                        "spec": job["spec"],
                        "result": job["result"],
                        "reproducibility": self._job_reproducibility(job),
                        "perturbation_plan": job["perturbation_plan"],
                    }
                    for job in jobs
                ],
            }

    async def capacity_snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            store = self._require_store()
            self._prune_intents(store, self._clock())
            pending = store.count_pending_jobs()
            return {
                "queue": {
                    "pending": pending,
                    "capacity": self._queue_capacity,
                    "available": max(0, self._queue_capacity - pending),
                },
                "active_leases": store.count_active_leases(),
                "waiting_runners": len(self._intents),
                "max_active_sessions_per_owner": self._max_active_sessions_per_owner,
                "direct_sessions_enabled": self._allow_direct_sessions,
                "persistence": "sqlite",
            }

    async def claim(
        self,
        run_id: str,
        request: ClaimRequest,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            store = self._require_store()
            run = self._require_run(store, run_id, owner_id)
            self._require_active_run(run)
            active = store.find_active_lease(run_id, request.runner_id)
            if active is not None:
                self._remove_intent(run_id, request.runner_id)
                payload = unpack_message(bytes(active["initial_payload"]))
                if not isinstance(payload, dict):
                    raise RuntimeError("Stored lease payload is not a map")
                payload["lease_expires_at"] = active["expires_at"]
                return payload
            if store.next_queued_job(run_id) is None:
                return self._queued_claim(run_id, request.runner_id)
            now = self._clock()
            self._register_intent(
                _ClaimIntent(
                    run_id=run_id,
                    owner_id=str(run["owner_id"]),
                    runner_id=request.runner_id,
                    requested_at=now,
                    expires_at=now + self._claim_intent_ttl_seconds,
                )
            )
            if self._session_manager.capacity_snapshot()["available"] <= 0:
                return self._queued_claim(run_id, request.runner_id)
            selected = self._select_intent(store, now)
            if selected is None:
                return self._queued_claim(run_id, request.runner_id)
            intent, job = selected
            store.mark_allocating(job["job_id"], now)

        mismatch = self._allocation_identity_mismatch(job)
        if mismatch is not None:
            async with self._lock:
                self._require_store().fail_allocation(
                    job["job_id"],
                    ErrorCode.REPRODUCIBILITY_MISMATCH.value,
                    mismatch,
                    self._clock(),
                )
            emit_audit(
                "reproducibility_mismatch",
                run_id=intent.run_id,
                owner_id=intent.owner_id,
                job_id=job["job_id"],
                job_index=job["ordinal"],
                error_code=ErrorCode.REPRODUCIBILITY_MISMATCH.value,
                cause=mismatch,
            )
            raise PlatformError(
                ErrorCode.REPRODUCIBILITY_MISMATCH,
                mismatch,
                status_code=409,
            )

        try:
            session = await self._session_manager.create(
                CreateSessionRequest(**job["spec"]), owner_id=intent.owner_id
            )
        except PlatformError as error:
            async with self._lock:
                now = self._clock()
                self._require_store().requeue_allocation(job["job_id"], now)
                self._register_intent(
                    _ClaimIntent(
                        run_id=intent.run_id,
                        owner_id=intent.owner_id,
                        runner_id=intent.runner_id,
                        requested_at=now,
                        expires_at=now + self._claim_intent_ttl_seconds,
                    )
                )
            if error.code == ErrorCode.SESSION_CAPACITY_REACHED:
                return self._queued_claim(run_id, request.runner_id)
            raise

        lease_id = f"lease_{uuid.uuid4().hex}"
        now = self._clock()
        try:
            environment_identity = initial_environment_reproducibility(session)
        except ValueError as error:
            await self._session_manager.close(
                str(session["session_id"]),
                reason="reproducibility_metadata_invalid",
                owner_id=intent.owner_id,
            )
            message = str(error)
            async with self._lock:
                self._require_store().fail_allocation(
                    job["job_id"],
                    ErrorCode.REPRODUCIBILITY_MISMATCH.value,
                    message,
                    self._clock(),
                )
            raise PlatformError(
                ErrorCode.REPRODUCIBILITY_MISMATCH,
                message,
                status_code=409,
            ) from error
        async with self._lock:
            state_matches = self._require_store().bind_reproducibility(
                job["job_id"], environment_identity, now
            )
        if not state_matches:
            await self._session_manager.close(
                str(session["session_id"]),
                reason="reproducibility_mismatch",
                owner_id=intent.owner_id,
            )
            message = "The recreated environment does not match the job's first reset"
            async with self._lock:
                self._require_store().fail_allocation(
                    job["job_id"],
                    ErrorCode.REPRODUCIBILITY_MISMATCH.value,
                    message,
                    self._clock(),
                )
            emit_audit(
                "reproducibility_mismatch",
                run_id=intent.run_id,
                owner_id=intent.owner_id,
                job_id=job["job_id"],
                job_index=job["ordinal"],
                error_code=ErrorCode.REPRODUCIBILITY_MISMATCH.value,
                cause="environment_reproducibility",
            )
            raise PlatformError(
                ErrorCode.REPRODUCIBILITY_MISMATCH,
                message,
                status_code=409,
            )
        reproducibility = {
            "job_fingerprint": str(job["job_fingerprint"]),
            "runtime_fingerprint": str(job["runtime_fingerprint"]),
            **{
                key: str(environment_identity[key])
                for key in (
                    "initial_state_fingerprint",
                    "initial_observation_fingerprint",
                    "perturbation_plan_fingerprint",
                )
            },
        }
        response = {
            "protocol_version": PROTOCOL_VERSION,
            "status": "leased",
            "run_id": intent.run_id,
            "job_id": job["job_id"],
            "job_index": job["ordinal"],
            "attempt": int(job["attempt"]) + 1,
            "lease_generation": int(job["attempt"]) + 1,
            "lease_id": lease_id,
            "lease_expires_at": now + self._lease_grace_period_seconds,
            "heartbeat_interval_seconds": self._heartbeat_interval_seconds,
            "episode_spec": dict(job["spec"]),
            "reproducibility": reproducibility,
            "session": session,
        }
        async with self._lock:
            activated = self._require_store().activate_lease(
                job_id=job["job_id"],
                lease_id=lease_id,
                runner_id=intent.runner_id,
                generation=response["lease_generation"],
                session_id=str(session["session_id"]),
                expires_at=response["lease_expires_at"],
                initial_payload=pack_message(response),
                updated_at=now,
            )
        if not activated:
            await self._session_manager.close(
                str(session["session_id"]), reason="allocation_cancelled"
            )
            raise PlatformError(
                ErrorCode.RUN_NOT_ACTIVE,
                "The evaluation run was cancelled during environment allocation",
                status_code=409,
            )
        await self._session_manager.bind_lease(
            str(session["session_id"]),
            intent.owner_id,
            lease_id,
            response["lease_generation"],
            response["lease_expires_at"],
        )
        emit_audit(
            "episode_leased",
            run_id=intent.run_id,
            owner_id=intent.owner_id,
            runner_id=intent.runner_id,
            job_id=job["job_id"],
            job_index=job["ordinal"],
            attempt=response["attempt"],
            lease_id=lease_id,
            lease_generation=response["lease_generation"],
            session_id=session["session_id"],
            status=LeaseStatus.ACTIVE.value,
            **reproducibility,
        )
        if intent.run_id == run_id and intent.runner_id == request.runner_id:
            return response
        return self._queued_claim(run_id, request.runner_id)

    async def cancel(
        self, run_id: str, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        async with self._lock:
            store = self._require_store()
            run = self._require_run(store, run_id, owner_id)
            if run["status"] == RunStatus.CANCELLED.value:
                return self._snapshot(run_id)
            if run["status"] in {RunStatus.COMPLETED.value, RunStatus.FAILED.value}:
                raise PlatformError(
                    ErrorCode.RUN_NOT_ACTIVE,
                    "The evaluation run has already finished",
                    status_code=409,
                )
            leases = store.cancel_run(run_id, self._clock())
            for key, intent in list(self._intents.items()):
                if intent.run_id == run_id:
                    self._intents.pop(key, None)

        for lease in leases:
            try:
                await self._session_manager.close(
                    str(lease["session_id"]), reason="run_cancelled"
                )
            except PlatformError as error:
                if error.code != ErrorCode.SESSION_NOT_FOUND:
                    raise
        emit_audit(
            "run_cancelled",
            run_id=run_id,
            active_lease_count=len(leases),
            status=RunStatus.CANCELLED.value,
        )
        return await self.get(run_id, owner_id)

    async def complete(
        self,
        lease_id: str,
        request: LeaseCommandRequest,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            store = self._require_store()
            lease = self._require_lease(store, lease_id, owner_id)
            self._require_generation(lease, request, owner_id)
            self._require_runner(lease, request.runner_id)
            if lease["status"] == LeaseStatus.COMPLETED.value:
                return self._completion_response(store, lease)
            if lease["status"] != LeaseStatus.ACTIVE.value:
                raise PlatformError(
                    ErrorCode.LEASE_NOT_ACTIVE,
                    "The lease can no longer complete an episode",
                    status_code=409,
                )
            store.mark_lease_completing(lease_id, self._clock())

        try:
            result = await self._session_manager.episode_outcome(
                str(lease["session_id"]), owner_id=owner_id
            )
        except Exception:
            async with self._lock:
                self._require_store().restore_active_lease(lease_id, self._clock())
            raise

        async with self._lock:
            job = self._require_store().get_job(str(lease["job_id"]))
        if job is None:
            raise RuntimeError("The completed lease has no episode job")
        result.update(
            {
                "account_id": str(lease["owner_id"]),
                "run_id": str(lease["run_id"]),
                "job_id": str(lease["job_id"]),
                "attempt": int(lease["generation"]),
                "lease_generation": int(lease["generation"]),
                **self._job_reproducibility(job),
            }
        )
        result_receipt = self._sign_result(result)
        async with self._lock:
            store = self._require_store()
            if not store.complete_lease(
                lease_id, result, self._clock(), result_receipt
            ):
                raise PlatformError(
                    ErrorCode.LEASE_NOT_ACTIVE,
                    "The lease changed state before completion was committed",
                    status_code=409,
                )
            completed_lease = self._require_lease(store, lease_id)
            response = self._completion_response(store, completed_lease)
        try:
            await self._session_manager.close(
                str(lease["session_id"]), reason="lease_completed"
            )
        except Exception as error:
            emit_audit(
                "completed_session_cleanup_failed",
                run_id=response["run_id"],
                job_id=response["job_id"],
                lease_id=lease_id,
                session_id=lease["session_id"],
                error_type=type(error).__name__,
                error_message=str(error),
            )
        emit_audit(
            "episode_completed",
            run_id=response["run_id"],
            job_id=response["job_id"],
            job_index=response["job_index"],
            lease_id=lease_id,
            session_id=result["session_id"],
            success=result["success"],
            step_count=result["step_count"],
            result_receipt=result_receipt,
            status=LeaseStatus.COMPLETED.value,
        )
        return response

    async def heartbeat(
        self,
        lease_id: str,
        request: LeaseCommandRequest,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            store = self._require_store()
            lease = self._require_lease(store, lease_id, owner_id)
            self._require_generation(lease, request, owner_id)
            self._require_runner(lease, request.runner_id)
            if lease["status"] != LeaseStatus.ACTIVE.value:
                raise PlatformError(
                    ErrorCode.LEASE_NOT_ACTIVE,
                    "The lease can no longer be renewed",
                    status_code=409,
                )
            now = self._clock()
            if float(lease["expires_at"]) <= now:
                raise PlatformError(
                    ErrorCode.STALE_LEASE,
                    "The episode lease has expired",
                    status_code=409,
                )
            expires_at = now + self._lease_grace_period_seconds
            await self._session_manager.extend_lease(
                str(lease["session_id"]),
                str(lease["owner_id"]),
                lease_id,
                int(lease["generation"]),
                expires_at,
            )
            store.extend_lease(lease_id, expires_at, now)
            return {
                "protocol_version": PROTOCOL_VERSION,
                "status": "active",
                "lease_id": lease_id,
                "lease_generation": int(lease["generation"]),
                "lease_expires_at": expires_at,
                "heartbeat_interval_seconds": self._heartbeat_interval_seconds,
            }

    async def abandon(
        self,
        lease_id: str,
        request: LeaseCommandRequest,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._lock:
            store = self._require_store()
            lease = self._require_lease(store, lease_id, owner_id)
            self._require_generation(lease, request, owner_id)
            self._require_runner(lease, request.runner_id)
            if lease["status"] == LeaseStatus.ABANDONED.value:
                return self._abandon_response(store, lease)
            if lease["status"] != LeaseStatus.ACTIVE.value:
                raise PlatformError(
                    ErrorCode.LEASE_NOT_ACTIVE,
                    "The lease can no longer be abandoned",
                    status_code=409,
                )
            if not store.abandon_lease(
                lease_id, self._clock(), "AGENT_FAILURE"
            ):
                raise PlatformError(
                    ErrorCode.LEASE_NOT_ACTIVE,
                    "The lease changed state before it could be abandoned",
                    status_code=409,
                )

        await self._session_manager.close(
            str(lease["session_id"]), reason="lease_abandoned"
        )
        async with self._lock:
            abandoned = self._require_lease(self._require_store(), lease_id)
            response = self._abandon_response(self._require_store(), abandoned)
        emit_audit(
            "lease_abandoned",
            run_id=response["run_id"],
            job_id=response["job_id"],
            job_index=response["job_index"],
            lease_id=lease_id,
            session_id=lease["session_id"],
            status=LeaseStatus.ABANDONED.value,
        )
        return response

    async def expire_leases(self) -> int:
        async with self._lock:
            expired = self._require_store().expire_due_leases(
                self._clock(), self._max_attempts
            )
        for lease in expired:
            try:
                await self._session_manager.close(
                    str(lease["session_id"]), reason="lease_expired"
                )
            except PlatformError as error:
                if error.code != ErrorCode.SESSION_NOT_FOUND:
                    raise
            emit_audit(
                "lease_expired",
                run_id=lease["run_id"],
                job_id=lease["job_id"],
                lease_id=lease["lease_id"],
                session_id=lease["session_id"],
                runner_id=lease["runner_id"],
                status=LeaseStatus.EXPIRED.value,
            )
        return len(expired)

    async def close(self) -> None:
        async with self._lock:
            if self._store is not None:
                self._store.close()
                self._store = None

    def _snapshot(
        self, run_id: str, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        store = self._require_store()
        run = self._require_run(store, run_id, owner_id)
        jobs = store.list_jobs(run_id)
        counts = Counter(job["status"] for job in jobs)
        completed = counts[JobStatus.COMPLETED.value]
        successful = sum(
            1 for job in jobs if job["result"] is not None and job["result"].get("success")
        )
        variants = sorted({str(job["spec"].get("variant", "base")) for job in jobs})
        by_variant: Dict[str, Dict[str, Any]] = {}
        for variant in variants:
            selected = [job for job in jobs if job["spec"].get("variant", "base") == variant]
            variant_completed = sum(
                1 for job in selected if job["status"] == JobStatus.COMPLETED.value
            )
            variant_successful = sum(
                1
                for job in selected
                if job["result"] is not None and job["result"].get("success")
            )
            by_variant[variant] = {
                "total": len(selected),
                "completed": variant_completed,
                "successful": variant_successful,
                "success_rate": (
                    variant_successful / variant_completed if variant_completed else None
                ),
            }
        return {
            "protocol_version": PROTOCOL_VERSION,
            "run_id": run_id,
            "owner_id": run["owner_id"],
            "status": run["status"],
            "summary": {
                "total": len(jobs),
                "queued": counts[JobStatus.QUEUED.value],
                "active": sum(
                    counts[status]
                    for status in (
                        JobStatus.ALLOCATING.value,
                        JobStatus.LEASED.value,
                        JobStatus.COMPLETING.value,
                    )
                ),
                "completed": completed,
                "failed": counts[JobStatus.FAILED.value],
                "cancelled": counts[JobStatus.CANCELLED.value],
                "successful": successful,
                "success_rate": successful / completed if completed else None,
                "by_variant": by_variant,
            },
        }

    @staticmethod
    def _require_run(
        store: SQLiteRunStore, run_id: str, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        run = store.get_run(run_id)
        if run is None or (owner_id is not None and run["owner_id"] != owner_id):
            raise PlatformError(
                ErrorCode.RUN_NOT_FOUND,
                "The requested evaluation run does not exist",
                status_code=404,
            )
        return run

    @staticmethod
    def _require_active_run(run: Dict[str, Any]) -> None:
        if run["status"] not in {RunStatus.QUEUED.value, RunStatus.RUNNING.value}:
            raise PlatformError(
                ErrorCode.RUN_NOT_ACTIVE,
                "The evaluation run no longer accepts episode claims",
                status_code=409,
            )

    @staticmethod
    def _queued_claim(run_id: str, runner_id: str) -> Dict[str, Any]:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "status": "queued",
            "run_id": run_id,
            "runner_id": runner_id,
            "retry_after_seconds": 1.0,
        }

    @staticmethod
    def _require_lease(
        store: SQLiteRunStore, lease_id: str, owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        lease = store.get_lease(lease_id)
        if lease is None or (owner_id is not None and lease["owner_id"] != owner_id):
            raise PlatformError(
                ErrorCode.LEASE_NOT_FOUND,
                "The requested episode lease does not exist",
                status_code=404,
            )
        return lease

    @staticmethod
    def _require_runner(lease: Dict[str, Any], runner_id: str) -> None:
        if lease["runner_id"] != runner_id:
            raise PlatformError(
                ErrorCode.LEASE_RUNNER_MISMATCH,
                "The lease belongs to a different runner",
                status_code=409,
            )

    @staticmethod
    def _completion_response(
        store: SQLiteRunStore, lease: Dict[str, Any]
    ) -> Dict[str, Any]:
        job = store.get_job(str(lease["job_id"]))
        if job is None or job["result"] is None:
            raise RuntimeError("Completed lease has no stored episode result")
        return {
            "protocol_version": PROTOCOL_VERSION,
            "status": "completed",
            "run_id": job["run_id"],
            "job_id": job["job_id"],
            "job_index": job["ordinal"],
            "lease_id": lease["lease_id"],
            "result": job["result"],
            "result_receipt": job["result_receipt"],
        }

    @staticmethod
    def _abandon_response(
        store: SQLiteRunStore, lease: Dict[str, Any]
    ) -> Dict[str, Any]:
        job = store.get_job(str(lease["job_id"]))
        if job is None:
            raise RuntimeError("Abandoned lease has no episode job")
        return {
            "protocol_version": PROTOCOL_VERSION,
            "status": job["status"],
            "run_id": job["run_id"],
            "job_id": job["job_id"],
            "job_index": job["ordinal"],
            "lease_id": lease["lease_id"],
        }

    def _require_store(self) -> SQLiteRunStore:
        if self._store is None:
            raise RuntimeError("RunScheduler.start() must be called before use")
        return self._store

    def _sign_result(self, result: Dict[str, Any]) -> str:
        payload = canonical_fingerprint(result).encode("ascii")
        return hmac.new(self._result_signing_key, payload, hashlib.sha256).hexdigest()

    @staticmethod
    def _require_generation(
        lease: Dict[str, Any],
        request: LeaseCommandRequest,
        authenticated_owner: Optional[str],
    ) -> None:
        generation = request.lease_generation
        if generation is None and authenticated_owner is None:
            return
        if generation != int(lease["generation"]):
            raise PlatformError(
                ErrorCode.STALE_LEASE,
                "The episode lease generation is no longer current",
                status_code=409,
            )

    def _allocation_identity_mismatch(
        self, job: Dict[str, Any]
    ) -> Optional[str]:
        if job.get("job_fingerprint") != canonical_fingerprint(job["spec"]):
            return "The stored episode specification no longer matches its fingerprint"
        if job.get("runtime_fingerprint") != self._runtime_fingerprint:
            return "The server runtime changed after this evaluation run was created"
        return None

    @staticmethod
    def _job_reproducibility(job: Dict[str, Any]) -> Dict[str, Optional[str]]:
        return {
            "job_fingerprint": job.get("job_fingerprint"),
            "runtime_fingerprint": job.get("runtime_fingerprint"),
            "initial_state_fingerprint": job.get("initial_state_fingerprint"),
            "initial_observation_fingerprint": job.get(
                "initial_observation_fingerprint"
            ),
            "perturbation_plan_fingerprint": job.get(
                "perturbation_plan_fingerprint"
            ),
        }

    def _register_intent(self, intent: _ClaimIntent) -> None:
        key = (intent.run_id, intent.runner_id)
        existing = self._intents.get(key)
        if existing is not None:
            intent.requested_at = existing.requested_at
        self._intents[key] = intent
        if intent.owner_id not in self._owner_turns:
            self._owner_turns.append(intent.owner_id)

    def _remove_intent(self, run_id: str, runner_id: str) -> None:
        self._intents.pop((run_id, runner_id), None)

    def _select_intent(
        self, store: SQLiteRunStore, now: float
    ) -> Optional[Tuple[_ClaimIntent, Dict[str, Any]]]:
        self._prune_intents(store, now)
        for _ in range(len(self._owner_turns)):
            owner_id = self._owner_turns.popleft()
            owner_intents = sorted(
                (
                    intent
                    for intent in self._intents.values()
                    if intent.owner_id == owner_id
                ),
                key=lambda intent: (intent.requested_at, intent.run_id, intent.runner_id),
            )
            if not owner_intents:
                continue
            if (
                store.count_active_jobs_for_owner(owner_id)
                >= self._max_active_sessions_per_owner
            ):
                self._owner_turns.append(owner_id)
                continue
            chosen: Optional[Tuple[_ClaimIntent, Dict[str, Any]]] = None
            for intent in owner_intents:
                job = store.next_queued_job(intent.run_id)
                if job is not None:
                    chosen = (intent, job)
                    break
                self._remove_intent(intent.run_id, intent.runner_id)
            if chosen is not None:
                self._remove_intent(chosen[0].run_id, chosen[0].runner_id)
                if any(
                    intent.owner_id == owner_id for intent in self._intents.values()
                ):
                    self._owner_turns.append(owner_id)
                return chosen
            if any(intent.owner_id == owner_id for intent in self._intents.values()):
                self._owner_turns.append(owner_id)
        return None

    def _prune_intents(self, store: SQLiteRunStore, now: float) -> None:
        for key, intent in list(self._intents.items()):
            if intent.expires_at <= now or store.next_queued_job(intent.run_id) is None:
                self._intents.pop(key, None)
        active_owners = {intent.owner_id for intent in self._intents.values()}
        self._owner_turns = deque(
            owner_id for owner_id in self._owner_turns if owner_id in active_owners
        )
