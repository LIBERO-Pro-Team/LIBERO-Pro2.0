#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

command -v docker >/dev/null || { echo "Docker is required." >&2; exit 1; }
docker compose version >/dev/null || { echo "Docker Compose v2 is required." >&2; exit 1; }
command -v nvidia-smi >/dev/null || { echo "NVIDIA driver is required." >&2; exit 1; }
docker info >/dev/null || { echo "Current user cannot access the Docker daemon." >&2; exit 1; }

if [[ ! -f .env || ! -f client.env ]]; then
  ./configure.sh
fi

sha256sum -c SHA256SUMS
chmod +x configure.sh add_account.sh install.sh healthcheck.sh
docker load -i images/libero-pro-server-1.0.0.tar

image_id="$(docker image inspect libero-pro-server:1.0.0 --format '{{.Id}}')"
sed -i "s|^LIBERO_REMOTE_IMAGE_DIGEST=.*|LIBERO_REMOTE_IMAGE_DIGEST=${image_id}|" .env

mkdir -p runtime logs
docker compose up -d
./healthcheck.sh

echo "Service is running. Install the SDK with:"
echo "  python3 -m pip install wheels/libero_remote-1.0.0-py3-none-any.whl"
