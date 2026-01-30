# Architecture

## Layers & components

```
User Space
  - aiosctl (CLI)         - minimal UI (static HTML/JS)
  - workload clients (OpenAI API)
          |
Control Plane (local) ---------------------- Data Plane (inference)
          |                                        |
  aios-agent (host agent)                 vLLM model server (container)
  - Policy engine                         - OpenAI-compatible API
  - GPU discovery (NVML)                  - batching/timeouts
  - Scheduler (lease-based)               - model cache
  - Runtime launcher (Docker/Podman)
```

## Control plane

- **aios-agent** runs as a privileged-but-minimal local service.
- Responsibilities:
  - Enumerate GPUs via NVML
  - Enforce policy (who can request GPUs, duration limits)
  - Lease-based scheduling (exclusive GPU assignment for MVP)
  - Launch GPU workloads through Docker/Podman
  - Emit metrics for observability

## Data plane

- **vLLM** serves OpenAI-compatible inference APIs.
- Receives GPU allocation (exclusive in MVP).
- Supports batching and request timeouts via vLLM config flags.

## Trust boundaries

1. **User → Agent**: authenticated by local user header / future mTLS.
2. **Agent → Runtime**: only allowlisted images, explicit GPU device mapping.
3. **Runtime → Model server**: no additional privileges; seccomp/AppArmor examples.

## Policy model

- **Users** are defined in `config/aios.yaml`.
- **Quotas**:
  - Max concurrent leases
  - Max lease duration
  - Per-user GPU quotas (for future extension)
- **Access**:
  - Default deny unless user is in `allowed_users`.
