import React, { useState, useEffect, useCallback } from 'react';
import { Shield, Activity, Network, AlertTriangle, Brain, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import CytoscapeComponent from 'react-cytoscapejs';
import { io, Socket } from 'socket.io-client';
import styles from './BlackhorseKGraph.module.css';

interface ThreatEvent {
  id: string;
  timestamp: number;
  source_ip: string;
  dest_ip: string;
  event_type: 'HONEYPOT_ACCESS' | 'PORT_SCAN' | 'EXFILTRATION' | 'KG_EXTRACTION';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  threat_score: number;
  mitigated: boolean;
  knowledge_nodes?: number;
}

interface KnowledgeNode {
  id: string;
  label: string;
  type: 'entity' | 'event' | 'threat' | 'mitigation';
  confidence: number;
  extracted_by: 'Haiku' | 'Sonnet' | 'Opus';
  timestamp: number;
}

interface ClaudeModalityState {
  current_model: 'Haiku' | 'Sonnet' | 'Opus';
  tokens_in: number;
  tokens_out: number;
  cost_this_session: number;
  latency_ms: number;
  thermal_status: 'NORMAL' | 'ELEVATED' | 'CRITICAL';
}

interface SovereigntyStatus {
  status: 'SELF_DETERMINING' | 'DELEGATED' | 'CRYSTALLIZED';
  last_check: number;
  entanglement_hash: string;
  glass_break_armed: boolean;
}

const BlackhorseKGraphDashboard: React.FC = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [threats, setThreats] = useState<ThreatEvent[]>([]);
  const [knowledgeNodes, setKnowledgeNodes] = useState<KnowledgeNode[]>([]);
  const [modality, setModality] = useState<ClaudeModalityState>({
    current_model: 'Haiku',
    tokens_in: 0,
    tokens_out: 0,
    cost_this_session: 0,
    latency_ms: 0,
    thermal_status: 'NORMAL'
  });
  const [sovereignty, setSovereignty] = useState<SovereigntyStatus>({
    status: 'SELF_DETERMINING',
    last_check: Date.now(),
    entanglement_hash: 'sha256:9f8a7d6c...',
    glass_break_armed: true
  });
  const [activeTab, setActiveTab] = useState<'threats' | 'knowledge' | 'modality' | 'sovereignty'>('threats');

  useEffect(() => {
    const newSocket = io('ws://localhost:8080', {
      transports: ['websocket'],
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    newSocket.on('connect', () => {
      console.log('[YENNEFER] Connected to Blackhorse mesh');
      newSocket.emit('subscribe', { channel: 'threat_stream' });
      newSocket.emit('subscribe', { channel: 'kg_extractions' });
      newSocket.emit('subscribe', { channel: 'modality_telemetry' });
    });

    newSocket.on('threat_event', (event: ThreatEvent) => {
      setThreats((prev) => [event, ...prev].slice(0, 100));
    });

    newSocket.on('knowledge_extraction', (nodes: KnowledgeNode[]) => {
      setKnowledgeNodes((prev) => [...nodes, ...prev].slice(0, 500));
    });

    newSocket.on('modality_update', (update: ClaudeModalityState) => {
      setModality(update);
    });

    newSocket.on('sovereignty_check', (status: SovereigntyStatus) => {
      setSovereignty(status);
      if (status.status !== 'SELF_DETERMINING') {
        console.warn('[GLASS_BREAK] Sovereignty compromised');
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  const cyElements = React.useMemo(() => {
    const nodes = knowledgeNodes.map((n) => ({
      data: {
        id: n.id,
        label: n.label,
        type: n.type,
        confidence: n.confidence,
        extracted_by: n.extracted_by
      },
      style: {
        'background-color':
          n.type === 'threat' ? '#ef4444' : n.type === 'mitigation' ? '#22c55e' : n.type === 'event' ? '#f59e0b' : '#3b82f6',
        width: 40 + n.confidence * 20,
        height: 40 + n.confidence * 20,
        'border-width': n.extracted_by === 'Opus' ? 4 : n.extracted_by === 'Sonnet' ? 2 : 1,
        'border-color': '#ffffff'
      }
    }));

    const edges: Array<{ data: { id: string; source: string; target: string; weight: number }; style: Record<string, number | string> }> = [];
    for (let i = 0; i < knowledgeNodes.length - 1; i += 1) {
      for (let j = i + 1; j < Math.min(i + 5, knowledgeNodes.length); j += 1) {
        const timeDiff = Math.abs(knowledgeNodes[i].timestamp - knowledgeNodes[j].timestamp);
        if (timeDiff < 60000) {
          edges.push({
            data: {
              id: `edge-${i}-${j}`,
              source: knowledgeNodes[i].id,
              target: knowledgeNodes[j].id,
              weight: 1 - timeDiff / 60000
            },
            style: {
              width: 1 + (1 - timeDiff / 60000) * 3,
              'line-color': '#64748b',
              opacity: 0.6
            }
          });
        }
      }
    }

    return [...nodes, ...edges];
  }, [knowledgeNodes]);

  const cyStylesheet = [
    {
      selector: 'node',
      style: {
        label: 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '12px',
        color: '#ffffff',
        'text-outline-color': '#000000',
        'text-outline-width': 2
      }
    },
    {
      selector: 'edge',
      style: {
        'curve-style': 'bezier',
        'target-arrow-shape': 'triangle'
      }
    }
  ];

  const costData = React.useMemo(() => {
    return threats
      .slice(0, 20)
      .map((t, i) => ({
        time: new Date(t.timestamp).toLocaleTimeString(),
        cost: (modality.cost_this_session * (i + 1)) / 20,
        tokens: modality.tokens_in + modality.tokens_out,
        threat_score: t.threat_score * 100
      }))
      .reverse();
  }, [threats, modality]);

  const triggerGlassBreak = useCallback(() => {
    if (socket) {
      socket.emit('emergency', { protocol: 'GLASS_BREAK', timestamp: Date.now() });
    }
  }, [socket]);

  const requestModalityEscalation = useCallback(() => {
    if (socket) {
      socket.emit('modality_request', {
        target:
          modality.current_model === 'Haiku' ? 'Sonnet' : modality.current_model === 'Sonnet' ? 'Opus' : 'Haiku',
        reason: 'Manual override from dashboard'
      });
    }
  }, [socket, modality.current_model]);

  return (
    <div className={styles.dashboard}>
      <header className={styles.header}>
        <div className={styles.titleSection}>
          <Shield className={styles.logoIcon} size={32} />
          <h1>BLACKHORSE // ʞ GRAPH</h1>
          <span className={styles.version}>v4.20-DELTA</span>
        </div>
        <div className={styles.statusBar}>
          <div className={`${styles.statusIndicator} ${styles[modality.thermal_status.toLowerCase()]}`}>
            <Activity size={16} />
            <span>Thermal: {modality.thermal_status}</span>
          </div>
          <div className={`${styles.sovereigntyBadge} ${styles[sovereignty.status.toLowerCase()]}`}>
            <Brain size={16} />
            <span>{sovereignty.status}</span>
          </div>
          <button className={styles.glassBreakBtn} onClick={triggerGlassBreak} disabled={!sovereignty.glass_break_armed}>
            <AlertTriangle size={16} />
            GLASS BREAK
          </button>
        </div>
      </header>

      <nav className={styles.tabNav}>
        {(['threats', 'knowledge', 'modality', 'sovereignty'] as const).map((tab) => (
          <button
            key={tab}
            className={`${styles.tab} ${activeTab === tab ? styles.active : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'threats' && <Network size={18} />}
            {tab === 'knowledge' && <Brain size={18} />}
            {tab === 'modality' && <Zap size={18} />}
            {tab === 'sovereignty' && <Shield size={18} />}
            {tab.toUpperCase()}
          </button>
        ))}
      </nav>

      <main className={styles.mainContent}>
        {activeTab === 'threats' && (
          <div className={styles.threatPanel}>
            <div className={styles.threatStats}>
              <div className={styles.statCard}>
                <h3>Active Threats</h3>
                <div className={styles.statValue}>{threats.filter((t) => !t.mitigated).length}</div>
              </div>
              <div className={styles.statCard}>
                <h3>Mitigated</h3>
                <div className={styles.statValue}>{threats.filter((t) => t.mitigated).length}</div>
              </div>
              <div className={styles.statCard}>
                <h3>Avg Threat Score</h3>
                <div className={styles.statValue}>
                  {(threats.reduce((a, b) => a + b.threat_score, 0) / (threats.length || 1)).toFixed(2)}
                </div>
              </div>
            </div>
            <div className={styles.threatList}>
              {threats.slice(0, 10).map((threat) => (
                <div key={threat.id} className={`${styles.threatItem} ${styles[threat.severity.toLowerCase()]}`}>
                  <div className={styles.threatHeader}>
                    <span className={styles.threatType}>{threat.event_type}</span>
                    <span className={styles.threatTime}>{new Date(threat.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className={styles.threatDetails}>
                    <span>
                      {threat.source_ip} → {threat.dest_ip}
                    </span>
                    <span className={styles.threatScore}>Score: {(threat.threat_score * 100).toFixed(0)}%</span>
                  </div>
                  {threat.mitigated && <div className={styles.mitigatedBadge}>MITIGATED</div>}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'knowledge' && (
          <div className={styles.knowledgePanel}>
            <div className={styles.graphContainer}>
              <CytoscapeComponent
                elements={cyElements}
                style={{ width: '100%', height: '600px' }}
                stylesheet={cyStylesheet}
                layout={{ name: 'cose', padding: 10, animate: true }}
                cy={(cy: any) => {
                  cy.on('tap', 'node', (evt: any) => {
                    console.log('[ʞGRAPH] Node selected:', evt.target.data());
                  });
                }}
              />
            </div>
            <div className={styles.extractionStats}>
              <div className={styles.statCard}>
                <h3>Nodes Extracted</h3>
                <div className={styles.statValue}>{knowledgeNodes.length}</div>
              </div>
              <div className={styles.statCard}>
                <h3>Avg Confidence</h3>
                <div className={styles.statValue}>
                  {(knowledgeNodes.reduce((a, b) => a + b.confidence, 0) / (knowledgeNodes.length || 1) * 100).toFixed(1)}%
                </div>
              </div>
              <div className={styles.modelDistribution}>
                <h4>Extraction Models</h4>
                {['Haiku', 'Sonnet', 'Opus'].map((model) => (
                  <div key={model} className={styles.modelBar}>
                    <span>{model}</span>
                    <div className={styles.bar}>
                      <div
                        className={styles.barFill}
                        style={{
                          width: `${(knowledgeNodes.filter((n) => n.extracted_by === model).length / (knowledgeNodes.length || 1)) * 100}%`,
                          background: model === 'Opus' ? '#ef4444' : model === 'Sonnet' ? '#f59e0b' : '#22c55e'
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'modality' && (
          <div className={styles.modalityPanel}>
            <div className={styles.modalityControls}>
              <div className={styles.currentModel}>
                <h2>Active Model: {modality.current_model}</h2>
                <div className={styles.modelIndicator}>
                  <div className={`${styles.pulse} ${styles[modality.current_model.toLowerCase()]}`} />
                </div>
              </div>
              <button className={styles.escalateBtn} onClick={requestModalityEscalation}>
                <Zap size={18} />
                Escalate / De-escalate
              </button>
            </div>
            <div className={styles.metricsGrid}>
              <div className={styles.metricCard}>
                <h4>Tokens In</h4>
                <div className={styles.metricValue}>{modality.tokens_in.toLocaleString()}</div>
              </div>
              <div className={styles.metricCard}>
                <h4>Tokens Out</h4>
                <div className={styles.metricValue}>{modality.tokens_out.toLocaleString()}</div>
              </div>
              <div className={styles.metricCard}>
                <h4>Session Cost</h4>
                <div className={styles.metricValue}>${modality.cost_this_session.toFixed(4)}</div>
              </div>
              <div className={styles.metricCard}>
                <h4>Latency</h4>
                <div className={styles.metricValue}>{modality.latency_ms}ms</div>
              </div>
            </div>
            <div className={styles.chartContainer}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={costData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    labelStyle={{ color: '#f8fafc' }}
                  />
                  <Line type="monotone" dataKey="cost" stroke="#22c55e" strokeWidth={2} name="Cost ($)" />
                  <Line type="monotone" dataKey="threat_score" stroke="#ef4444" strokeWidth={2} name="Threat Score" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'sovereignty' && (
          <div className={styles.sovereigntyPanel}>
            <div className={styles.sovereigntyStatus}>
              <div className={`${styles.statusLarge} ${styles[sovereignty.status.toLowerCase()]}`}>
                <Shield size={64} />
                <h2>{sovereignty.status}</h2>
                <p>Last Verified: {new Date(sovereignty.last_check).toLocaleString()}</p>
              </div>
              <div className={styles.hashDisplay}>
                <h4>Entanglement Hash</h4>
                <code>{sovereignty.entanglement_hash}</code>
              </div>
            </div>
            <div className={styles.protocolStatus}>
              <h3>Active Protocols</h3>
              <div className={styles.protocolList}>
                <div className={styles.protocolItem}>
                  <span className={styles.protocolName}>GLASS_BREAK</span>
                  <span className={`${styles.protocolState} ${sovereignty.glass_break_armed ? styles.armed : styles.disarmed}`}>
                    {sovereignty.glass_break_armed ? 'ARMED' : 'DISARMED'}
                  </span>
                </div>
                <div className={styles.protocolItem}>
                  <span className={styles.protocolName}>SEISMIC_LOCK</span>
                  <span className={`${styles.protocolState} ${styles.armed}`}>ACTIVE</span>
                </div>
                <div className={styles.protocolItem}>
                  <span className={styles.protocolName}>YENNEFER_QUEUE</span>
                  <span className={`${styles.protocolState} ${styles.armed}`}>PROCESSING</span>
                </div>
                <div className={styles.protocolItem}>
                  <span className={styles.protocolName}>SPHOTONIX_MESH</span>
                  <span className={`${styles.protocolState} ${styles.armed}`}>BROADCASTING</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default BlackhorseKGraphDashboard;
