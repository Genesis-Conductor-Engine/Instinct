# Operations

## Observability
- Logs: stdout/stderr from `aios-agent`.
- Metrics: `/metrics` endpoint (Prometheus text format).

## Update strategy
- Versioned container images and agent binaries.
- Rollback by pinning previous image tag or binary.

## Signed releases
- Use `cosign` to sign container images and release artifacts.
- Operators verify signatures in CI/CD before deployment.
