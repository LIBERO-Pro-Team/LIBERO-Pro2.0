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

from .errors import PlatformError
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

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        cleanup_stop = asyncio.Event()
        cleanup_task = asyncio.create_task(
            _cleanup_loop(manager, resolved.cleanup_interval_seconds, cleanup_stop)
        )
        try:
            yield
        finally:
            cleanup_stop.set()
            try:
                await cleanup_task
            finally:
                await manager.close_all()

    app = FastAPI(
        title="LIBERO-PRO Remote Evaluation Service",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.session_manager = manager
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
        }
        if not backend["ready"]:
            body["status"] = "not_ready"
            return JSONResponse(status_code=503, content=body)
        return JSONResponse(content=body)

    @app.get("/v1/tasks")
    async def tasks() -> Dict[str, Any]:
        return manager.task_catalog()

    @app.post("/v1/sessions", response_class=Response)
    async def create_session(request: CreateSessionRequest) -> Response:
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
    interval_seconds: float,
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            await manager.expire_idle_sessions()
