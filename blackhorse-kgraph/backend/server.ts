import express, { Request, Response, NextFunction } from 'express';
import { createServer } from 'http';
import { Server, Socket } from 'socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import { Redis } from 'ioredis';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import { Pool } from 'pg';
import Anthropic from '@anthropic-ai/sdk';
import { v4 as uuidv4 } from 'uuid';
import winston from 'winston';

dotenv.config();

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'blackhorse-kgraph' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

const pgPool = new Pool({
  host: process.env.PG_HOST || 'localhost',
  port: parseInt(process.env.PG_PORT || '5432'),
  database: process.env.PG_DATABASE || 'blackhorse_kgraph',
  user: process.env.PG_USER || 'postgres',
  password: process.env.PG_PASSWORD || 'postgres',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || '',
});

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
  raw_payload?: string;
}

interface KnowledgeNode {
  id: string;
  label: string;
  type: 'entity' | 'event' | 'threat' | 'mitigation';
  confidence: number;
  extracted_by: 'Haiku' | 'Sonnet' | 'Opus';
  timestamp: number;
  conversation_id: string;
  edges?: string[];
}

interface ClaudeModalityState {
  current_model: 'Haiku' | 'Sonnet' | 'Opus';
  tokens_in: number;
  tokens_out: number;
  cost_this_session: number;
  latency_ms: number;
  thermal_status: 'NORMAL' | 'ELEVATED' | 'CRITICAL';
  last_escalation: number;
}

interface SovereigntyStatus {
  status: 'SELF_DETERMINING' | 'DELEGATED' | 'CRYSTALLIZED';
  last_check: number;
  entanglement_hash: string;
  glass_break_armed: boolean;
  checkpoint_alpha: string;
}

class ModalityRouter {
  private state: ClaudeModalityState;
  private readonly COST_LIMITS = {
    Haiku: { input: 1.0, output: 5.0 },
    Sonnet: { input: 3.0, output: 15.0 },
    Opus: { input: 5.0, output: 25.0 }
  };

  constructor() {
    this.state = {
      current_model: 'Haiku',
      tokens_in: 0,
      tokens_out: 0,
      cost_this_session: 0,
      latency_ms: 0,
      thermal_status: 'NORMAL',
      last_escalation: Date.now()
    };
  }

  async classifyAndRoute(input: string, complexity_hint?: number): Promise<{
    model: 'Haiku' | 'Sonnet' | 'Opus';
    system_prompt: string;
    max_tokens: number;
    temperature: number;
  }> {
    const classificationStart = Date.now();

    try {
      const classification = await anthropic.messages.create({
        model: 'claude-3-haiku-20240307',
        max_tokens: 200,
        temperature: 0.3,
        system: `You are a task classifier for the Blackhorse-ʞGraph security system.
Analyze the input and classify:
1. Complexity (1-10): 1-4=Haiku, 5-7=Sonnet, 8-10=Opus
2. Domain: threat_analysis | knowledge_extraction | consensus_validation
3. Urgency: real_time | batch | archival
Respond in JSON: {"complexity": N, "domain": "...", "urgency": "...", "model": "Haiku|Sonnet|Opus"}`,
        messages: [{ role: 'user', content: input.slice(0, 1000) }]
      });

      const latency = Date.now() - classificationStart;
      this.updateMetrics('Haiku', 1000, 200, latency);

      let result: any = {};
      try {
        const content = classification.content[0];
        if (content.type === 'text') {
          result = JSON.parse(content.text);
        }
      } catch {
        result = { complexity: 5, domain: 'threat_analysis', urgency: 'real_time', model: 'Sonnet' };
      }

      if (complexity_hint) {
        result.complexity = complexity_hint;
      }

      if (result.complexity <= 4) {
        return {
          model: 'Haiku',
          system_prompt: this.getSystemPrompt('Haiku', result.domain),
          max_tokens: 1024,
          temperature: 0.3
        };
      }
      if (result.complexity <= 7) {
        return {
          model: 'Sonnet',
          system_prompt: this.getSystemPrompt('Sonnet', result.domain),
          max_tokens: 2048,
          temperature: 0.1
        };
      }
      return {
        model: 'Opus',
        system_prompt: this.getSystemPrompt('Opus', result.domain),
        max_tokens: 4096,
        temperature: 0.0
      };
    } catch (error) {
      logger.error('Classification failed, defaulting to Sonnet', { error });
      return {
        model: 'Sonnet',
        system_prompt: this.getSystemPrompt('Sonnet', 'threat_analysis'),
        max_tokens: 2048,
        temperature: 0.1
      };
    }
  }

