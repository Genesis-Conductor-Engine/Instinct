# AIOS Layer (MVP)

AIOS Layer is an **OS-style control plane** that runs on top of existing operating systems and infrastructure to manage AI/GPU workloads. It provides a minimal host agent, a GPU-aware runtime launcher, a CLI, and an optional UI. The MVP targets **Ubuntu 24.04 + NVIDIA** with a vLLM inference server. This repo also includes a CPU fallback path using vLLM's CPU backend (see notes).  

## 10-minute quickstart (Ubuntu 24.04 + NVIDIA)

> **Prereqs**: Docker Engine, NVIDIA driver, NVIDIA Container Toolkit.

```bash
cd aios-layer
./scripts/install.sh
```

Start the stack (GPU path):

```bash
docker compose -f deploy/docker/docker-compose.yaml --profile gpu up -d --build
```

Verify agent + GPU discovery:

```bash
curl -fsS http://localhost:8088/v1/health | jq .
curl -fsS http://localhost:8088/v1/gpus | jq .
```

Run inference via CLI:

```bash
go run ./cli -endpoint http://localhost:8000/v1/completions -model aios-demo -prompt "Hello from AIOS Layer" -max-tokens 64
```

Optional minimal UI:

```bash
docker compose -f deploy/docker/docker-compose.yaml --profile ui up -d
open http://localhost:8080
```

CPU fallback (if no GPU):

```bash
docker compose -f deploy/docker/docker-compose.yaml --profile cpu up -d
go run ./cli -endpoint http://localhost:8001/v1/completions -model aios-demo-cpu -prompt "CPU fallback" -max-tokens 32
```

## Configuration

All settings are in **`config/aios.yaml`** (single source of truth).  
The host agent reads this file on startup for policy, runtime, and GPU discovery settings.

## Build

```bash
make build
```

## systemd (host agent)

```bash
sudo useradd -r -s /usr/sbin/nologin aios || true
sudo install -m 0755 bin/aios-agent /usr/local/bin/aios-agent
sudo install -D -m 0644 config/aios.yaml /etc/aios/aios.yaml
sudo install -D -m 0644 deploy/systemd/aios-agent.service /etc/systemd/system/aios-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now aios-agent
```

## Tests

```bash
make test
./tests/integration/stack.sh
```

## Docs

- Architecture: `docs/architecture.md`
- Threat model: `docs/threat-model.md`
- Roadmap: `docs/roadmap.md`
- Full report (requested format): `docs/report.md`
- Release/signing plan: `docs/release.md`

## Notes

- The MVP uses **vLLM** for an OpenAI-compatible inference API.
- GPU scheduling is **exclusive** per GPU in the MVP.
- CPU fallback relies on vLLM CPU backend; performance is limited.
- Telemetry is **off by default**; no data is sent unless explicitly enabled.
