"""Versioned request, response, and schema models shared by client and server."""

import math
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator

PROTOCOL_VERSION: Literal["1.0"] = "1.0"
OBSERVATION_SCHEMA_VERSION: Literal["libero_standard_v1"] = "libero_standard_v1"
ACTION_SCHEMA_VERSION = "libero_action_v1"


class SessionStatus(str, Enum):
    CREATING = "creating"
    READY = "ready"
    STEPPING = "stepping"
    TERMINATED = "terminated"
    TRUNCATED = "truncated"
    FAILED = "failed"
    CLOSED = "closed"
    EXPIRED = "expired"


class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_ACTION = "INVALID_ACTION"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_CAPACITY_REACHED = "SESSION_CAPACITY_REACHED"
    SESSION_NOT_ACTIVE = "SESSION_NOT_ACTIVE"
    EPISODE_NOT_ACTIVE = "EPISODE_NOT_ACTIVE"
    STALE_EPISODE = "STALE_EPISODE"
    REQUEST_ID_CONFLICT = "REQUEST_ID_CONFLICT"
    DUPLICATE_OR_EXPIRED_STEP = "DUPLICATE_OR_EXPIRED_STEP"
    OUT_OF_ORDER_STEP = "OUT_OF_ORDER_STEP"
    WORKER_TIMEOUT = "WORKER_TIMEOUT"
    WORKER_FAILED = "WORKER_FAILED"
    ENVIRONMENT_CREATION_FAILED = "ENVIRONMENT_CREATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CreateSessionRequest(BaseModel):
    protocol_version: Literal["1.0"] = PROTOCOL_VERSION
    suite: str = "libero_goal"
    task_id: int = Field(0, ge=0)
    init_state_id: int = Field(0, ge=0)
    seed: int = 42
    variant: Literal["base"] = "base"
    control_mode: Literal["relative", "absolute"] = "relative"
    camera_names: List[str] = Field(default_factory=lambda: ["agentview", "robot0_eye_in_hand"])
    camera_height: int = Field(128, ge=16, le=1024)
    camera_width: int = Field(128, ge=16, le=1024)
    max_steps: int = Field(300, ge=1, le=5000)
    observation_schema_version: Literal["libero_standard_v1"] = OBSERVATION_SCHEMA_VERSION

    @validator("suite")
    def validate_suite(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("suite must not be empty")
        return value

    @validator("camera_names")
    def validate_camera_names(cls, value: List[str]) -> List[str]:
        if not value or len(value) > 8 or any(not item.strip() for item in value):
            raise ValueError("camera_names must contain between one and eight names")
        if len(value) != len(set(value)):
            raise ValueError("camera_names must not contain duplicates")
        return value


class ResetRequest(BaseModel):
    init_state_id: int = Field(0, ge=0)
    seed: int = 42


class StepRequest(BaseModel):
    episode_id: str = Field(..., min_length=1, max_length=128)
    expected_step_index: int = Field(..., ge=0)
    request_id: str = Field(..., min_length=1, max_length=128)
    action: List[float] = Field(..., min_items=1, max_items=128)

    @validator("action")
    def validate_finite_action(cls, value: List[float]) -> List[float]:
        if not all(math.isfinite(item) for item in value):
            raise ValueError("action values must be finite")
        return value


class ArraySchema(BaseModel):
    shape: List[int]
    dtype: str
    byte_order: str = "little"
    layout: Literal["C"] = "C"


class ActionSchema(BaseModel):
    version: str = ACTION_SCHEMA_VERSION
    shape: List[int]
    dtype: str = "float32"
    low: List[float]
    high: List[float]
    controller: str
    control_mode: Literal["relative", "absolute"]
    control_freq: int
    action_repeat: int = 1


class ErrorResponse(BaseModel):
    protocol_version: str = PROTOCOL_VERSION
    error_code: ErrorCode
    message: str
    request_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
