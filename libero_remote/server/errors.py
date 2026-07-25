"""Stable platform errors shared by the session and transport modules."""

from typing import Any, Dict, Optional

from libero_remote.protocol.models import ErrorCode


class PlatformError(RuntimeError):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.details = details or {}
