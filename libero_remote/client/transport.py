"""HTTP transport with explicit retries for idempotent requests only."""

from typing import Any, Dict, Optional

import httpx

from libero_remote.protocol.codec import MESSAGEPACK_MEDIA_TYPE, unpack_message

from .errors import RemoteLiberoError


class HttpTransport:
    def __init__(
        self,
        base_url: str,
        timeout: float,
        http_client: Optional[Any] = None,
    ) -> None:
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout),
        )

    def get_json(self, path: str) -> Dict[str, Any]:
        return self._handle(self._client.get(path))

    def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle(self._client.post(path, json=body))

    def post_idempotent(
        self, path: str, body: Dict[str, Any], transport_retries: int = 2
    ) -> Dict[str, Any]:
        """Retry a request whose payload carries a server-side idempotency key."""

        if transport_retries < 0:
            raise ValueError("transport_retries cannot be negative")
        for attempt in range(transport_retries + 1):
            try:
                return self.post(path, body)
            except httpx.TransportError:
                if attempt == transport_retries:
                    raise
        raise AssertionError("idempotent POST retry loop did not return or raise")

    def delete(self, path: str) -> None:
        response = self._client.delete(path)
        if response.status_code >= 400:
            self._raise_remote_error(response)

    def delete_json(self, path: str) -> Dict[str, Any]:
        return self._handle(self._client.delete(path))

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _handle(self, response: Any) -> Dict[str, Any]:
        if response.status_code >= 400:
            self._raise_remote_error(response)
        content_type = response.headers.get("content-type", "").split(";", 1)[0]
        if content_type == MESSAGEPACK_MEDIA_TYPE:
            decoded = unpack_message(response.content)
            if not isinstance(decoded, dict):
                raise RemoteLiberoError("INVALID_RESPONSE", "Expected a map response", 500)
            return decoded
        decoded = response.json()
        if not isinstance(decoded, dict):
            raise RemoteLiberoError("INVALID_RESPONSE", "Expected a map response", 500)
        return decoded

    @staticmethod
    def _raise_remote_error(response: Any) -> None:
        try:
            error = response.json()
        except Exception:
            error = {}
        raise RemoteLiberoError(
            str(error.get("error_code", "HTTP_ERROR")),
            str(error.get("message", response.text or "Remote request failed")),
            int(response.status_code),
            error.get("request_id"),
            error.get("details"),
        )
