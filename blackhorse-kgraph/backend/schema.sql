-- Blackhorse-ʞGraph Database Schema
-- PostgreSQL 15+ optimized for knowledge graph storage

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE knowledge_nodes (
    id VARCHAR(255) PRIMARY KEY,
    label VARCHAR(500) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('entity', 'event', 'threat', 'mitigation')),
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    extracted_by VARCHAR(50) NOT NULL CHECK (extracted_by IN ('Haiku', 'Sonnet', 'Opus')),
    timestamp BIGINT NOT NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    edges JSONB DEFAULT '[]',
    properties JSONB DEFAULT '{}',
    vector_embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE knowledge_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_id VARCHAR(255) REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relationship VARCHAR(100) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    properties JSONB DEFAULT '{}',
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_id, target_id, relationship)
);

CREATE TABLE threat_events (
    id VARCHAR(255) PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    source_ip INET NOT NULL,
    dest_ip INET NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('HONEYPOT_ACCESS', 'PORT_SCAN', 'EXFILTRATION', 'KG_EXTRACTION')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    threat_score DECIMAL(3,2) NOT NULL,
    mitigated BOOLEAN DEFAULT FALSE,
    raw_payload TEXT,
    knowledge_node_ids JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE modality_telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    current_model VARCHAR(50) NOT NULL,
    tokens_in BIGINT NOT NULL DEFAULT 0,
    tokens_out BIGINT NOT NULL DEFAULT 0,
    cost_session DECIMAL(10,6) NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL,
    thermal_status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE sovereignty_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(50) NOT NULL,
    entanglement_hash VARCHAR(255) NOT NULL,
    glass_break_armed BOOLEAN NOT NULL,
    checkpoint_alpha VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_knowledge_nodes_type ON knowledge_nodes(type);
CREATE INDEX idx_knowledge_nodes_timestamp ON knowledge_nodes(timestamp DESC);
CREATE INDEX idx_knowledge_nodes_conversation ON knowledge_nodes(conversation_id);
CREATE INDEX idx_knowledge_nodes_confidence ON knowledge_nodes(confidence DESC);
CREATE INDEX idx_threat_events_timestamp ON threat_events(timestamp DESC);
CREATE INDEX idx_threat_events_severity ON threat_events(severity);
CREATE INDEX idx_threat_events_mitigated ON threat_events(mitigated);
CREATE INDEX idx_modality_telemetry_session ON modality_telemetry(session_id, timestamp DESC);

CREATE INDEX idx_knowledge_nodes_edges ON knowledge_nodes USING GIN(edges);
CREATE INDEX idx_knowledge_nodes_properties ON knowledge_nodes USING GIN(properties);
CREATE INDEX idx_conversations_metadata ON conversations USING GIN(metadata);

CREATE INDEX idx_conversations_content_trgm ON conversations USING GIN(content gin_trgm_ops);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE threat_events ENABLE ROW LEVEL SECURITY;

CREATE VIEW high_confidence_nodes AS
SELECT * FROM knowledge_nodes WHERE confidence >= 0.8;

CREATE VIEW active_threats AS
SELECT * FROM threat_events WHERE mitigated = FALSE AND timestamp > EXTRACT(EPOCH FROM NOW() - INTERVAL '24 hours') * 1000;

CREATE VIEW daily_cost_summary AS
SELECT
    DATE(timestamp) as date,
    current_model,
    SUM(tokens_in) as total_tokens_in,
    SUM(tokens_out) as total_tokens_out,
    SUM(cost_session) as total_cost,
    AVG(latency_ms) as avg_latency
FROM modality_telemetry
GROUP BY DATE(timestamp), current_model;
