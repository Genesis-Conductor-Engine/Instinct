# Threat Model

| Threat | Impact | Mitigation |
| --- | --- | --- |
| Unauthorized GPU use | Resource theft, denial of service | Allowlisted users, lease timeouts, max concurrent leases |
| Container escape | Host compromise | Seccomp/AppArmor profiles, no-new-privileges, cap drop |
| Supply chain attack on images | Malicious runtime | Image allowlist, pinned image tags, signed releases plan |
| Agent API abuse | Job flooding, quota bypass | Request validation, quotas, future authn via mTLS |
| GPU data leakage | Data exposure between workloads | Exclusive GPU leases in MVP, secure cleanup |
| Metrics scraping | Information disclosure | Local-only listen by default, configurable |
