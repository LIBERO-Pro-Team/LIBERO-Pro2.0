#!/usr/bin/env bash
set -euo pipefail

umask 077

bind_address="${LIBERO_REMOTE_BIND_ADDRESS:-127.0.0.1}"
public_port="${LIBERO_REMOTE_PUBLIC_PORT:-8000}"
public_url="${LIBERO_REMOTE_PUBLIC_URL:-http://127.0.0.1:${public_port}}"
if [[ ! "$bind_address" =~ ^[0-9A-Fa-f:.]+$ ]]; then
  echo "LIBERO_REMOTE_BIND_ADDRESS must be an IP address." >&2
  exit 1
fi
if [[ ! "$public_port" =~ ^[0-9]+$ ]] || ((public_port < 1 || public_port > 65535)); then
  echo "LIBERO_REMOTE_PUBLIC_PORT must be between 1 and 65535." >&2
  exit 1
fi
if [[ ! "$public_url" =~ ^https?://[^[:space:]]+$ ]]; then
  echo "LIBERO_REMOTE_PUBLIC_URL must be an http:// or https:// URL." >&2
  exit 1
fi

if [[ -e .env || -e client.env ]]; then
  echo "Refusing to overwrite .env or client.env; remove them explicitly to rotate credentials." >&2
  exit 1
fi

api_key="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
api_hash="$(printf '%s' "$api_key" | sha256sum | awk '{print $1}')"
signing_key="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

cat > .env <<EOF
LIBERO_REMOTE_BIND_ADDRESS=${bind_address}
LIBERO_REMOTE_PUBLIC_PORT=${public_port}
LIBERO_REMOTE_PUBLIC_URL=${public_url}
GPU_ID=all
LIBERO_REMOTE_MAX_SESSIONS=1
LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER=1
LIBERO_REMOTE_WORKER_TIMEOUT_SECONDS=120
LIBERO_REMOTE_SESSION_IDLE_TIMEOUT_SECONDS=900
LIBERO_REMOTE_CLEANUP_INTERVAL_SECONDS=30
LIBERO_REMOTE_API_KEY_HASHES={"${api_hash}":"local-account"}
LIBERO_REMOTE_RESULT_SIGNING_KEY=${signing_key}
LIBERO_REMOTE_IMAGE_DIGEST=
EOF

cat > client.env <<EOF
LIBERO_REMOTE_URL=${public_url}
LIBERO_REMOTE_API_KEY=${api_key}
EOF

chmod 600 .env client.env
echo "Created .env and client.env with mode 0600. Keep client.env private."
