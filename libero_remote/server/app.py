import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from libero_remote import __version__
from libero_remote.environment.readiness import check_backend_readiness
from libero_remote.protocol.codec import MESSAGEPACK_MEDIA_TYPE, pack_message
from libero_remote.protocol.models import (
    CreateSessionRequest,
    ErrorCode,
    ErrorResponse,
    ResetRequest,
    StepRequest,
)
from libero_remote.scheduler import RunScheduler, SubmitRunRequest
from libero_remote.scheduler.models import ClaimRequest, LeaseCommandRequest

from .errors import PlatformError
from .runtime import collect_runtime_manifest
from .session_manager import SessionManager
from .settings import Settings


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    resolved = settings or Settings()
    manager = SessionManager(
        backend=resolved.environment_backend,
        max_sessions=resolved.max_sessions,
        worker_timeout_seconds=resolved.worker_timeout_seconds,
        request_cache_size=resolved.request_cache_size,
        session_idle_timeout_seconds=resolved.session_idle_timeout_seconds,
    )
    scheduler = RunScheduler(
        db_path=resolved.scheduler_db_path,
        queue_capacity=resolved.scheduler_queue_capacity,
        session_manager=manager,
        heartbeat_interval_seconds=resolved.heartbeat_interval_seconds,
        lease_grace_period_seconds=resolved.lease_grace_period_seconds,
        max_active_sessions_per_owner=resolved.max_active_sessions_per_owner,
        claim_intent_ttl_seconds=resolved.claim_intent_ttl_seconds,
        allow_direct_sessions=resolved.allow_direct_sessions,
    )
    runtime_manifest = collect_runtime_manifest()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await scheduler.start()
        cleanup_stop = asyncio.Event()
        cleanup_task = asyncio.create_task(
            _cleanup_loop(
                manager,
                scheduler,
                resolved.cleanup_interval_seconds,
                cleanup_stop,
            )
        )
        try:
            yield
        finally:
            cleanup_stop.set()
            try:
                await cleanup_task
            finally:
                try:
                    await manager.close_all()
                finally:
                    await scheduler.close()

    app = FastAPI(
        title="LIBERO-PRO Remote Evaluation Service",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.session_manager = manager
    app.state.run_scheduler = scheduler
    app.state.settings = resolved

    @app.exception_handler(PlatformError)
    async def platform_error_handler(_: Request, error: PlatformError) -> JSONResponse:
        body = ErrorResponse(
            error_code=error.code,
            message=error.message,
            request_id=error.request_id,
            details=error.details,
        )
        return JSONResponse(status_code=error.status_code, content=body.dict())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
        body = ErrorResponse(
            error_code=ErrorCode.INVALID_REQUEST,
            message="The request does not match protocol version 1.0",
            details={"errors": error.errors()},
        )
        return JSONResponse(status_code=422, content=body.dict())

    @app.get("/v1/health")
    async def health() -> Response:
        backend = check_backend_readiness(resolved.environment_backend)
        body = {
            "status": "ok",
            "version": __version__,
            "backend": backend,
            "sessions": manager.capacity_snapshot(),
            "scheduler": await scheduler.capacity_snapshot(),
            "runtime": runtime_manifest,
        }
        if not backend["ready"]:
            body["status"] = "not_ready"
            return JSONResponse(status_code=503, content=body)
        return JSONResponse(content=body)

    @app.get("/v1/tasks")
    async def tasks() -> Dict[str, Any]:
        return manager.task_catalog()

    @app.post("/v1/runs", status_code=201)
    async def submit_run(request: SubmitRunRequest) -> Dict[str, Any]:
        return await scheduler.submit(request)

    @app.get("/v1/runs/{run_id}")
    async def get_run(run_id: str) -> Dict[str, Any]:
        return await scheduler.get(run_id)

    @app.get("/v1/runs/{run_id}/episodes")
    async def get_run_episodes(run_id: str) -> Dict[str, Any]:
        return await scheduler.list_episodes(run_id)

    @app.delete("/v1/runs/{run_id}")
    async def cancel_run(run_id: str) -> Dict[str, Any]:
        return await scheduler.cancel(run_id)

    @app.post("/v1/runs/{run_id}/claim", response_class=Response)
    async def claim_episode(run_id: str, request: ClaimRequest) -> Response:
        return _messagepack(await scheduler.claim(run_id, request))

    @app.post("/v1/leases/{lease_id}/complete")
    async def complete_episode(
        lease_id: str, request: LeaseCommandRequest
    ) -> Dict[str, Any]:
        return await scheduler.complete(lease_id, request)

    @app.post("/v1/leases/{lease_id}/heartbeat")
    async def heartbeat_episode(
        lease_id: str, request: LeaseCommandRequest
    ) -> Dict[str, Any]:
        return await scheduler.heartbeat(lease_id, request)

    @app.post("/v1/leases/{lease_id}/abandon")
    async def abandon_episode(
        lease_id: str, request: LeaseCommandRequest
    ) -> Dict[str, Any]:
        return await scheduler.abandon(lease_id, request)

    @app.post("/v1/sessions", response_class=Response)
    async def create_session(request: CreateSessionRequest) -> Response:
        if not resolved.allow_direct_sessions:
            raise PlatformError(
                ErrorCode.DIRECT_SESSIONS_DISABLED,
                "Direct sessions are disabled; submit and claim a scheduled run",
                status_code=403,
            )
        return _messagepack(await manager.create(request), status_code=201)

    @app.post("/v1/sessions/{session_id}/reset", response_class=Response)
    async def reset_session(session_id: str, request: ResetRequest) -> Response:
        return _messagepack(await manager.reset(session_id, request))

    @app.post("/v1/sessions/{session_id}/step", response_class=Response)
    async def step_session(session_id: str, request: StepRequest) -> Response:
        return _messagepack(await manager.step(session_id, request))

    @app.get("/v1/sessions/{session_id}")
    async def get_session(session_id: str) -> Dict[str, Any]:
        return await manager.get(session_id)

    @app.delete("/v1/sessions/{session_id}", status_code=204)
    async def close_session(session_id: str) -> Response:
        await manager.close(session_id)
        return Response(status_code=204)

    return app


def _messagepack(message: Dict[str, Any], status_code: int = 200) -> Response:
    return Response(
        content=pack_message(message),
        status_code=status_code,
        media_type=MESSAGEPACK_MEDIA_TYPE,
    )


app = create_app()


async def _cleanup_loop(
    manager: SessionManager,
    scheduler: RunScheduler,
    interval_seconds: float,
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            await scheduler.expire_leases()
            await manager.expire_idle_sessions()
