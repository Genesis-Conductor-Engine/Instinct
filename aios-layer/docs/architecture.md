# Architecture

## ASCII diagram (MVP)

```
User space
  - aiosctl (CLI)          - minimal UI (static HTML/JS)
  - workload clients (OpenAI API)
        | Control plane (local)                 | Data plane (inference)
        |                                      |
+-------v--------------------------------------+-----------------------+
| aios-agent (host agent)                                              |
|  - Policy engine (who can run what; quotas; max duration)            |
|  - GPU discovery (nvidia-smi now; NVML in v1)                        |
|  - Scheduler (lease-based; exclusive GPU assignment in MVP)          |
|  - Runtime launcher (Docker/Podman)                                  |
+-----------------------------------------------------------------------+
        |                                              |
        |                                              v
        |                                 +-------------------------+
        |                                 | vLLM model server       |
        |                                 | OpenAI-compatible API   |
        |                                 +-------------------------+
        |
        v
+---------------------+
| Host OS (Ubuntu)    |
| - NVIDIA driver     |
| - container runtime |
+---------------------+
```

## Control vs Data Plane

- **Control plane**: `aios-agent` + policy + scheduler + runtime launcher.
- **Data plane**: model-serving containers with GPU access.

## Trust boundaries

- User/CLI boundary: all user inputs validated by agent.
- Agent/runtime boundary: container runtime uses seccomp/AppArmor.
- Host boundary: minimal privileged operations (Docker socket scoped).

## Policy model

- Each user requests a lease: duration + runtime launch intent.
- Policy constraints enforce max GPUs per user + max duration.
- Scheduler provides exclusive GPU assignments for MVP.
