#!/usr/bin/env bash
set -euo pipefail

echo "== Agent health =="
curl -fsS http://localhost:8088/v1/health | jq .

echo "== GPUs =="
curl -fsS http://localhost:8088/v1/gpus | jq .

echo "== Leases =="
curl -fsS http://localhost:8088/v1/leases | jq .
