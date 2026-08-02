"""Environment-driven server settings."""

import secrets
from typing import Any, Dict, Optional

from pydantic import BaseSettings, Field, root_validator


class Settings(BaseSettings):
    authentication_required: bool = Field(
        False, env="LIBERO_REMOTE_AUTHENTICATION_REQUIRED"
    )
    api_key_hashes: Dict[str, str] = Field(
        default_factory=dict, env="LIBERO_REMOTE_API_KEY_HASHES"
    )
    result_signing_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        env="LIBERO_REMOTE_RESULT_SIGNING_KEY",
    )
    environment_backend: str = Field("libero", env="LIBERO_REMOTE_BACKEND")
    max_sessions: int = Field(1, ge=1, env="LIBERO_REMOTE_MAX_SESSIONS")
    worker_timeout_seconds: float = Field(60.0, gt=0.0, env="LIBERO_REMOTE_WORKER_TIMEOUT_SECONDS")
    request_cache_size: int = Field(16, ge=1, le=1024, env="LIBERO_REMOTE_CACHE_SIZE")
    session_idle_timeout_seconds: float = Field(
        900.0, gt=0.0, env="LIBERO_REMOTE_SESSION_IDLE_TIMEOUT_SECONDS"
    )
    cleanup_interval_seconds: float = Field(
        30.0, gt=0.0, env="LIBERO_REMOTE_CLEANUP_INTERVAL_SECONDS"
    )
    scheduler_db_path: str = Field(
        "runtime/scheduler.sqlite3", env="LIBERO_REMOTE_SCHEDULER_DB_PATH"
    )
    task_manifest_path: Optional[str] = Field(
        None, env="LIBERO_REMOTE_TASK_MANIFEST"
    )
    scheduler_queue_capacity: int = Field(
        4096, ge=1, env="LIBERO_REMOTE_SCHEDULER_QUEUE_CAPACITY"
    )
    max_attempts: int = Field(3, ge=1, le=100, env="LIBERO_REMOTE_MAX_ATTEMPTS")
    heartbeat_interval_seconds: float = Field(
        15.0, gt=0.0, env="LIBERO_REMOTE_HEARTBEAT_INTERVAL_SECONDS"
    )
    lease_grace_period_seconds: float = Field(
        60.0, gt=0.0, env="LIBERO_REMOTE_LEASE_GRACE_PERIOD_SECONDS"
    )
    max_active_sessions_per_owner: int = Field(
        1, ge=1, env="LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER"
    )
    claim_intent_ttl_seconds: float = Field(
        30.0, gt=0.0, env="LIBERO_REMOTE_CLAIM_INTENT_TTL_SECONDS"
    )
    allow_direct_sessions: bool = Field(
        True, env="LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS"
    )
    host: str = Field("127.0.0.1", env="LIBERO_REMOTE_HOST")
    port: int = Field(8000, ge=1, le=65535, env="LIBERO_REMOTE_PORT")
    log_level: str = Field("info", env="LIBERO_REMOTE_LOG_LEVEL")

    @root_validator
    def validate_scheduler_timeouts(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        heartbeat = values.get("heartbeat_interval_seconds")
        lease_grace = values.get("lease_grace_period_seconds")
        session_idle = values.get("session_idle_timeout_seconds")
        if heartbeat is not None and lease_grace is not None and heartbeat >= lease_grace:
            raise ValueError("lease grace period must be longer than heartbeat interval")
        if heartbeat is not None and session_idle is not None and heartbeat >= session_idle:
            raise ValueError("session idle timeout must be longer than heartbeat interval")
        api_key_hashes = values.get("api_key_hashes") or {}
        if values.get("authentication_required") and not api_key_hashes:
            raise ValueError("authentication requires at least one API key hash")
        for key_hash, owner in api_key_hashes.items():
            try:
                valid_hash = len(key_hash) == 64 and len(bytes.fromhex(key_hash)) == 32
            except ValueError:
                valid_hash = False
            if not valid_hash or not owner.strip():
                raise ValueError(
                    "API key hashes must be 64 hexadecimal characters and account ids nonempty"
                )
        return values

    class Config:
        env_file = ".env"
        case_sensitive = False
