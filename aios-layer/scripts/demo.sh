#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting AIOS stack (GPU profile)..."
docker compose -f "$ROOT_DIR/deploy/docker/docker-compose.yaml" --profile gpu up -d --build

echo "Waiting for agent..."
until curl -fsS http://localhost:8088/v1/health >/dev/null 2>&1; do
  sleep 1
done

echo "Requesting GPU lease..."
LEASE_JSON=$(curl -fsS -X POST http://localhost:8088/v1/leases \
  -H "Content-Type: application/json" \
  -d '{"user":"local","lease_seconds":900,"allow_any_gpu":true}')

LEASE_ID=$(echo "$LEASE_JSON" | jq -r '.id')
GPU_INDEX=$(echo "$LEASE_JSON" | jq -r '.gpu_index')
echo "Lease $LEASE_ID on GPU $GPU_INDEX"

echo "Launching vLLM container via agent..."
curl -fsS -X POST http://localhost:8088/v1/launch \
  -H "Content-Type: application/json" \
  -d "{\"user\":\"local\",\"lease_id\":\"$LEASE_ID\",\"image\":\"vllm/vllm-openai:v0.6.3\",\"gpu\":$GPU_INDEX,\"command\":[\"--model\",\"TinyLlama/TinyLlama-1.1B-Chat-v1.0\",\"--served-model-name\",\"aios-demo\",\"--port\",\"8000\"],\"env\":[\"HF_HOME=/data/hf\",\"VLLM_LOGGING_LEVEL=info\"]}" | jq .

echo "Querying model via aiosctl..."
go run ./cli -endpoint http://localhost:8000/v1/completions -model aios-demo -prompt "Hello from AIOS demo" -max-tokens 32
