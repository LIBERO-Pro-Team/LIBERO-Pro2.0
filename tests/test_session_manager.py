import json
import logging
from typing import Any

import numpy as np
import pytest

from libero_remote.protocol.models import (
    CreateSessionRequest,
    ErrorCode,
    ResetRequest,
    StepRequest,
)
from libero_remote.server.errors import PlatformError
from libero_remote.server.session_manager import SessionManager


@pytest.mark.asyncio
async def test_retried_step_returns_cached_result_without_advancing_environment() -> None:
    manager = SessionManager(backend="fake", max_sessions=1, worker_timeout_seconds=5.0)
    created = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    command = StepRequest(
        episode_id=created["episode_id"],
        expected_step_index=0,
        request_id="request-1",
        action=[0.25, 0.0],
    )

    first = await manager.step(created["session_id"], command)
    retried = await manager.step(created["session_id"], command)
    snapshot = await manager.get(created["session_id"])
    await manager.close_all()

    assert retried["observation"]["robot0_joint_pos"][0] == np.float32(0.25)
    assert first["request_id"] == retried["request_id"]
    assert snapshot["next_step_index"] == 1


@pytest.mark.asyncio
async def test_closed_session_does_not_replay_a_cached_step() -> None:
    manager = SessionManager(backend="fake", max_sessions=1, worker_timeout_seconds=5.0)
    created = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    command = StepRequest(
        episode_id=created["episode_id"],
        expected_step_index=0,
        request_id="request-before-close",
        action=[0.25, 0.0],
    )
    await manager.step(created["session_id"], command)
    await manager.close(created["session_id"])

    with pytest.raises(PlatformError) as closed:
        await manager.step(created["session_id"], command)

    assert closed.value.code == ErrorCode.SESSION_NOT_ACTIVE


@pytest.mark.asyncio
async def test_step_rejects_conflicting_request_id_and_out_of_order_index() -> None:
    manager = SessionManager(backend="fake", max_sessions=1, worker_timeout_seconds=5.0)
    created = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    await manager.step(
        created["session_id"],
        StepRequest(
            episode_id=created["episode_id"],
            expected_step_index=0,
            request_id="request-1",
            action=[0.25, 0.0],
        ),
    )

    with pytest.raises(PlatformError) as conflict:
        await manager.step(
            created["session_id"],
            StepRequest(
                episode_id=created["episode_id"],
                expected_step_index=0,
                request_id="request-1",
                action=[0.5, 0.0],
            ),
        )
    assert conflict.value.code == ErrorCode.REQUEST_ID_CONFLICT

    with pytest.raises(PlatformError) as out_of_order:
        await manager.step(
            created["session_id"],
            StepRequest(
                episode_id=created["episode_id"],
                expected_step_index=2,
                request_id="request-2",
                action=[0.25, 0.0],
            ),
        )
    assert out_of_order.value.code == ErrorCode.OUT_OF_ORDER_STEP
    await manager.close_all()


@pytest.mark.asyncio
async def test_invalid_action_error_is_stable_and_request_id_cannot_be_reused() -> None:
    manager = SessionManager(backend="fake", max_sessions=1, worker_timeout_seconds=5.0)
    created = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    invalid = StepRequest(
        episode_id=created["episode_id"],
        expected_step_index=0,
        request_id="invalid-request",
        action=[2.0, 0.0],
    )

    with pytest.raises(PlatformError) as first:
        await manager.step(created["session_id"], invalid)
    with pytest.raises(PlatformError) as replayed:
        await manager.step(created["session_id"], invalid)
    with pytest.raises(PlatformError) as conflict:
        await manager.step(
            created["session_id"],
            StepRequest(
                episode_id=created["episode_id"],
                expected_step_index=0,
                request_id="invalid-request",
                action=[3.0, 0.0],
            ),
        )
    snapshot = await manager.get(created["session_id"])
    await manager.close_all()

    assert first.value.code == ErrorCode.INVALID_ACTION
    assert replayed.value.code == ErrorCode.INVALID_ACTION
    assert conflict.value.code == ErrorCode.REQUEST_ID_CONFLICT
    assert snapshot["next_step_index"] == 0


