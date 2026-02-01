#!/usr/bin/env bash
set -euo pipefail

MODEL_ENDPOINT=${MODEL_ENDPOINT:-http://127.0.0.1:8000/v1/chat/completions}
MODEL=${MODEL:-TinyLlama/TinyLlama-1.1B-Chat-v1.0}

python3 - <<'PY'
import json
import os
import time
import urllib.request

endpoint = os.environ.get("MODEL_ENDPOINT")
model = os.environ.get("MODEL")

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Summarize GPU scheduling."}],
    "max_tokens": 64,
    "temperature": 0.2,
}

data = json.dumps(payload).encode("utf-8")

start = time.time()
req = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    resp.read()
end = time.time()

print(f"latency_ms={(end-start)*1000:.2f}")
PY

nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits || true
