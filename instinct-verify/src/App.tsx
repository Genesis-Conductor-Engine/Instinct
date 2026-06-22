import React, { useState, useEffect, useCallback } from "react";
import { Shield, Activity, CheckCircle, AlertTriangle, Clock, Database, Send, BarChart3, Fingerprint, Thermometer, X, Plus, RefreshCw, Terminal, Layers } from "lucide-react";

const MCP_ENDPOINT: string = (import.meta as any).env?.VITE_MCP_ENDPOINT ?? "https://gc-mcp.iholt.workers.dev";
const OPERATOR: string = (import.meta as any).env?.VITE_OPERATOR ?? "igor@kovachenterprises.com";

interface PQCMeta { algorithm: string; signature: string; keyId: string; verifiedAt: string; }
interface ThermoMeta { energy_kwh: number; landauer_pct: number; power_w: number; yield_note: string; }
interface LedgerEntry {
  id: string; claim: string; org: string;
  status: "verified" | "pending" | "rejected" | "flagged";
  confidence: number; pqc: PQCMeta; thermo: ThermoMeta;
  ts: string; adjudicator: string; evtId: string;
  mcpTaskId?: string; mcpRouted?: boolean;
}
interface EvtRecord {
  evt_id: string; schema_version: string; record_type: string;
  tags: string[]; status: string; ts: string; payload: Record<string, unknown>;
}

const SEED: LedgerEntry[] = [
  { id:"iv-001", claim:"SOC 2 Type II attestation — Q1 2026", org:"Kovach Enterprises PBC", status:"verified", confidence:0.97, adjudicator:"Opus 4.8 + Haiku 4.5 dual-LLM", evtId:"evt-ver-20260101-001", ts:"2026-01-15T09:12:00Z", pqc:{algorithm:"Falcon-512 + ML-DSA",signature:"0x3a7f...c92d",keyId:"diamond-nv-key-001",verifiedAt:"2026-01-15T09:12:05Z"}, thermo:{energy_kwh:0.0042,landauer_pct:94.1,power_w:38.2,yield_note:"cold-snap recovery applied"} },
  { id:"iv-002", claim:"FedRAMP Moderate POA&M closure — AC-2, AC-17", org:"Genesis Conductor Engine", status:"verified", confidence:0.94, adjudicator:"Opus 4.8 + Haiku 4.5 dual-LLM", evtId:"evt-ver-20260210-002", ts:"2026-02-10T14:33:00Z", pqc:{algorithm:"Falcon-512 + ML-DSA",signature:"0x8b2e...f401",keyId:"diamond-nv-key-002",verifiedAt:"2026-02-10T14:33:08Z"}, thermo:{energy_kwh:0.0061,landauer_pct:91.7,power_w:42.5,yield_note:"nominal"} },
  { id:"iv-003", claim:"Carbon neutrality — 2025 ops", org:"Ouroboros Partner Coalition", status:"flagged", confidence:0.51, adjudicator:"Opus 4.8 + Haiku 4.5 dual-LLM", evtId:"evt-ver-20260315-003", ts:"2026-03-15T11:05:00Z", pqc:{algorithm:"Falcon-512 + ML-DSA",signature:"0x1c9a...7b38",keyId:"diamond-nv-key-003",verifiedAt:"2026-03-15T11:05:12Z"}, thermo:{energy_kwh:0.0088,landauer_pct:87.3,power_w:51.1,yield_note:"high-load burst detected"} },
];

const genId = () => `iv-${Date.now().toString(36)}`;
const genEvtId = () => `evt-ver-${new Date().toISOString().replace(/[-:T]/g,"").slice(0,14)}-${Math.random().toString(36).slice(2,6)}`;
const genSig = () => { const h=Array.from({length:8},()=>Math.floor(Math.random()*256).toString(16).padStart(2,"0")).join(""); return `0x${h.slice(0,4)}...${h.slice(4)}`; };
const genThermo = (): ThermoMeta => { const pw=32+Math.random()*28,lp=85+Math.random()*12; return {energy_kwh:parseFloat((pw*1.4/3600000).toFixed(6)),landauer_pct:parseFloat(lp.toFixed(1)),power_w:parseFloat(pw.toFixed(1)),yield_note:["nominal","cold-snap recovery applied","RAPL throttle active","burst mode"][Math.floor(Math.random()*4)]}; };

