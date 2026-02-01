# Roadmap

## MVP (this repo)
- Single-node agent with GPU leases
- vLLM container runtime
- CLI + static UI

## v1.0
- NVML-based GPU discovery
- Multi-tenant quotas and fair sharing
- Signed releases (cosign)
- Pluggable runtimes (Docker/Podman)

## Multi-node
- Control plane service + worker agents
- GPU-aware scheduling across nodes
- Kubernetes integration (optional)

## Windows/macOS
- Windows: WDDM + DirectML, Hyper-V isolation
- macOS: Metal + HVF

## AMD/Intel
- AMD ROCm integration
- Intel oneAPI/Level-Zero integration
