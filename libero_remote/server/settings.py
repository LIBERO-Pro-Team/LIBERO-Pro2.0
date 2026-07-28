"""Environment-driven server settings."""

from typing import Any, Dict

from pydantic import BaseSettings, Field, root_validator


class Settings(BaseSettings):
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
    scheduler_queue_capacity: int = Field(
        4096, ge=1, env="LIBERO_REMOTE_SCHEDULER_QUEUE_CAPACITY"
    )
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
        return values

    class Config:
        env_file = ".env"
        case_sensitive = False
