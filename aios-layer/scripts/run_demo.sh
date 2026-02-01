#!/usr/bin/env bash
set -euo pipefail

./scripts/check_prereqs.sh

docker build -t aios-layer-agent:local -f docker/agent.Dockerfile .
docker build -t aios-layer-vllm:local -f docker/vllm.Dockerfile .

docker compose -f deploy/docker-compose.yml up -d

sleep 5
curl -s http://127.0.0.1:8080/v1/health
