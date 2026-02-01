# AIOS Layer (MVP)

AIOS Layer is a reproducible, secure-by-default AI/GPU “OS-style layer” that runs on top of an existing host OS. It provides a minimal host agent, GPU-aware scheduling, runtime launch hooks, and a CLI + optional UI for inference workflows.

## 10-minute Quickstart (Ubuntu 24.04 + NVIDIA)

1) **Install prerequisites**

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
# NVIDIA drivers + container toolkit (see docs below)
```

2) **Build + run**

```bash
cd aios-layer
make build
./scripts/run_demo.sh
```

3) **Request a lease + run inference**

```bash
./bin/aiosctl lease --agent http://127.0.0.1:8080 --user demo --duration 300
./bin/aiosctl infer --endpoint http://127.0.0.1:8000/v1/chat/completions --prompt "Hello from AIOS"
```

4) **Open the UI**

```bash
python3 -m http.server 9000 -d ui
# visit http://127.0.0.1:9000/index.html
```

## Architecture Overview

- **Control plane**: `aios-agent` manages GPU discovery, scheduling, policy enforcement, and runtime launch.
- **Data plane**: model servers run in containers (vLLM in the MVP).
- **Interface**: `aiosctl` CLI and a static UI.

See `docs/architecture.md` for diagrams and rationale.

## NVIDIA GPU Integration (MVP)

- Driver + `nvidia-container-toolkit` required for GPU containers.
- GPU discovery via `nvidia-smi` (NVML alternative in v1).
- Scheduler uses exclusive GPU leases (time-based).
- CPU-only fallback is enabled when no GPU is detected.

## Security

- Minimal privileges for the agent and containers.
- Example seccomp + AppArmor profiles in `deploy/security`.
- No telemetry; metrics are local-only.

## Tests

```bash
make test
./scripts/run_checks.sh
```

Test and benchmark logs are written to `reports/` when using `./scripts/run_checks.sh`.

## License

MIT
