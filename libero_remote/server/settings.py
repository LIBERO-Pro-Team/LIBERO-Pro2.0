"""Environment-driven server settings."""

from pydantic import BaseSettings, Field


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
    host: str = Field("127.0.0.1", env="LIBERO_REMOTE_HOST")
    port: int = Field(8000, ge=1, le=65535, env="LIBERO_REMOTE_PORT")
    log_level: str = Field("info", env="LIBERO_REMOTE_LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False
