"""Container health probe using only the Python standard library."""

import json
import os
import sys
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def main() -> None:
    port = os.environ.get("LIBERO_REMOTE_PORT", "8000")
    url = os.environ.get("LIBERO_REMOTE_HEALTH_URL", f"http://127.0.0.1:{port}/v1/health")
    try:
        with urlopen(url, timeout=5.0) as response:
            payload: Dict[str, Any] = json.load(response)
    except (HTTPError, URLError, OSError, ValueError) as error:
        print(f"health check failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    if payload.get("status") != "ok":
        print(f"service is not ready: {payload}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
