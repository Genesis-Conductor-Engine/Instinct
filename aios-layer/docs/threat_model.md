# Threat Model (MVP)

| Threat | Risk | Mitigation |
| --- | --- | --- |
| Container breakout | High | Seccomp + AppArmor profiles; no privileged containers; minimal capabilities |
| Unauthorized GPU access | Medium | Lease-based scheduler and user quotas; audit logs |
| Data exfiltration | Medium | No default telemetry; explicit outbound rules for containers |
| DoS via long jobs | Medium | Max lease duration; reaper for expired leases |
| Supply chain | High | Pinned images; signed releases (cosign plan) |