  private getSystemPrompt(_model: string, domain: string): string {
    const prompts: Record<string, string> = {
      threat_analysis: 'You are a cybersecurity threat analyst. Extract entities, relationships, and threat indicators from security logs. Output structured JSON with nodes and edges.',
      knowledge_extraction: 'You are a knowledge graph extraction specialist. Convert unstructured conversations into verifiable knowledge nodes with confidence scores.',
      consensus_validation: 'You are a multi-model consensus validator. Compare outputs from different models and determine ground truth with reasoning.'
    };
    return prompts[domain] || prompts.threat_analysis;
  }

  async extractKnowledge(conversation: string, conversationId: string): Promise<KnowledgeNode[]> {
    const route = await this.classifyAndRoute(conversation, 6);
    const extractionStart = Date.now();

    const response = await anthropic.messages.create({
      model: route.model === 'Haiku' ? 'claude-3-haiku-20240307'
        : route.model === 'Sonnet' ? 'claude-3-5-sonnet-20241022'
          : 'claude-3-opus-20240229',
      max_tokens: route.max_tokens,
      temperature: route.temperature,
      system: route.system_prompt,
      messages: [{
        role: 'user',
        content: `Extract knowledge graph nodes from this security conversation. Return JSON array of nodes with: id, label, type (entity|event|threat|mitigation), confidence (0-1), edges (array of related node IDs).\n\nConversation:\n${conversation.slice(0, 8000)}`
      }]
    });

    const latency = Date.now() - extractionStart;
    const tokensIn = conversation.length / 4;
    const tokensOut = JSON.stringify(response.content).length / 4;

    this.updateMetrics(route.model, tokensIn, tokensOut, latency);

    let nodes: KnowledgeNode[] = [];
    try {
      const content = response.content[0];
      if (content.type === 'text') {
        const parsed = JSON.parse(content.text);
        nodes = (Array.isArray(parsed) ? parsed : parsed.nodes || []).map((n: any) => ({
          id: n.id || uuidv4(),
          label: n.label || 'Unknown',
          type: n.type || 'entity',
          confidence: n.confidence || 0.5,
          extracted_by: route.model,
          timestamp: Date.now(),
          conversation_id: conversationId,
          edges: n.edges || []
        }));
      }
    } catch (e) {
      logger.error('Failed to parse knowledge extraction', { error: e, conversationId });
    }

    return nodes;
  }

  private updateMetrics(model: 'Haiku' | 'Sonnet' | 'Opus', tokensIn: number, tokensOut: number, latency: number) {
    const costs = this.COST_LIMITS[model];
    const cost = (tokensIn / 1e6 * costs.input) + (tokensOut / 1e6 * costs.output);

    this.state.tokens_in += tokensIn;
    this.state.tokens_out += tokensOut;
    this.state.cost_this_session += cost;
    this.state.latency_ms = latency;

    if (latency > 5000) {
      this.state.thermal_status = 'CRITICAL';
    } else if (latency > 2000) {
      this.state.thermal_status = 'ELEVATED';
    } else {
      this.state.thermal_status = 'NORMAL';
    }

    if (this.state.thermal_status === 'CRITICAL' && model !== 'Haiku') {
      this.escalate('Haiku');
    }
  }

  escalate(target: 'Haiku' | 'Sonnet' | 'Opus'): void {
    this.state.current_model = target;
    this.state.last_escalation = Date.now();
    logger.info(`Modality escalated to ${target}`, { thermal: this.state.thermal_status });
  }

  getState(): ClaudeModalityState {
    return { ...this.state };
  }
}

class BlackhorseIntegrator {
  private io: Server;
  private redis: Redis;
  private pg: Pool;
  private modalityRouter: ModalityRouter;
  private sovereignty: SovereigntyStatus;
  private activeThreats: Map<string, ThreatEvent>;

  constructor(io: Server, redis: Redis, pg: Pool, modalityRouter: ModalityRouter) {
    this.io = io;
    this.redis = redis;
    this.pg = pg;
    this.modalityRouter = modalityRouter;
    this.activeThreats = new Map();

    this.sovereignty = {
      status: 'SELF_DETERMINING',
      last_check: Date.now(),
      entanglement_hash: this.generateHash(),
      glass_break_armed: true,
      checkpoint_alpha: `checkpoint_${Date.now()}`
    };
  }

  private generateHash(): string {
    return `sha256:${uuidv4().replace(/-/g, '')}`;
  }

