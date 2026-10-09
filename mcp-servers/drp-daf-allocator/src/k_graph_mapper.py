from __future__ import annotations
import hashlib, json

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def state_hash(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

class KGraphMapper:
    def map(self, state):
        nodes = sorted({"workspace", *[str(k) for k in state.keys()]})
        edges = sorted([["workspace", str(k)] for k in state.keys()])
        graph = {"directed": True, "nodes": nodes, "edges": edges}
        deficits = [n for n in ["funding_need", "eligibility", "impact_metric"] if n not in state]
        return {"k_graph": graph, "state_hash": state_hash(state), "graph_hash": state_hash(graph), "deficits": deficits}

def is_subgraph_isomorphic(candidate, target):
    c_edges = {tuple(e) for e in candidate.get("edges", [])}
    t_edges = {tuple(e) for e in target.get("edges", [])}
    c_nodes = set(candidate.get("nodes", []))
    t_nodes = set(target.get("nodes", []))
    return c_nodes.issubset(t_nodes) and c_edges.issubset(t_edges)