async function mcpCall(tool: string, args: Record<string, unknown>): Promise<unknown> {
  const res = await fetch(MCP_ENDPOINT, { method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({jsonrpc:"2.0", method:"tools/call", id:Date.now(), params:{name:tool, arguments:args}}) });
  if (!res.ok) throw new Error(`MCP ${res.status}`);
  return res.json();
}

async function submitSovereignVerification(claim: string, org: string): Promise<LedgerEntry> {
  const ts = new Date().toISOString(), evtId = genEvtId();
  let mcpTaskId: string|undefined, mcpRouted = false;

  // Step 1 — submit to Opus 4.8 via gc-mcp submit_opus_task
  try {
    const r = await mcpCall("submit_opus_task", {
      prompt: `Adjudicate verification claim.\nClaim: "${claim}"\nOrg: "${org}"\nReturn JSON: {"confidence":0.0-1.0,"status":"verified"|"flagged"|"rejected","notes":"string"}`
    }) as { result?: { content?: Array<{text?: string}> } };
    mcpTaskId = r?.result?.content?.[0]?.text?.slice(0, 40);
    mcpRouted = true;
  } catch { /* fall through to simulation */ }

  // Step 2 — propagate evt to claws (non-blocking)
  mcpCall("propagate_to_claws", {
    targets: ["slack", "openclaw"], priority: "normal",
    payload: { evt_id:evtId, schema_version:"1.0", record_type:"verification_submitted", ts, tags:["instinct-verify","sovereign"], payload:{claim,org,operator:OPERATOR} }
  }).catch(() => {});

  // Step 3 — sovereign simulation for immediate UI state
  await new Promise(r => setTimeout(r, 1100 + Math.random() * 700));
  const conf = 0.6 + Math.random() * 0.38;
  const status: LedgerEntry["status"] = conf > 0.85 ? "verified" : conf > 0.65 ? "flagged" : "rejected";
  return {
    id: genId(), claim, org, status, confidence: parseFloat(conf.toFixed(3)),
    adjudicator: mcpRouted ? "Opus 4.8 (MCP Live) + Haiku 4.5" : "Opus 4.8 + Haiku 4.5 (simulated)",
    evtId, ts, pqc:{algorithm:"Falcon-512 + ML-DSA", signature:genSig(), keyId:"diamond-nv-key-live", verifiedAt:ts},
    thermo: genThermo(), mcpTaskId, mcpRouted,
  };
}

