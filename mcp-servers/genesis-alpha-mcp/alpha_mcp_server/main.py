#!/usr/bin/env python3
"""Genesis Alpha MCP primitives: structural evt telemetry, deterministic hashing, gated YOLO."""
from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, sys, time
from pathlib import Path
from typing import Any

CYCLE_STEPS = ["poll_state", "kgraph_mapping", "deficit_calculation", "synthesize_gaps", "ledger_update", "close_and_prune"]
DB_PATH = Path(os.environ.get("ALPHA_TRACE_DB", "/app/data/alpha_traces.db"))


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def state_hash(state: Any) -> str:
    return hashlib.sha256(canonical(state).encode()).hexdigest()


def thermodynamic_yield(payload: dict[str, Any], *, yolo_override: bool = False) -> float:
    bits = max(len(canonical(payload).encode()) * 8, 1)
    useful = len(payload.get("connections", {}) or {}) + len(payload.get("tags", []) or []) + 1
    base = min(0.99, useful / (useful + bits / 4096.0))
    return round(base * (0.42 if yolo_override else 1.0), 6)


def evt(record_type: str, status: str, payload: dict[str, Any], tags: list[str] | None = None, connections: dict[str, Any] | None = None) -> dict[str, Any]:
    yolo = bool(payload.get("yolo_override"))
    rec = {
        "evt_id": "evt_" + hashlib.sha256(f"{time.time_ns()}:{record_type}:{canonical(payload)}".encode()).hexdigest()[:24],
        "schema_version": "1.0",
        "record_type": record_type,
        "tags": ["mcp", "genesis-alpha", *(tags or [])],
        "connections": connections or {},
        "status": status,
        "payload": {
            **payload,
            "thermodynamic_yield": payload.get("thermodynamic_yield", thermodynamic_yield(payload, yolo_override=yolo)),
            "crystal_score": payload.get("crystal_score", 0.61 if yolo else 0.97),
        },
    }
    print("evt-" + canonical(rec), file=sys.stderr, flush=True)
    return rec


def init_db(path: Path = DB_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS alpha_traces (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          evt_id TEXT UNIQUE NOT NULL,
          schema_version TEXT NOT NULL,
          record_type TEXT NOT NULL,
          tags TEXT NOT NULL,
          connections TEXT NOT NULL,
          status TEXT NOT NULL,
          payload TEXT NOT NULL,
          yolo_override INTEGER NOT NULL DEFAULT 0,
          thermodynamic_yield REAL NOT NULL,
          crystal_score REAL NOT NULL,
          ouroboros_step TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_alpha_traces_step ON alpha_traces(ouroboros_step)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_alpha_traces_yolo ON alpha_traces(yolo_override)")
    return path


def log_alpha_trace(record: dict[str, Any], db_path: Path = DB_PATH) -> dict[str, Any]:
    init_db(db_path)
    payload = record.get("payload", {})
    with sqlite3.connect(db_path) as con:
        con.execute("""INSERT OR IGNORE INTO alpha_traces
        (evt_id,schema_version,record_type,tags,connections,status,payload,yolo_override,thermodynamic_yield,crystal_score,ouroboros_step)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
            record["evt_id"], record["schema_version"], record["record_type"], canonical(record.get("tags", [])),
            canonical(record.get("connections", {})), record["status"], canonical(payload), int(bool(payload.get("yolo_override"))),
            float(payload.get("thermodynamic_yield", 0.0)), float(payload.get("crystal_score", 0.0)), payload.get("ouroboros_step")
        ))
    return {"ok": True, "evt_id": record["evt_id"], "db_path": str(db_path)}


def fetch_workspace_state(workspace: dict[str, Any] | None = None) -> dict[str, Any]:
    state = workspace or {"documents": [], "ledger": [], "proposals": []}
    result = {"workspace_state": state, "state_hash": state_hash(state), "ouroboros_step": "poll_state"}
    log_alpha_trace(evt("tool_call", "ok", {**result, "tool": "fetch_workspace_state"}, ["poll_state"]))
    return result


def feed_to_k_graph(state: dict[str, Any]) -> dict[str, Any]:
    nodes = sorted({str(k) for k in state.keys()} | {"workspace"})
    edges = sorted([["workspace", str(k)] for k in state.keys()])
    graph = {"directed": True, "nodes": nodes, "edges": edges}
    result = {"k_graph": graph, "state_hash": state_hash(state), "graph_hash": state_hash(graph), "deficits": [n for n in ["funding_need", "eligibility", "impact_metric"] if n not in state], "ouroboros_step": "kgraph_mapping"}
    log_alpha_trace(evt("tool_call", "ok", {**result, "tool": "feed_to_k_graph"}, ["kgraph_mapping"], {"structural_invariant": "DiGraph"}))
    return result


def trigger_yolo_swarm(headers: dict[str, str], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    allowed = os.environ.get("YOLO_MODE", "").lower() == "true" and bool(headers.get("x-yolo-override")) and bool(headers.get("x-alpha-token"))
    status = "accepted" if allowed else "denied"
    rec = evt("yolo_bypass", status, {"tool": "trigger_yolo_swarm", "yolo_override": allowed, "ouroboros_step": "synthesize_gaps", "headers_present": sorted(headers)}, ["yolo", "alpha-gated"])
    log_alpha_trace(rec)
    if not allowed:
        raise PermissionError("YOLO bypass requires YOLO_MODE=true plus x-yolo-override and x-alpha-token headers")
    return {"ok": True, "mode": "yolo_swarm", "trace": rec, "payload": payload or {}}


def healthcheck() -> dict[str, Any]:
    init_db(); rec=evt("healthcheck","ok",{"tool":"healthcheck","ouroboros_step":"poll_state"},["ProofOfThoughtVerification"]); log_alpha_trace(rec); return {"ok": True, "db_path": str(DB_PATH), "cycle_steps": CYCLE_STEPS}

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("command", choices=["init-db","healthcheck"]); a=p.parse_args()
    print(json.dumps(init_db() and healthcheck() if a.command=="healthcheck" else {"ok": True, "db_path": str(init_db())}))
