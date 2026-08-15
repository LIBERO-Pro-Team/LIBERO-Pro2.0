"""Bearer API-key authentication with server-owned account identities."""

import hashlib
import secrets
from typing import Dict, Optional

from fastapi import Header

from libero_remote.protocol.models import ErrorCode

from .errors import PlatformError


class ApiKeyAuthenticator:
    def __init__(self, required: bool, api_key_hashes: Dict[str, str]) -> None:
        self._required = required
        self._api_key_hashes = {
            key_hash.lower(): owner_id for key_hash, owner_id in api_key_hashes.items()
        }

    def __call__(self, authorization: Optional[str] = Header(None)) -> Optional[str]:
        if authorization is None:
            if not self._required:
                return None
            raise PlatformError(
                ErrorCode.AUTHENTICATION_REQUIRED,
                "A Bearer API key is required",
                status_code=401,
            )
        scheme, separator, credential = authorization.partition(" ")
        if separator != " " or scheme.lower() != "bearer" or not credential:
            raise PlatformError(
                ErrorCode.INVALID_CREDENTIALS,
                "The Authorization header must contain a valid Bearer API key",
                status_code=401,
            )
        supplied_hash = hashlib.sha256(credential.encode("utf-8")).hexdigest()
        for key_hash, owner_id in self._api_key_hashes.items():
            if secrets.compare_digest(supplied_hash, key_hash):
                return owner_id
        raise PlatformError(
            ErrorCode.INVALID_CREDENTIALS,
            "The supplied API key is not valid",
            status_code=401,
        )
