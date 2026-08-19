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
    INVALID_TASK = "INVALID_TASK"
    INVALID_ACTION = "INVALID_ACTION"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_CAPACITY_REACHED = "SESSION_CAPACITY_REACHED"
    SESSION_NOT_ACTIVE = "SESSION_NOT_ACTIVE"
    EPISODE_NOT_ACTIVE = "EPISODE_NOT_ACTIVE"
    EPISODE_NOT_FINISHED = "EPISODE_NOT_FINISHED"
    STALE_EPISODE = "STALE_EPISODE"
    REQUEST_ID_CONFLICT = "REQUEST_ID_CONFLICT"
    DUPLICATE_OR_EXPIRED_STEP = "DUPLICATE_OR_EXPIRED_STEP"
    OUT_OF_ORDER_STEP = "OUT_OF_ORDER_STEP"
    WORKER_TIMEOUT = "WORKER_TIMEOUT"
    WORKER_FAILED = "WORKER_FAILED"
    ENVIRONMENT_CREATION_FAILED = "ENVIRONMENT_CREATION_FAILED"
    RUN_NOT_FOUND = "RUN_NOT_FOUND"
    RUN_NOT_ACTIVE = "RUN_NOT_ACTIVE"
    RUN_QUEUE_FULL = "RUN_QUEUE_FULL"
    LEASE_NOT_FOUND = "LEASE_NOT_FOUND"
    LEASE_NOT_ACTIVE = "LEASE_NOT_ACTIVE"
    LEASE_RUNNER_MISMATCH = "LEASE_RUNNER_MISMATCH"
    STALE_LEASE = "STALE_LEASE"
    DIRECT_SESSIONS_DISABLED = "DIRECT_SESSIONS_DISABLED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    REPRODUCIBILITY_MISMATCH = "REPRODUCIBILITY_MISMATCH"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CreateSessionRequest(BaseModel):
    protocol_version: Literal["1.0"] = PROTOCOL_VERSION
    suite: str = "libero_goal"
    task_id: int = Field(0, ge=0)
    init_state_id: int = Field(0, ge=0)
    seed: int = 42
    variant: str = Field("base", min_length=1, max_length=16)
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

    @validator("variant")
    def validate_variant(cls, value: str) -> str:
        normalized = value.strip()
        if normalized.lower() == "base":
            return "base"
        normalized = normalized.upper()
        if len(normalized) != 3 or normalized[0] not in {"S", "D"}:
            raise ValueError("variant must be base, S01-S22, or D01-D21")
        try:
            index = int(normalized[1:])
        except ValueError as exc:
            raise ValueError("variant must be base, S01-S22, or D01-D21") from exc
        valid = (
            normalized[0] == "S" and 1 <= index <= 22
        ) or (
            normalized[0] == "D" and 1 <= index <= 21
        )
        if not valid:
            raise ValueError("variant must be base, S01-S22, or D01-D21")
        return normalized

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
    lease_id: Optional[str] = Field(None, min_length=1, max_length=128)
    lease_generation: Optional[int] = Field(None, ge=1)
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
    translation_frame: Literal["world"]
    rotation_frame: Literal["world"]
    rotation_representation: Literal["axis_angle"]
    gripper_semantics: Literal["negative_open_positive_close_zero_hold"]
    control_freq: int
    action_repeat: int = 1


class ErrorResponse(BaseModel):
    protocol_version: str = PROTOCOL_VERSION
    error_code: ErrorCode
    message: str
    request_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
