"""Client-side representation of stable server errors."""

from typing import Any, Dict, Optional


class RemoteLiberoError(RuntimeError):
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(f"{error_code}: {message}")
        self.error_code = error_code
        self.status_code = status_code
        self.request_id = request_id
        self.details = details or {}
