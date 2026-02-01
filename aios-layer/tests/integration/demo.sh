#!/usr/bin/env bash
set -euo pipefail

curl -s http://127.0.0.1:8080/v1/health | grep -q ok
curl -s http://127.0.0.1:8080/v1/gpus

curl -s -X POST http://127.0.0.1:8080/v1/leases \
  -H "Content-Type: application/json" \
  -d '{"user":"demo","duration_seconds":60}'

curl -s -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"TinyLlama/TinyLlama-1.1B-Chat-v1.0","messages":[{"role":"user","content":"hello"}]}'
