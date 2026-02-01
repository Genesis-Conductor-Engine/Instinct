#!/usr/bin/env bash
set -euo pipefail

command -v docker >/dev/null 2>&1 || { echo "docker not found"; exit 1; }
command -v nvidia-smi >/dev/null 2>&1 || { echo "nvidia-smi not found (GPU optional)"; }

echo "Prereqs ok"
