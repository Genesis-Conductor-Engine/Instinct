#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports

{
  echo "== Test run (count=2) =="
  go test -count=2 ./agent/... ./cli/...
} | tee reports/test.log

{
  echo "== Bench run (count=2) =="
  go test ./agent/... -run ^$ -bench . -benchmem -count=2
} | tee reports/bench.log
