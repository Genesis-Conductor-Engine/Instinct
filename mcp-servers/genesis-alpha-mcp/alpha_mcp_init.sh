#!/usr/bin/env bash
set -euo pipefail
export ALPHA_TRACE_DB="${ALPHA_TRACE_DB:-/app/data/alpha_traces.db}"
python3 /app/alpha_mcp_server/main.py init-db
python3 /app/alpha_mcp_server/main.py healthcheck
