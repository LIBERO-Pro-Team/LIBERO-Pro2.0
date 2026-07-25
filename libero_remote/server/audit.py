"""Stable, image-free JSON audit events for remote environment operations."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

AUDIT_SCHEMA_VERSION = "1.0"
_LOGGER = logging.getLogger("libero_remote.audit")
_LOGGER.setLevel(logging.INFO)
_LOGGER.propagate = False
_HANDLER = logging.StreamHandler()
_HANDLER.setFormatter(logging.Formatter("%(message)s"))
_LOGGER.addHandler(_HANDLER)


def emit_audit(event: str, **fields: Any) -> None:
    payload = {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    _LOGGER.info(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    )