@pytest.mark.asyncio
async def test_reset_invalidates_old_episode_and_close_releases_capacity() -> None:
    manager = SessionManager(backend="fake", max_sessions=1, worker_timeout_seconds=5.0)
    created = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    reset = await manager.reset(created["session_id"], ResetRequest(init_state_id=1, seed=7))
    assert reset["episode_id"] != created["episode_id"]
    assert reset["step_index"] == 0

    with pytest.raises(PlatformError) as stale:
        await manager.step(
            created["session_id"],
            StepRequest(
                episode_id=created["episode_id"],
                expected_step_index=0,
                request_id="old-episode-request",
                action=[0.0, 0.0],
            ),
        )
    assert stale.value.code == ErrorCode.STALE_EPISODE

    await manager.close(created["session_id"])
    replacement = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    assert replacement["session_id"] != created["session_id"]
    await manager.close_all()


@pytest.mark.asyncio
async def test_audit_covers_reset_replay_rejection_and_expiration(caplog: Any) -> None:
    now = [100.0]
    manager = SessionManager(
        backend="fake",
        max_sessions=1,
        worker_timeout_seconds=5.0,
        session_idle_timeout_seconds=10.0,
        clock=lambda: now[0],
    )

    audit_logger = logging.getLogger("libero_remote.audit")
    audit_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="libero_remote.audit"):
            created = await manager.create(
                CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
            )
            reset = await manager.reset(
                created["session_id"], ResetRequest(init_state_id=0, seed=7)
            )
            command = StepRequest(
                episode_id=reset["episode_id"],
                expected_step_index=0,
                request_id="audited-step",
                action=[0.25, 0.0],
            )
            await manager.step(created["session_id"], command)
            await manager.step(created["session_id"], command)
            with pytest.raises(PlatformError):
                await manager.step(
                    created["session_id"],
                    StepRequest(
                        episode_id=reset["episode_id"],
                        expected_step_index=1,
                        request_id="invalid-step",
                        action=[2.0, 0.0],
                    ),
                )
            now[0] = 111.0
            assert await manager.expire_idle_sessions() == 1
    finally:
        audit_logger.removeHandler(caplog.handler)

    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "libero_remote.audit"
    ]
    by_name = {event["event"]: event for event in events}
    assert {
        "session_reset",
        "step_replayed",
        "step_rejected",
        "session_expired",
    } <= set(by_name)
    assert by_name["session_reset"]["previous_episode_id"] == created["episode_id"]
    assert by_name["step_replayed"]["request_id"] == "audited-step"
    assert by_name["step_replayed"]["cached_outcome"] == "response"
    assert by_name["step_rejected"]["error_code"] == "INVALID_ACTION"
    assert len(by_name["step_rejected"]["action_sha256"]) == 64
    assert by_name["session_expired"]["idle_seconds"] == 11.0


@pytest.mark.asyncio
async def test_idle_session_is_expired_and_releases_worker_capacity() -> None:
    now = [100.0]
    manager = SessionManager(
        backend="fake",
        max_sessions=1,
        worker_timeout_seconds=5.0,
        session_idle_timeout_seconds=10.0,
        clock=lambda: now[0],
    )
    created = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )

    now[0] = 111.0
    expired_count = await manager.expire_idle_sessions()
    snapshot = await manager.get(created["session_id"])

    assert expired_count == 1
    assert snapshot["status"] == "expired"
    replacement = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    await manager.close_all()
    assert replacement["session_id"] != created["session_id"]


@pytest.mark.asyncio
async def test_failed_worker_releases_session_capacity() -> None:
    manager = SessionManager(backend="fake", max_sessions=1, worker_timeout_seconds=5.0)
    created = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    manager._sessions[created["session_id"]].worker.terminate()

    with pytest.raises(PlatformError) as failed:
        await manager.step(
            created["session_id"],
            StepRequest(
                episode_id=created["episode_id"],
                expected_step_index=0,
                request_id="failed-worker-request",
                action=[0.0, 0.0],
            ),
        )
    assert failed.value.code == ErrorCode.WORKER_FAILED

    with pytest.raises(PlatformError) as replayed:
        await manager.step(
            created["session_id"],
            StepRequest(
                episode_id=created["episode_id"],
                expected_step_index=0,
                request_id="failed-worker-request",
                action=[0.0, 0.0],
            ),
        )
    assert replayed.value.code == ErrorCode.WORKER_FAILED

    replacement = await manager.create(
        CreateSessionRequest(camera_height=16, camera_width=16, max_steps=10)
    )
    assert replacement["session_id"] != created["session_id"]
    await manager.close_all()
