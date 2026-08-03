#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

account_id="${1:-}"
if [[ ! "$account_id" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "Usage: $0 ACCOUNT_ID (letters, digits, dot, underscore and dash only)" >&2
  exit 1
fi
[[ -f .env ]] || { echo ".env is missing; run ./configure.sh first." >&2; exit 1; }

public_url="$(sed -n 's/^LIBERO_REMOTE_PUBLIC_URL=//p' .env)"
if [[ ! "$public_url" =~ ^https?://[^[:space:]]+$ ]]; then
  echo "LIBERO_REMOTE_PUBLIC_URL is missing or invalid in .env." >&2
  exit 1
fi

umask 077
api_key="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
api_hash="$(printf '%s' "$api_key" | sha256sum | awk '{print $1}')"

python3 - "$account_id" "$api_hash" <<'PY'
import json
import sys
from pathlib import Path

account_id, api_hash = sys.argv[1:]
path = Path(".env")
lines = path.read_text(encoding="utf-8").splitlines()
prefix = "LIBERO_REMOTE_API_KEY_HASHES="
for index, line in enumerate(lines):
    if line.startswith(prefix):
        accounts = json.loads(line[len(prefix):])
        if account_id in accounts.values():
            raise SystemExit(f"account already exists: {account_id}")
        accounts[api_hash] = account_id
        lines[index] = prefix + json.dumps(accounts, separators=(",", ":"), sort_keys=True)
        break
else:
    raise SystemExit("LIBERO_REMOTE_API_KEY_HASHES is missing from .env")
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

client_file="client-${account_id}.env"
cat > "$client_file" <<EOF
LIBERO_REMOTE_URL=${public_url}
LIBERO_REMOTE_API_KEY=${api_key}
EOF
chmod 600 .env "$client_file"
echo "Created $client_file. Run 'docker compose up -d --force-recreate' to activate it."
