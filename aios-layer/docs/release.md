# Release & Signing Plan

## Signed releases

- Use **cosign** to sign container images and release artifacts.
- Generate a keyless signature with GitHub OIDC.
- Publish signatures to the OCI registry.

## Update strategy

- Versioned artifacts in `releases/` tagged by semantic version.
- Agent checks for updates when explicitly invoked (no telemetry).
- Rollback by pinning to previous version tag in config or systemd unit.
