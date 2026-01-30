#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not available. Skipping integration test."
  exit 0
fi

docker compose -f "$ROOT_DIR/deploy/docker/docker-compose.yaml" --profile gpu up -d --build
trap 'docker compose -f "$ROOT_DIR/deploy/docker/docker-compose.yaml" down' EXIT

echo "Waiting for agent..."
until curl -fsS http://localhost:8088/v1/health >/dev/null 2>&1; do
  sleep 1
done

curl -fsS http://localhost:8088/v1/gpus >/dev/null
echo "Integration test passed."
