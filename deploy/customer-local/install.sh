#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

command -v docker >/dev/null || { echo "Docker is required." >&2; exit 1; }
docker compose version >/dev/null || { echo "Docker Compose v2 is required." >&2; exit 1; }
command -v nvidia-smi >/dev/null || { echo "NVIDIA driver is required." >&2; exit 1; }
docker info >/dev/null || { echo "Current user cannot access the Docker daemon." >&2; exit 1; }

if [[ ! -f .env || ! -f client.env ]]; then
  bash configure.sh
fi

sha256sum -c SHA256SUMS
chmod +x configure.sh add_account.sh install.sh healthcheck.sh
docker load -i images/libero-pro-server-1.0.0.tar

if ! docker run --rm --gpus all \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics \
  --entrypoint nvidia-smi \
  libero-pro-server:1.0.0 >/dev/null 2>&1; then
  echo "Docker cannot access the NVIDIA GPU. Install or repair NVIDIA Container Toolkit." >&2
  exit 1
fi

image_id="$(docker image inspect libero-pro-server:1.0.0 --format '{{.Id}}')"
sed -i "s|^LIBERO_REMOTE_IMAGE_DIGEST=.*|LIBERO_REMOTE_IMAGE_DIGEST=${image_id}|" .env

mkdir -p runtime logs
docker compose up -d
bash healthcheck.sh

echo "Service is running. Install the SDK with:"
echo "  python3 -m pip install --no-index --find-links wheels wheels/libero_remote-1.0.0-py3-none-any.whl"
