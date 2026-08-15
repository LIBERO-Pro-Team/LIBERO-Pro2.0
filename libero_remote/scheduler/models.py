"""Public requests and internal state names for scheduled evaluation runs."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from libero_remote.protocol.models import CreateSessionRequest


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(str, Enum):
    QUEUED = "queued"
    ALLOCATING = "allocating"
    LEASED = "leased"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LeaseStatus(str, Enum):
    ACTIVE = "active"
    COMPLETING = "completing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"
    CANCELLED = "cancelled"
    FAILED = "failed"


class SubmitRunRequest(BaseModel):
    # Deprecated for unauthenticated development mode. Authenticated deployments
    # always replace this value with the server-resolved account identity.
    owner_id: Optional[str] = Field(None, min_length=1, max_length=128)
    episodes: List[CreateSessionRequest] = Field(..., min_items=1)

    @validator("owner_id")
    def normalize_owner_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("owner_id must not be empty")
        return normalized


class ClaimRequest(BaseModel):
    runner_id: str = Field(..., min_length=1, max_length=128)

    @validator("runner_id")
    def normalize_runner_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("runner_id must not be empty")
        return normalized


class LeaseCommandRequest(ClaimRequest):
    lease_generation: Optional[int] = Field(None, ge=1)
