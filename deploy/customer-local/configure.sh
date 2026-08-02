#!/usr/bin/env bash
set -euo pipefail

umask 077

if [[ -e .env || -e client.env ]]; then
  echo "Refusing to overwrite .env or client.env; remove them explicitly to rotate credentials." >&2
  exit 1
fi

api_key="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
api_hash="$(printf '%s' "$api_key" | sha256sum | awk '{print $1}')"
signing_key="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

cat > .env <<EOF
LIBERO_REMOTE_PUBLIC_PORT=8000
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
LIBERO_REMOTE_URL=http://127.0.0.1:8000
LIBERO_REMOTE_API_KEY=${api_key}
EOF

chmod 600 .env client.env
echo "Created .env and client.env with mode 0600. Keep client.env private."

