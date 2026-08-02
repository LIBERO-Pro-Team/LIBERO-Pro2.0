#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

[[ -f client.env ]] || { echo "client.env is missing; run ./configure.sh." >&2; exit 1; }
set -a
source client.env
set +a

python3 - "$LIBERO_REMOTE_URL" "$LIBERO_REMOTE_API_KEY" <<'PY'
import json
import sys
from urllib.request import Request, urlopen

base_url, api_key = sys.argv[1:]
request = Request(
    f"{base_url.rstrip('/')}/v1/health",
    headers={"Authorization": f"Bearer {api_key}"},
)
with urlopen(request, timeout=10) as response:
    payload = json.load(response)
if payload.get("status") != "ok":
    raise SystemExit(f"service is not ready: {payload}")
print(json.dumps(payload, indent=2, sort_keys=True))
PY

