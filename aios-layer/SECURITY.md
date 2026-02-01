# Security Policy

## Reporting

Please report security issues by opening a private security advisory in the repository.

## Supported versions

Only the latest release is supported.

## Hardening

- Run `aios-agent` as a non-root user.
- Use AppArmor and seccomp profiles in `deploy/security`.
- Avoid granting containers additional capabilities.
