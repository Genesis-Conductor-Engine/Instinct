#!/usr/bin/env bash
set -euo pipefail

ENDPOINT="${1:-http://localhost:8000/v1/completions}"
MODEL="${2:-aios-demo}"

PAYLOAD=$(jq -n --arg model "$MODEL" --arg prompt "Benchmark run" --argjson max_tokens 64 \
  '{model:$model,prompt:$prompt,max_tokens:$max_tokens}')

echo "Benchmarking $ENDPOINT ($MODEL)"

START=$(date +%s%3N)
RESPONSE=$(curl -fsS -X POST "$ENDPOINT" -H "Content-Type: application/json" -d "$PAYLOAD")
END=$(date +%s%3N)

LATENCY=$((END - START))
TOKENS=$(echo "$RESPONSE" | jq -r '.usage.total_tokens // 0')

echo "Latency_ms=$LATENCY"
echo "Total_tokens=$TOKENS"
