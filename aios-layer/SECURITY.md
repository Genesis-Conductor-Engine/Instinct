# Security Policy

## Reporting a Vulnerability

Please report security issues by opening a private security advisory or emailing `security@example.com`. Include:

- A clear description of the issue
- Steps to reproduce
- Impact analysis
- Suggested remediation (if known)

## Supported Versions

Only the latest tagged release is supported for security fixes.

## Secure-by-default posture

- Minimal privileges for containers and services
- Default deny in runtime policy with explicit allowlist for images
- Seccomp/AppArmor examples in `deploy/security/`
- No telemetry unless explicitly enabled by operators
