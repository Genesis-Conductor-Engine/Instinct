# Genesis Alpha + DRP DAF MCP Integration

This integration registers two production MCP endpoints in the Conductor registry:

- `drp-daf-allocator` (`v0.2.0`) is a Node stdio MCP that owns philanthropic funding synthesis and ledger closure.
- `genesis-alpha-mcp` (`v0.1.0-alpha`) is a Podman-isolated Python MCP that owns mandatory Alpha telemetry persistence in `alpha_traces.db`.

## Shared Ouroboros loop

Both endpoints participate in the same invariant cycle:

1. `poll_state`
2. `kgraph_mapping`
3. `deficit_calculation`
4. `synthesize_gaps`
5. `ledger_update`
6. `close_and_prune`

The shared primitives are `fetch_workspace_state` and `feed_to_k_graph`. State hashes are SHA-256 over canonical JSON with sorted object keys, so equivalent states hash identically regardless of key order. K-graph matching is structural: directed nodes and edges are compared as graph sets; no fuzzy matching, embeddings, or distance thresholds are introduced.

## evt- observability

Every tool call emits a structured `evt-` record to stderr for Conductor/Thrive Monitor ingestion:

```json
{
  "evt_id": "evt_<sha256-prefix>",
  "schema_version": "1.0",
  "record_type": "tool_call",
  "tags": ["mcp", "genesis-alpha"],
  "connections": {"structural_invariant": "DiGraph"},
  "status": "ok",
  "payload": {
    "tool": "feed_to_k_graph",
    "ouroboros_step": "kgraph_mapping",
    "thermodynamic_yield": 0.97,
    "crystal_score": 0.97
  }
}
```

Alpha persists the same evt-native record to SQLite. Example query:

```sql
SELECT evt_id, record_type, ouroboros_step, yolo_override, thermodynamic_yield, crystal_score
FROM alpha_traces
ORDER BY id DESC
LIMIT 10;
```

## YOLO/SOTA bypass gating

`trigger_yolo_swarm` is Alpha-only and activates only when all gates are present:

- `YOLO_MODE=true`
- `x-yolo-override` header
- `x-alpha-token` header

Denied bypass attempts are still logged. Accepted bypass traces deliberately record reduced `thermodynamic_yield` and lower `crystal_score` as explicit Alpha risk telemetry.

## Launch commands

DRP stdio launch:

```bash
node mcp-servers/drp-daf-allocator/scripts/drp-daf-allocator.mjs
```

Alpha Podman launch:

```bash
podman build -t genesis-alpha-mcp:0.1.0-alpha mcp-servers/genesis-alpha-mcp
podman run --rm -e YOLO_MODE=false -e ALPHA_TRACE_DB=/app/data/alpha_traces.db -v ./backend/data:/app/data genesis-alpha-mcp:0.1.0-alpha
```

Local Alpha healthcheck / ProofOfThoughtVerification hook:

```bash
ALPHA_TRACE_DB=backend/data/alpha_traces.db python3 mcp-servers/genesis-alpha-mcp/alpha_mcp_server/main.py healthcheck
```
