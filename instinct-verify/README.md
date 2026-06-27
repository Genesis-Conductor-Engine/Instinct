# Instinct Verify — Sovereign Edition v0.1

> Post-Quantum Cryptography + Thermodynamic Instrumentation + Genesis Conductor MCP

Built at Green Haven Node • 2026-06-22 • Operator: igor@kovachenterprises.com

## Stack

- Vite + React 18 + TypeScript + Tailwind CSS 3
- Lucide React icons
- Genesis Conductor MCP endpoint (gc-mcp.iholt.workers.dev)

## Sovereign Integrations

### PQC — Falcon-512 + ML-DSA
Every verification carries a PQC signature. Currently simulated; wire to Diamond NV-center signing path via MCP agent for real Dilithium/Falcon operations.

### Thermodynamic Instrumentation (TAO)
Every ledger entry records energy_kwh, landauer_pct, power_w, and yield_note. Wire RAPL/NVML/eBPF telemetry from the sandboxed execution container into the thermo object via the existing thermodynamic_kernel.py.

### Genesis Conductor MCP
Submit via MCP button routes to gc-mcp.iholt.workers.dev / gc-mcp.genesisconductor.io (once deployed). Uses submit_opus_task tool for dual-LLM adjudication (Opus 4.8 + Haiku 4.5). Falls back to sovereign simulation.

### evt- Observability
Every verification produces a structured evt-ver-* record. Visible in the dashboard observability stream. Ready for integration with existing evt-processor skill and Genesis Conductor logging.

## Run

```bash
cd instinct-verify
npm install
npm run dev
```

## Deploy

```bash
npm run build
# dist/ → Cloudflare Pages or Workers Sites
wrangler pages deploy dist --project-name instinct-verify
```

## Revenue Activation

- Tier 1: Sovereign Starter — $299/mo, 50 verifications
- Tier 2: Operator Pro — $990/mo, 500 verifications + full PQC stack
- Tier 3: Coalition Enterprise — Custom, unlimited + Diamond NV signing + FedRAMP + OPC

## Next Steps

1. Wire real MCP backend — replace submitSovereignVerification simulation with gc-mcp tool call
2. Add real PQC — call Falcon-512 / ML-DSA from Diamond NV-center path via MCP agent
3. Thermodynamic real data — pipe RAPL/NVML from thermodynamic_kernel.py
4. Deploy frontend to Cloudflare Pages
5. Revenue activation — first 10 paying customers from existing network + OPC

## evt- Record

```json
{
  "evt_id": "tunnel-through-20260622T0224Z-instinct-verify-sovereign-wired",
  "schema_version": "1.0",
  "record_type": "execution_complete",
  "status": "through",
  "tags": ["tunnel-through", "instinct-verify", "genesis-conductor", "pqc", "thermodynamic", "mcp-integration", "revenue-stream"]
}
```