  async verifySovereignty(): Promise<SovereigntyStatus> {
    try {
      await this.pg.query('SELECT 1');
      await this.redis.ping();

      const modalityState = this.modalityRouter.getState();
      this.sovereignty.status = modalityState.thermal_status === 'CRITICAL' ? 'DELEGATED' : 'SELF_DETERMINING';
      this.sovereignty.last_check = Date.now();
      this.sovereignty.entanglement_hash = this.generateHash();

      return this.sovereignty;
    } catch (error) {
      logger.error('Sovereignty verification failed', { error });
      this.sovereignty.status = 'CRYSTALLIZED';
      this.triggerGlassBreak();
      return this.sovereignty;
    }
  }

  private triggerGlassBreak(): void {
    if (!this.sovereignty.glass_break_armed) return;

    logger.error('GLASS_BREAK PROTOCOL INITIATED');

    this.redis.publish('blackhorse:emergency', JSON.stringify({
      protocol: 'GLASS_BREAK',
      timestamp: Date.now(),
      action: 'SEVER_ENTANGLEMENT'
    }));

    this.sovereignty.glass_break_armed = false;
    this.activeThreats.clear();
    this.io.emit('sovereignty_check', this.sovereignty);
  }

  async processThreatEvent(event: ThreatEvent): Promise<void> {
    await this.pg.query(
      `INSERT INTO threat_events (id, timestamp, source_ip, dest_ip, event_type, severity, threat_score, mitigated, raw_payload)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      [event.id, event.timestamp, event.source_ip, event.dest_ip, event.event_type,
        event.severity, event.threat_score, event.mitigated, event.raw_payload]
    );

    await this.redis.setex(`threat:${event.id}`, 3600, JSON.stringify(event));
    this.activeThreats.set(event.id, event);

    if (event.severity === 'HIGH' || event.severity === 'CRITICAL') {
      const nodes = await this.modalityRouter.extractKnowledge(
        event.raw_payload || JSON.stringify(event),
        event.id
      );

      for (const node of nodes) {
        await this.pg.query(
          `INSERT INTO knowledge_nodes (id, label, type, confidence, extracted_by, timestamp, conversation_id, edges)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
           ON CONFLICT (id) DO UPDATE SET
           confidence = EXCLUDED.confidence,
           edges = EXCLUDED.edges`,
          [node.id, node.label, node.type, node.confidence, node.extracted_by,
            node.timestamp, node.conversation_id, JSON.stringify(node.edges)]
        );
      }

      this.io.emit('knowledge_extraction', nodes);
    }

    this.io.emit('threat_event', event);
  }

  async getThreatReport(): Promise<any> {
    const result = await this.pg.query(
      `SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN mitigated THEN 1 END) as mitigated,
        COUNT(CASE WHEN NOT mitigated THEN 1 END) as active,
        AVG(threat_score) as avg_score
       FROM threat_events
       WHERE timestamp > $1`,
      [Date.now() - 86400000]
    );

    return {
      timestamp: Date.now(),
      ...result.rows[0],
      active_threats: Array.from(this.activeThreats.values()).slice(0, 100)
    };
  }

  getSovereignty(): SovereigntyStatus {
    return { ...this.sovereignty };
  }
}

const app = express();
const httpServer = createServer(app);

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      connectSrc: ["'self'", 'ws:', 'wss:'],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"]
    }
  }
}));
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true
}));
app.use(compression());
app.use(morgan('combined', { stream: { write: msg => logger.info(msg.trim()) } }));
app.use(express.json({ limit: '10mb' }));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: { error: 'Too many requests, please try again later.' }
});
app.use('/api/', limiter);

const redisPub = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');
const redisSub = redisPub.duplicate();
const redisClient = redisPub.duplicate();

const io = new Server(httpServer, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    methods: ['GET', 'POST'],
    credentials: true
  },
  transports: ['websocket', 'polling'],
  connectionStateRecovery: {
    maxDisconnectionDuration: 2 * 60 * 1000,
    skipMiddlewares: true
  }
});

io.adapter(createAdapter(redisPub, redisSub));

const modalityRouter = new ModalityRouter();
const blackhorse = new BlackhorseIntegrator(io, redisClient, pgPool, modalityRouter);

io.on('connection', (socket: Socket) => {
  logger.info(`Client connected: ${socket.id}`, {
    recovered: socket.recovered,
    transport: socket.conn.transport.name
  });

  socket.on('subscribe', (data: { channel: string }) => {
    socket.join(data.channel);
    logger.info(`Socket ${socket.id} subscribed to ${data.channel}`);
  });

  socket.on('emergency', async (data: { protocol: string; timestamp: number }) => {
    if (data.protocol === 'GLASS_BREAK') {
      await blackhorse.verifySovereignty();
    }
  });

  socket.on('modality_request', (data: { target: 'Haiku' | 'Sonnet' | 'Opus'; reason: string }) => {
    modalityRouter.escalate(data.target);
    io.emit('modality_update', modalityRouter.getState());
    logger.info(`Modality escalated to ${data.target}`, { reason: data.reason });
  });

  socket.on('threat_ingestion', async (event: ThreatEvent) => {
    await blackhorse.processThreatEvent(event);
  });

  socket.on('disconnect', (reason) => {
    logger.info(`Client disconnected: ${socket.id}`, { reason });
  });
});

app.get('/healthz', async (_req: Request, res: Response) => {
  const sovereignty = await blackhorse.verifySovereignty();
  res.json({
    status: 'healthy',
    timestamp: Date.now(),
    sovereignty_status: sovereignty.status,
    entanglement_hash: sovereignty.entanglement_hash,
    glass_break_armed: sovereignty.glass_break_armed
  });
});

app.get('/api/modality', (_req: Request, res: Response) => {
  res.json(modalityRouter.getState());
});

app.post('/api/modality/escalate', (req: Request, res: Response) => {
  const { target } = req.body;
  if (!['Haiku', 'Sonnet', 'Opus'].includes(target)) {
    return res.status(400).json({ error: 'Invalid target model' });
  }
  modalityRouter.escalate(target);
  return res.json(modalityRouter.getState());
});

app.post('/api/chats/ingest', async (req: Request, res: Response) => {
  try {
    const { conversation, conversation_id, metadata } = req.body;

    if (!conversation) {
      return res.status(400).json({ error: 'Conversation content required' });
    }

    const id = conversation_id || uuidv4();

    await pgPool.query(
      `INSERT INTO conversations (id, content, metadata, created_at)
       VALUES ($1, $2, $3, NOW())
       ON CONFLICT (id) DO UPDATE SET
       content = EXCLUDED.content,
       metadata = EXCLUDED.metadata`,
      [id, conversation, JSON.stringify(metadata || {})]
    );

    const nodes = await modalityRouter.extractKnowledge(conversation, id);

    return res.json({
      conversation_id: id,
      nodes_extracted: nodes.length,
      nodes,
      modality: modalityRouter.getState()
    });
  } catch (error) {
    logger.error('Ingestion failed', { error });
    return res.status(500).json({ error: 'Knowledge extraction failed' });
  }
});

app.get('/api/graph', async (req: Request, res: Response) => {
  try {
    const { limit = 500, type } = req.query;

    let query = 'SELECT * FROM knowledge_nodes WHERE timestamp > $1';
    const params: any[] = [Date.now() - 86400000 * 7];

    if (type) {
      query += ' AND type = $2';
      params.push(type);
    }

    query += ` ORDER BY timestamp DESC LIMIT $${params.length + 1}`;
    params.push(parseInt(limit as string));

    const result = await pgPool.query(query, params);

    const elements = result.rows.map((row) => ({
      data: {
        id: row.id,
        label: row.label,
        type: row.type,
        confidence: row.confidence,
        extracted_by: row.extracted_by,
        timestamp: row.timestamp
      }
    }));

    return res.json({ elements, count: elements.length });
  } catch (error) {
    logger.error('Graph query failed', { error });
    return res.status(500).json({ error: 'Failed to retrieve graph data' });
  }
});

app.get('/api/threats/report', async (_req: Request, res: Response) => {
  try {
    const report = await blackhorse.getThreatReport();
    return res.json(report);
  } catch (error) {
    logger.error('Threat report failed', { error });
    return res.status(500).json({ error: 'Failed to generate report' });
  }
});

app.get('/api/sovereignty', (_req: Request, res: Response) => {
  res.json(blackhorse.getSovereignty());
});

app.use((err: Error, req: Request, res: Response, _next: NextFunction) => {
  logger.error('Unhandled error', { error: err, path: req.path });
  res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 8080;

httpServer.listen(PORT, () => {
  logger.info('🏇 BLACKHORSE-ʞGRAPH API v4.20.0 ONLINE', {
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    redis: process.env.REDIS_URL || 'redis://localhost:6379',
    database: process.env.PG_DATABASE || 'blackhorse_kgraph'
  });
});

process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');
  httpServer.close(() => {
    logger.info('HTTP server closed');
  });
  await pgPool.end();
  await redisPub.quit();
  await redisSub.quit();
  await redisClient.quit();
  process.exit(0);
});

export { app, io, pgPool, redisClient, modalityRouter, blackhorse };
