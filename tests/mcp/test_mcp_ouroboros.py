from __future__ import annotations
import importlib.util, json, os, sqlite3, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALPHA = ROOT / "mcp-servers/genesis-alpha-mcp/alpha_mcp_server/main.py"
DRP = ROOT / "mcp-servers/drp-daf-allocator/scripts/drp-daf-allocator.mjs"

def load_alpha(tmp_path):
    os.environ["ALPHA_TRACE_DB"] = str(tmp_path / "alpha_traces.db")
    spec = importlib.util.spec_from_file_location("alpha_main", ALPHA)
    mod = importlib.util.module_from_spec(spec); sys.modules["alpha_main"] = mod; spec.loader.exec_module(mod)
    mod.DB_PATH = Path(os.environ["ALPHA_TRACE_DB"])
    return mod

def test_invariant_state_hash_order_independent(tmp_path):
    a = load_alpha(tmp_path)
    assert a.state_hash({"b": 2, "a": [3, 1]}) == a.state_hash({"a": [3, 1], "b": 2})

def test_alpha_telemetry_persistence_and_shared_tools(tmp_path):
    a = load_alpha(tmp_path)
    state = a.fetch_workspace_state({"funding_need": 10, "eligibility": True, "impact_metric": "meals"})
    graph = a.feed_to_k_graph(state["workspace_state"])
    assert graph["deficits"] == []
    with sqlite3.connect(os.environ["ALPHA_TRACE_DB"]) as con:
        assert con.execute("select count(*) from alpha_traces").fetchone()[0] >= 2

def test_yolo_requires_env_and_two_headers(tmp_path, monkeypatch):
    a = load_alpha(tmp_path)
    monkeypatch.setenv("YOLO_MODE", "true")
    try:
        a.trigger_yolo_swarm({"x-yolo-override": "1"})
        raise AssertionError("gate should deny missing x-alpha-token")
    except PermissionError:
        pass
    out = a.trigger_yolo_swarm({"x-yolo-override": "1", "x-alpha-token": "token"})
    assert out["trace"]["payload"]["thermodynamic_yield"] < 0.5
    assert out["trace"]["payload"]["crystal_score"] < 0.7

def test_drp_full_cycle_and_evt_stderr(tmp_path):
    env = {**os.environ, "ALPHA_TRACE_DB": str(tmp_path / "alpha_traces.db"), "ALPHA_TRACE_JSONL": str(tmp_path / "alpha_traces.drp.jsonl")}
    req = {"tool": "fetch_workspace_state", "arguments": {"workspace": {"funding_need": 1}}}
    p = subprocess.run(["node", str(DRP)], input=json.dumps(req), text=True, capture_output=True, env=env, check=True)
    assert json.loads(p.stdout)["ouroboros_step"] == "poll_state"
    assert "evt-" in p.stderr
    req2 = {"tool": "close_ouroboros_cycle", "arguments": {"ok": True}}
    subprocess.run(["node", str(DRP)], input=json.dumps(req2), text=True, capture_output=True, env=env, check=True)
    assert Path(env["ALPHA_TRACE_JSONL"]).exists()

def test_registry_contains_both_servers():
    reg = json.loads((ROOT / "mcp-registry.json").read_text())
    assert {s["name"] for s in reg["servers"]} >= {"drp-daf-allocator", "genesis-alpha-mcp"}
