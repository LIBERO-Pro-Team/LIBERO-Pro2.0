#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

[[ -f client.env ]] || { echo "client.env is missing; run ./configure.sh." >&2; exit 1; }
set -a
source client.env
set +a

python3 - \
  "$LIBERO_REMOTE_URL" \
  "$LIBERO_REMOTE_API_KEY" \
  "${LIBERO_REMOTE_HEALTHCHECK_TIMEOUT_SECONDS:-120}" \
  "${LIBERO_REMOTE_HEALTHCHECK_INTERVAL_SECONDS:-2}" <<'PY'
import http.client
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

base_url, api_key, timeout_text, interval_text = sys.argv[1:]
timeout = float(timeout_text)
interval = float(interval_text)
deadline = time.monotonic() + timeout
last_error = "service did not answer"

while True:
    request = Request(
        f"{base_url.rstrip('/')}/v1/health",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urlopen(request, timeout=min(10.0, max(0.1, timeout))) as response:
            payload = json.load(response)
        if payload.get("status") == "ok":
            print(json.dumps(payload, indent=2, sort_keys=True))
            break
        last_error = f"service is not ready: {payload}"
    except (HTTPError, URLError, OSError, ValueError, http.client.HTTPException) as error:
        last_error = f"{type(error).__name__}: {error}"

    if time.monotonic() >= deadline:
        raise SystemExit(f"service did not become ready within {timeout:g}s: {last_error}")
    time.sleep(interval)
PY