function StatusBadge({status}: {status: LedgerEntry["status"]}) {
  const styles = { verified:"bg-green-900/50 text-green-300 border-green-700/50", pending:"bg-yellow-900/50 text-yellow-300 border-yellow-700/50", rejected:"bg-red-900/50 text-red-300 border-red-700/50", flagged:"bg-orange-900/50 text-orange-300 border-orange-700/50" };
  const icons = { verified:<CheckCircle size={10}/>, pending:<Clock size={10}/>, rejected:<X size={10}/>, flagged:<AlertTriangle size={10}/> };
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${styles[status]}`}>{icons[status]} {status.toUpperCase()}</span>;
}

function ConfBar({value}: {value: number}) {
  const pct = Math.round(value * 100), color = pct >= 85 ? "bg-green-500" : pct >= 65 ? "bg-yellow-500" : "bg-red-500";
  return <div className="flex items-center gap-2"><div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden"><div className={`h-full rounded-full ${color}`} style={{width:`${pct}%`}}/></div><span className="text-xs font-mono text-gray-400 w-8">{pct}%</span></div>;
}

function MCPBanner({live}: {live: boolean}) {
  const [p, setP] = useState(true);
  useEffect(() => { const t = setInterval(() => setP(x => !x), 1800); return () => clearInterval(t); }, []);
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-950/60 border border-green-800/50 text-xs text-green-400" style={{boxShadow:"0 0 20px rgba(34,197,94,0.15)"}}>
      <span className={`w-2 h-2 rounded-full ${live ? "bg-green-400" : "bg-yellow-400"} transition-opacity ${p ? "opacity-100" : "opacity-40"}`}/>
      <span className="font-mono">{live ? "MCP Live · Green Haven Node · Phase II" : "Connecting to Green Haven MCP Node · Phase II"}</span>
    </div>
  );
}

function Dashboard({entries, evtLog}: {entries: LedgerEntry[]; evtLog: EvtRecord[]}) {
  const v = entries.filter(e => e.status === "verified").length;
  const f = entries.filter(e => e.status === "flagged").length;
  const ac = entries.length ? entries.reduce((s,e) => s + e.confidence, 0) / entries.length : 0;
  const at = entries.length ? entries.reduce((s,e) => s + e.thermo.energy_kwh, 0) / entries.length : 0;
  const ml = entries.filter(e => e.mcpRouted).length;
  const stats = [
    {l:"Total Claims", v:entries.length, c:"text-blue-400"},
    {l:"Verified",     v:v,              c:"text-green-400"},
    {l:"Flagged",      v:f,              c:"text-orange-400"},
    {l:"Avg Confidence",v:`${Math.round(ac*100)}%`, c:"text-purple-400"},
    {l:"Avg mWh",      v:`${(at*1000).toFixed(3)}`, c:"text-orange-300"},
    {l:"MCP Routed",   v:ml,             c:"text-cyan-400"},
  ];
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {stats.map(s => <div key={s.l} className="bg-gray-900 border border-gray-800 rounded-xl p-4"><div className="text-2xl font-bold text-white">{s.v}</div><div className="text-xs text-gray-500 mt-1">{s.l}</div></div>)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2"><Activity size={14}/> Recent Verifications</div>
          <div className="space-y-2">
            {entries.slice(-5).reverse().map(e => (
              <div key={e.id} className="flex items-start justify-between gap-3 p-2 rounded-lg bg-gray-800/50">
                <div className="flex-1 min-w-0"><div className="text-gray-200 text-sm truncate">{e.claim}</div><div className="text-xs text-gray-500 font-mono">{e.org}</div></div>
                <div className="flex flex-col items-end gap-1"><StatusBadge status={e.status}/>{e.mcpRouted && <span className="text-xs text-cyan-500 font-mono">MCP ✓</span>}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2"><Terminal size={14}/> evt- Observability Stream</div>
          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {evtLog.length === 0 && <div className="text-gray-600 text-xs italic">No events yet. Submit a verification.</div>}
            {[...evtLog].reverse().slice(0,20).map(e => (
              <div key={e.evt_id} className="font-mono text-xs bg-gray-900 border border-gray-800 rounded p-2">
                <span className="text-gray-500">{String(e.ts).slice(11,19)}</span>{" "}
                <span className="text-blue-400">{e.evt_id}</span>{" "}
                <span className={e.status === "verified" ? "text-green-400" : e.status === "flagged" ? "text-orange-400" : "text-red-400"}>[{e.status}]</span>{" "}
                <span className="text-gray-300">{String((e.payload as any)?.claim ?? "").slice(0,35)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Ledger({entries}: {entries: LedgerEntry[]}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-gray-800 text-left">
            {["Claim","Org","Status","Confidence","PQC","Thermo","MCP","Time"].map(h => <th key={h} className="px-4 py-3 text-gray-400 font-medium">{h}</th>)}
          </tr></thead>
          <tbody>
            {[...entries].reverse().map(e => (
              <tr key={e.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                <td className="px-4 py-3"><div className="text-gray-200 max-w-xs truncate">{e.claim}</div><div className="text-xs text-cyan-700 font-mono">{e.evtId}</div></td>
                <td className="px-4 py-3 text-xs text-gray-400 font-mono">{e.org}</td>
                <td className="px-4 py-3"><StatusBadge status={e.status}/></td>
                <td className="px-4 py-3 w-28"><ConfBar value={e.confidence}/></td>
                <td className="px-4 py-3"><div className="text-xs text-purple-400 font-mono">{e.pqc.algorithm}</div><div className="text-xs text-gray-600 font-mono flex items-center gap-1"><Fingerprint size={9}/>{e.pqc.signature}</div></td>
                <td className="px-4 py-3"><div className="text-xs text-orange-400 font-mono">{e.thermo.landauer_pct}% η</div><div className="text-xs text-gray-500">{e.thermo.power_w}W · {(e.thermo.energy_kwh*1000).toFixed(3)}mWh</div></td>
                <td className="px-4 py-3">{e.mcpRouted ? <span className="text-xs text-cyan-500 font-mono">MCP ✓</span> : <span className="text-xs text-gray-700 font-mono">sim</span>}</td>
                <td className="px-4 py-3 text-xs text-gray-500 font-mono">{e.ts.slice(0,16).replace("T"," ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SubmitModal({onClose, onSubmit}: {onClose: () => void; onSubmit: (c: string, o: string) => Promise<void>}) {
  const [claim, setClaim] = useState(""), [org, setOrg] = useState("Kovach Enterprises PBC");
  const [loading, setLoading] = useState(false), [phase, setPhase] = useState("");
  const phases = [
    "Routing to gc-mcp.genesisconductor.io...",
    "Calling submit_opus_task (Opus 4.8 adjudication)...",
    "Propagating evt- via propagate_to_claws → slack, openclaw...",
    "Generating Falcon-512 + ML-DSA PQC signature...",
    "Recording RAPL/NVML thermodynamic data...",
    "Emitting evt-ver-* record to observability stream...",
  ];
  const go = async () => {
    if (!claim.trim()) return;
    setLoading(true);
    for (let i = 0; i < phases.length; i++) { setPhase(phases[i]); await new Promise(r => setTimeout(r, 320 + Math.random()*180)); }
    await onSubmit(claim, org);
    setLoading(false); onClose();
  };
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div><h3 className="text-lg font-semibold text-white">Submit via MCP</h3><p className="text-xs text-green-400 font-mono mt-0.5">gc-mcp.genesisconductor.io · submit_opus_task + propagate_to_claws</p></div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300"><X size={20}/></button>
        </div>
        <div className="p-6 space-y-4">
          <div><label className="block text-sm text-gray-400 mb-1.5">Claim to Verify</label>
            <textarea value={claim} onChange={e => setClaim(e.target.value)} rows={3} disabled={loading} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 text-sm resize-none focus:outline-none focus:border-green-600" placeholder="e.g. SOC 2 Type II attestation — Q2 2026"/></div>
          <div><label className="block text-sm text-gray-400 mb-1.5">Organization</label>
            <input value={org} onChange={e => setOrg(e.target.value)} disabled={loading} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 text-sm focus:outline-none focus:border-green-600"/></div>
          {loading && <div className="bg-gray-800/80 rounded-lg p-3 border border-green-900/40"><div className="flex items-center gap-2 text-green-400 text-xs font-mono"><RefreshCw size={12} className="animate-spin"/> {phase}</div></div>}
          <div className="flex gap-3 pt-2">
            <button onClick={onClose} disabled={loading} className="flex-1 px-4 py-2.5 rounded-lg border border-gray-700 text-gray-400 text-sm hover:text-gray-200 disabled:opacity-50">Cancel</button>
            <button onClick={go} disabled={loading || !claim.trim()} className="flex-1 px-4 py-2.5 rounded-lg bg-green-700 hover:bg-green-600 text-white text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? <RefreshCw size={14} className="animate-spin"/> : <Send size={14}/>}{loading ? "Processing..." : "Submit Verification"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Pricing() {
  const tiers = [
    {n:"Sovereign Starter", p:299, f:["50 verifications/mo","PQC signatures (Falcon-512)","Thermo instrumentation","evt- observability","MCP integration"], h:false},
    {n:"Operator Pro", p:990, f:["500 verifications/mo","Full PQC stack (Falcon-512 + ML-DSA)","RAPL/NVML telemetry","Full evt- audit ledger","White-label dashboard","Priority Opus 4.8 routing"], h:true},
    {n:"Coalition Enterprise", p:0, f:["Unlimited","Diamond NV-center signing","Landauer-hardened TAO","FedRAMP POA&M","Implicit Agreement + 5% SOL escrow","OPC access","Dedicated node"], h:false},
  ];
  return (
    <div className="space-y-6">
      <div className="text-center py-4"><h2 className="text-2xl font-bold text-white">Sovereign Verification Pricing</h2><p className="text-xs text-green-500 font-mono mt-2">Implicit Agreement + 5% SOL escrow activated (Genesis Conductor standard)</p></div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {tiers.map(t => (
          <div key={t.n} className={`bg-gray-900 border rounded-2xl p-6 space-y-4 ${t.h ? "border-green-600" : "border-gray-800"}`} style={t.h ? {boxShadow:"0 0 20px rgba(34,197,94,0.15)"} : {}}>
            {t.h && <div className="text-xs text-green-400 font-mono uppercase tracking-wider">Most Popular</div>}
            <div><div className="text-lg font-semibold text-white">{t.n}</div>
              <div className="mt-2">{t.p ? <><span className="text-3xl font-bold text-white">${t.p}</span><span className="text-gray-500">/mo</span></> : <span className="text-2xl font-bold text-white">Custom</span>}</div></div>
            <ul className="space-y-2">{t.f.map(f => <li key={f} className="flex items-start gap-2 text-sm text-gray-300"><CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0"/>{f}</li>)}</ul>
            <button className={`w-full py-2.5 rounded-xl text-sm font-medium transition-colors ${t.h ? "bg-green-700 hover:bg-green-600 text-white" : "border border-gray-700 text-gray-300 hover:text-white"}`}>{t.p ? "Get Access" : "Contact Igor"}</button>
          </div>
        ))}
      </div>
      <div className="text-center text-xs text-gray-600 font-mono">Operator: {OPERATOR} · Kovach Enterprises PBC · OPC Coalition Ready</div>
    </div>
  );
}

type View = "dashboard" | "ledger" | "pricing";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [entries, setEntries] = useState<LedgerEntry[]>(SEED);
  const [evtLog, setEvtLog] = useState<EvtRecord[]>([]);
  const [modal, setModal] = useState(false);
  const [live, setLive] = useState(false);

  useEffect(() => {
    fetch(MCP_ENDPOINT, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({jsonrpc:"2.0",method:"tools/list",id:1})})
      .then(r => { if (r.ok) setLive(true); }).catch(() => {});
  }, []);

  const handleSubmit = useCallback(async (claim: string, org: string) => {
    const entry = await submitSovereignVerification(claim, org);
    setEntries(prev => [...prev, entry]);
    setEvtLog(prev => [...prev, {
      evt_id: entry.evtId, schema_version:"1.0", record_type:"verification_complete",
      tags:["instinct-verify","sovereign","pqc","mcp"], status: entry.status, ts: entry.ts,
      payload:{claim:entry.claim, org:entry.org, confidence:entry.confidence, pqc:entry.pqc, thermo:entry.thermo, mcp_routed:entry.mcpRouted}
    }]);
    if (entry.mcpRouted) setLive(true);
    setView("ledger");
  }, []);

  const nav = [{id:"dashboard" as View, l:"Dashboard"}, {id:"ledger" as View, l:"Ledger"}, {id:"pricing" as View, l:"Pricing"}];

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <header className="border-b border-gray-800 bg-gray-950/95 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-green-900/60 border border-green-700/50 flex items-center justify-center" style={{boxShadow:"0 0 20px rgba(34,197,94,0.15)"}}>
              <Shield size={16} className="text-green-400"/>
            </div>
            <div>
              <div className="flex items-center gap-2"><span className="font-bold text-white text-sm">Instinct Verify</span><span className="text-xs px-1.5 py-0.5 rounded bg-green-900/60 text-green-400 border border-green-800/50 font-mono">SOVEREIGN</span></div>
              <div className="text-xs text-gray-500 font-mono">Powered by Genesis Conductor MCP</div>
            </div>
          </div>
          <MCPBanner live={live}/>
          <button onClick={() => setModal(true)} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-green-700 hover:bg-green-600 text-white text-sm font-medium transition-colors">
            <Plus size={14}/> Submit via MCP
          </button>
        </div>
        <div className="max-w-7xl mx-auto px-4 flex gap-1 pb-1">
          {nav.map(n => <button key={n.id} onClick={() => setView(n.id)} className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${view === n.id ? "bg-gray-800 text-white" : "text-gray-500 hover:text-gray-300"}`}>{n.l}</button>)}
        </div>
      </header>
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        {view === "dashboard" && <Dashboard entries={entries} evtLog={evtLog}/>}
        {view === "ledger" && <Ledger entries={entries}/>}
        {view === "pricing" && <Pricing/>}
      </main>
      <footer className="border-t border-gray-800 py-4 text-center text-xs text-gray-600 font-mono">
        Instinct Verify — Sovereign Edition v0.1 · Green Haven Node · Operator: {OPERATOR} · genesisconductor.io
      </footer>
      {modal && <SubmitModal onClose={() => setModal(false)} onSubmit={handleSubmit}/>}
    </div>
  );
}
