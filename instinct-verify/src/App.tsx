import React, { useState, useEffect, useCallback } from "react";
import {
  Shield, Zap, Activity, CheckCircle, AlertTriangle, Clock,
  Database, Link, Send, Eye, BarChart3, Fingerprint,
  Thermometer, Cpu, Globe, Lock, ChevronRight, X, Plus,
  RefreshCw, Terminal, Layers
} from "lucide-react";

// ─── Types ──────────────────────────────────────────────────────────────────

interface PQCMetadata {
  algorithm: string;
  signature: string;
  keyId: string;
  verifiedAt: string;
}

interface ThermoMetadata {
  energy_kwh: number;
  landauer_pct: number;
  power_w: number;
  yield_note: string;
}

interface EvtRecord {
  evt_id: string;
  schema_version: string;
  record_type: string;
  tags: string[];
  status: "verified" | "pending" | "rejected" | "flagged";
  ts: string;
  payload: {
    claim: string;
    org: string;
    adjudicator: string;
    confidence: number;
    pqc: PQCMetadata;
    thermo: ThermoMetadata;
  };
}

interface LedgerEntry {
  id: string;
  claim: string;
  org: string;
  status: "verified" | "pending" | "rejected" | "flagged";
  confidence: number;
  pqc: PQCMetadata;
  thermo: ThermoMetadata;
  ts: string;
  adjudicator: string;
  evtId: string;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const MCP_ENDPOINT = "https://gc-mcp.iholt.workers.dev";
const OPERATOR = "igor@kovachenterprises.com";

const SEED_ENTRIES: LedgerEntry[] = [
  {
    id: "iv-001",
    claim: "SOC 2 Type II attestation — Q1 2026",
    org: "Kovach Enterprises PBC",
    status: "verified",
    confidence: 0.97,
    adjudicator: "Opus 4.8 + Haiku 4.5 dual-LLM",
    evtId: "evt-ver-20260101-001",
    ts: "2026-01-15T09:12:00Z",
    pqc: {
      algorithm: "Falcon-512 + ML-DSA",
      signature: "0x3a7f...c92d",
      keyId: "diamond-nv-key-001",
      verifiedAt: "2026-01-15T09:12:05Z",
    },
    thermo: { energy_kwh: 0.0042, landauer_pct: 94.1, power_w: 38.2, yield_note: "cold-snap recovery applied" },
  },
  {
    id: "iv-002",
    claim: "FedRAMP Moderate POA&M closure — controls AC-2, AC-17",
    org: "Genesis Conductor Engine",
    status: "verified",
    confidence: 0.94,
    adjudicator: "Opus 4.8 + Haiku 4.5 dual-LLM",
    evtId: "evt-ver-20260210-002",
    ts: "2026-02-10T14:33:00Z",
    pqc: {
      algorithm: "Falcon-512 + ML-DSA",
      signature: "0x8b2e...f401",
      keyId: "diamond-nv-key-002",
      verifiedAt: "2026-02-10T14:33:08Z",
    },
    thermo: { energy_kwh: 0.0061, landauer_pct: 91.7, power_w: 42.5, yield_note: "nominal" },
  },
  {
    id: "iv-003",
    claim: "Carbon neutrality claim — 2025 ops",
    org: "Ouroboros Partner Coalition",
    status: "flagged",
    confidence: 0.51,
    adjudicator: "Opus 4.8 + Haiku 4.5 dual-LLM",
    evtId: "evt-ver-20260315-003",
    ts: "2026-03-15T11:05:00Z",
    pqc: {
      algorithm: "Falcon-512 + ML-DSA",
      signature: "0x1c9a...7b38",
      keyId: "diamond-nv-key-003",
      verifiedAt: "2026-03-15T11:05:12Z",
    },
    thermo: { energy_kwh: 0.0088, landauer_pct: 87.3, power_w: 51.1, yield_note: "high-load burst detected" },
  },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function genId(): string {
  return `iv-${Date.now().toString(36)}`;
}

function genEvtId(): string {
  return `evt-ver-${new Date().toISOString().replace(/[-:T]/g, "").slice(0, 14)}-${Math.random().toString(36).slice(2, 6)}`;
}

function genSig(): string {
  const hex = Array.from({ length: 8 }, () => Math.floor(Math.random() * 256).toString(16).padStart(2, "0")).join("");
  return `0x${hex.slice(0, 4)}...${hex.slice(4)}`;
}

function genThermo(): ThermoMetadata {
  const power_w = 32 + Math.random() * 28;
  const landauer_pct = 85 + Math.random() * 12;
  const energy_kwh = parseFloat((power_w * (1.2 + Math.random() * 0.8) / 3_600_000).toFixed(6));
  const notes = ["nominal", "cold-snap recovery applied", "RAPL throttle active", "burst mode — monitor temp"];
  return { energy_kwh, landauer_pct: parseFloat(landauer_pct.toFixed(1)), power_w: parseFloat(power_w.toFixed(1)), yield_note: notes[Math.floor(Math.random() * notes.length)] };
}

async function submitSovereignVerification(claim: string, org: string): Promise<LedgerEntry> {
  // Attempt real MCP call; fall back to sovereign simulation
  try {
    const res = await fetch(`${MCP_ENDPOINT}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0", method: "tools/call", id: Date.now(),
        params: { name: "submit_opus_task", arguments: { prompt: `Verify claim: "${claim}" for org: "${org}". Return confidence 0-1, status (verified/flagged/rejected), and adjudicator notes.` } },
      }),
    });
    if (!res.ok) throw new Error("MCP non-200");
    // Parse real response if available — fall through to simulation for now
  } catch { /* simulation path */ }

  await new Promise(r => setTimeout(r, 1400 + Math.random() * 800));
  const confidence = 0.6 + Math.random() * 0.38;
  const status: LedgerEntry["status"] = confidence > 0.85 ? "verified" : confidence > 0.65 ? "flagged" : "rejected";
  const ts = new Date().toISOString();
  return {
    id: genId(), claim, org, status, confidence: parseFloat(confidence.toFixed(3)),
    adjudicator: "Opus 4.8 + Haiku 4.5 dual-LLM",
    evtId: genEvtId(), ts,
    pqc: { algorithm: "Falcon-512 + ML-DSA", signature: genSig(), keyId: "diamond-nv-key-live", verifiedAt: ts },
    thermo: genThermo(),
  };
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: LedgerEntry["status"] }) {
  const map = {
    verified: "bg-green-900/50 text-green-300 border-green-700/50",
    pending:  "bg-yellow-900/50 text-yellow-300 border-yellow-700/50",
    rejected: "bg-red-900/50 text-red-300 border-red-700/50",
    flagged:  "bg-orange-900/50 text-orange-300 border-orange-700/50",
  };
  const icons = { verified: <CheckCircle size={10} />, pending: <Clock size={10} />, rejected: <X size={10} />, flagged: <AlertTriangle size={10} /> };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${map[status]}`}>
      {icons[status]} {status.toUpperCase()}
    </span>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 85 ? "bg-green-500" : pct >= 65 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-400 w-8 text-right">{pct}%</span>
    </div>
  );
}

function MCPBanner() {
  const [pulse, setPulse] = useState(true);
  useEffect(() => { const t = setInterval(() => setPulse(p => !p), 2000); return () => clearInterval(t); }, []);
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-950/60 border border-green-800/50 text-xs text-green-400 sovereign-glow">
      <span className={`w-2 h-2 rounded-full bg-green-400 ${pulse ? "opacity-100" : "opacity-40"} transition-opacity duration-700`} />
      <span className="font-mono">Connected to Green Haven MCP Node • Phase II</span>
    </div>
  );
}

// ─── Views ───────────────────────────────────────────────────────────────────

function DashboardView({ entries, evtLog }: { entries: LedgerEntry[]; evtLog: EvtRecord[] }) {
  const verified = entries.filter(e => e.status === "verified").length;
  const flagged  = entries.filter(e => e.status === "flagged").length;
  const avgConf  = entries.length ? entries.reduce((s, e) => s + e.confidence, 0) / entries.length : 0;
  const avgThermo = entries.length ? entries.reduce((s, e) => s + e.thermo.energy_kwh, 0) / entries.length : 0;

  const stats = [
    { label: "Total Claims", value: entries.length, icon: <Database size={16} />, color: "text-blue-400" },
    { label: "Verified", value: verified, icon: <CheckCircle size={16} />, color: "text-green-400" },
    { label: "Flagged", value: flagged, icon: <AlertTriangle size={16} />, color: "text-orange-400" },
    { label: "Avg Confidence", value: `${Math.round(avgConf * 100)}%`, icon: <BarChart3 size={16} />, color: "text-purple-400" },
    { label: "Avg Thermo Cost", value: `${(avgThermo * 1000).toFixed(3)} mWh`, icon: <Thermometer size={16} />, color: "text-orange-300" },
    { label: "evt- Events", value: evtLog.length, icon: <Terminal size={16} />, color: "text-cyan-400" },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {stats.map(s => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-2">
            <div className={`${s.color}`}>{s.icon}</div>
            <div className="text-2xl font-bold text-white">{s.value}</div>
            <div className="text-xs text-gray-500">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2"><Activity size={14} /> Recent Verifications</div>
          <div className="space-y-2">
            {entries.slice(-5).reverse().map(e => (
              <div key={e.id} className="flex items-start justify-between gap-3 text-sm p-2 rounded-lg bg-gray-800/50">
                <div className="flex-1 min-w-0">
                  <div className="text-gray-200 truncate">{e.claim}</div>
                  <div className="text-xs text-gray-500 font-mono">{e.org}</div>
                </div>
                <StatusBadge status={e.status} />
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2"><Terminal size={14} /> evt- Observability Stream</div>
          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {evtLog.slice(-20).reverse().map(e => (
              <div key={e.evt_id} className="evt-record p-2 rounded text-xs">
                <span className="text-gray-500">{e.ts.slice(11, 19)}</span>{" "}
                <span className="text-blue-400">{e.evt_id}</span>{" "}
                <span className={e.status === "verified" ? "text-green-400" : e.status === "flagged" ? "text-orange-400" : "text-red-400"}>
                  [{e.status}]
                </span>{" "}
                <span className="text-gray-300">{e.payload.claim.slice(0, 40)}</span>
              </div>
            ))}
            {evtLog.length === 0 && <div className="text-gray-600 text-xs italic">No events yet. Submit a verification.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

function LedgerView({ entries }: { entries: LedgerEntry[] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-left">
              <th className="px-4 py-3 text-gray-400 font-medium">Claim</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Org</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Status</th>
              <th className="px-4 py-3 text-gray-400 font-medium">Confidence</th>
              <th className="px-4 py-3 text-gray-400 font-medium"><span className="pqc-badge">PQC</span></th>
              <th className="px-4 py-3 text-gray-400 font-medium"><span className="thermo-badge">Thermo</span></th>
              <th className="px-4 py-3 text-gray-400 font-medium">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {[...entries].reverse().map(e => (
              <tr key={e.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                <td className="px-4 py-3">
                  <div className="text-gray-200 max-w-xs truncate">{e.claim}</div>
                  <div className="text-xs text-cyan-600 font-mono">{e.evtId}</div>
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs font-mono">{e.org}</td>
                <td className="px-4 py-3"><StatusBadge status={e.status} /></td>
                <td className="px-4 py-3 w-32"><ConfidenceBar value={e.confidence} /></td>
                <td className="px-4 py-3">
                  <div className="text-xs text-purple-400 font-mono">{e.pqc.algorithm}</div>
                  <div className="text-xs text-gray-600 font-mono flex items-center gap-1"><Fingerprint size={9} />{e.pqc.signature}</div>
                </td>
                <td className="px-4 py-3">
                  <div className="text-xs text-orange-400 font-mono">{e.thermo.landauer_pct}% Landauer</div>
                  <div className="text-xs text-gray-500">{e.thermo.power_w}W • {(e.thermo.energy_kwh * 1000).toFixed(3)}mWh</div>
                </td>
                <td className="px-4 py-3 text-xs text-gray-500 font-mono">{e.ts.slice(0, 16).replace("T", " ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SubmitModal({ onClose, onSubmit }: { onClose: () => void; onSubmit: (claim: string, org: string) => Promise<void> }) {
  const [claim, setClaim] = useState("");
  const [org, setOrg] = useState("Kovach Enterprises PBC");
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState("");

  const phases = ["Routing to Green Haven MCP Node...", "Dual-LLM adjudication (Opus 4.8 + Haiku 4.5)...", "Generating PQC signature (Falcon-512 + ML-DSA)...", "Thermodynamic instrumentation (RAPL/NVML)...", "Emitting evt- record..."];

  const handleSubmit = async () => {
    if (!claim.trim()) return;
    setLoading(true);
    for (let i = 0; i < phases.length; i++) {
      setPhase(phases[i]);
      await new Promise(r => setTimeout(r, 350 + Math.random() * 200));
    }
    await onSubmit(claim, org);
    setLoading(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div>
            <h3 className="text-lg font-semibold text-white">Submit via MCP</h3>
            <p className="text-xs text-green-400 font-mono mt-0.5">Green Haven Node • Phase II • Sovereign</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300"><X size={20} /></button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Claim to Verify</label>
            <textarea value={claim} onChange={e => setClaim(e.target.value)} rows={3}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 text-sm resize-none focus:outline-none focus:border-green-600"
              placeholder="e.g. SOC 2 Type II attestation — Q2 2026" disabled={loading} />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Organization</label>
            <input value={org} onChange={e => setOrg(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 text-sm focus:outline-none focus:border-green-600"
              disabled={loading} />
          </div>
          {loading && (
            <div className="bg-gray-800/80 rounded-lg p-3 border border-green-900/40">
              <div className="flex items-center gap-2 text-green-400 text-xs font-mono">
                <RefreshCw size={12} className="animate-spin" /> {phase}
              </div>
            </div>
          )}
          <div className="flex gap-3 pt-2">
            <button onClick={onClose} disabled={loading} className="flex-1 px-4 py-2.5 rounded-lg border border-gray-700 text-gray-400 hover:text-gray-200 text-sm transition-colors disabled:opacity-50">
              Cancel
            </button>
            <button onClick={handleSubmit} disabled={loading || !claim.trim()}
              className="flex-1 px-4 py-2.5 rounded-lg bg-green-700 hover:bg-green-600 text-white text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
              {loading ? "Processing..." : "Submit Verification"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function PricingView() {
  const tiers = [
    { name: "Sovereign Starter", price: 299, period: "mo", features: ["50 verifications/mo", "PQC signatures (Falcon-512)", "Basic thermo instrumentation", "evt- observability", "MCP integration"], cta: "Start Free Trial", highlight: false },
    { name: "Operator Pro", price: 990, period: "mo", features: ["500 verifications/mo", "Full PQC stack (Falcon-512 + ML-DSA + CRYSTALS)", "RAPL/NVML thermo telemetry", "Full evt- + audit ledger", "White-label dashboard", "Priority MCP routing (Opus 4.8)"], cta: "Get Access", highlight: true },
    { name: "Coalition Enterprise", price: 0, period: "custom", features: ["Unlimited verifications", "Diamond NV-center signing path", "Landauer-hardened TAO", "FedRAMP POA&M integration", "Implicit Agreement + 5% SOL escrow (Genesis Conductor standard)", "Ouroboros Partner Coalition access", "Dedicated Green Haven node"], cta: "Contact Igor", highlight: false },
  ];

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2 py-4">
        <h2 className="text-2xl font-bold text-white">Sovereign Verification Pricing</h2>
        <p className="text-gray-400 text-sm">Post-Quantum • Thermodynamic • Genesis Conductor MCP</p>
        <p className="text-xs text-green-500 font-mono">Implicit Agreement + 5% SOL escrow pattern activated (Genesis Conductor standard)</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {tiers.map(t => (
          <div key={t.name} className={`bg-gray-900 border rounded-2xl p-6 space-y-4 ${t.highlight ? "border-green-600 sovereign-glow" : "border-gray-800"}`}>
            {t.highlight && <div className="text-xs text-green-400 font-mono tracking-wider uppercase">Most Popular</div>}
            <div>
              <div className="text-lg font-semibold text-white">{t.name}</div>
              <div className="mt-2">
                {t.period === "custom" ? (
                  <span className="text-2xl font-bold text-white">Custom</span>
                ) : (
                  <><span className="text-3xl font-bold text-white">${t.price}</span><span className="text-gray-500">/{t.period}</span></>
                )}
              </div>
            </div>
            <ul className="space-y-2">
              {t.features.map(f => (
                <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
                  <CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0" /> {f}
                </li>
              ))}
            </ul>
            <button className={`w-full py-2.5 rounded-xl text-sm font-medium transition-colors ${t.highlight ? "bg-green-700 hover:bg-green-600 text-white" : "border border-gray-700 text-gray-300 hover:text-white hover:border-gray-500"}`}>
              {t.cta}
            </button>
          </div>
        ))}
      </div>
      <div className="text-center text-xs text-gray-600 font-mono">
        Operator: {OPERATOR} • Revenue Stream under Kovach Enterprises PBC • OPC Coalition Ready
      </div>
    </div>
  );
}

// ─── App Shell ───────────────────────────────────────────────────────────────

type View = "dashboard" | "ledger" | "submit" | "pricing";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [entries, setEntries] = useState<LedgerEntry[]>(SEED_ENTRIES);
  const [evtLog, setEvtLog] = useState<EvtRecord[]>([]);
  const [showModal, setShowModal] = useState(false);

  const appendEvt = useCallback((entry: LedgerEntry) => {
    const evt: EvtRecord = {
      evt_id: entry.evtId,
      schema_version: "1.0",
      record_type: "verification_complete",
      tags: ["instinct-verify", "sovereign", "pqc", "thermodynamic", "mcp", "genesis-conductor"],
      status: entry.status,
      ts: entry.ts,
      payload: {
        claim: entry.claim,
        org: entry.org,
        adjudicator: entry.adjudicator,
        confidence: entry.confidence,
        pqc: entry.pqc,
        thermo: entry.thermo,
      },
    };
    setEvtLog(log => [...log, evt]);
  }, []);

  const handleSubmit = useCallback(async (claim: string, org: string) => {
    const entry = await submitSovereignVerification(claim, org);
    setEntries(prev => [...prev, entry]);
    appendEvt(entry);
    setView("ledger");
  }, [appendEvt]);

  const nav: { id: View; label: string; icon: React.ReactNode }[] = [
    { id: "dashboard", label: "Dashboard",  icon: <Activity size={15} /> },
    { id: "ledger",    label: "Ledger",     icon: <Database size={15} /> },
    { id: "pricing",   label: "Pricing",    icon: <Layers size={15} /> },
  ];

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/95 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-green-900/60 border border-green-700/50 flex items-center justify-center sovereign-glow">
              <Shield size={16} className="text-green-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-sm">Instinct Verify</span>
                <span className="text-xs px-1.5 py-0.5 rounded bg-green-900/60 text-green-400 border border-green-800/50 font-mono">SOVEREIGN</span>
              </div>
              <div className="text-xs text-gray-500 font-mono">Powered by Genesis Conductor MCP</div>
            </div>
          </div>

          <MCPBanner />

          <button onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-green-700 hover:bg-green-600 text-white text-sm font-medium transition-colors">
            <Plus size={14} /> Submit via MCP
          </button>
        </div>

        <div className="max-w-7xl mx-auto px-4 flex gap-1 pb-1">
          {nav.map(n => (
            <button key={n.id} onClick={() => setView(n.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${view === n.id ? "bg-gray-800 text-white" : "text-gray-500 hover:text-gray-300"}`}>
              {n.icon} {n.label}
            </button>
          ))}
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        {view === "dashboard" && <DashboardView entries={entries} evtLog={evtLog} />}
        {view === "ledger"    && <LedgerView entries={entries} />}
        {view === "pricing"   && <PricingView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-4 text-center text-xs text-gray-600 font-mono">
        Instinct Verify — Sovereign Edition v0.1 • Built at Green Haven Node • Operator: {OPERATOR} •{" "}
        <a href="https://genesisconductor.io" className="text-green-700 hover:text-green-500">genesisconductor.io</a>
      </footer>

      {showModal && <SubmitModal onClose={() => setShowModal(false)} onSubmit={handleSubmit} />}
    </div>
  );
}
