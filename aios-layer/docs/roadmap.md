# Roadmap

## MVP (this repo)

- Single-machine agent + vLLM inference
- Exclusive GPU lease scheduling
- CLI + optional UI
- Basic policy engine

## v1.0

- Multi-user auth (mTLS, OIDC)
- Fair-share scheduling and time-slicing
- Model cache management
- Persistent state for leases
- Automated updates + rollback

## Multi-node (v2)

- Cluster coordinator
- GPU-aware scheduling across nodes
- Node attestation and signed agent registration

## Windows/macOS support

- **Windows**: use WDDM + DirectML, Hyper-V isolation option.
- **macOS**: use Metal backend, Apple HVF for VM isolation.

## AMD/Intel support

- **AMD**: ROCm container runtime + GPU discovery via rocm-smi.
- **Intel**: oneAPI Level-Zero and Intel GPU plugin for containers.
