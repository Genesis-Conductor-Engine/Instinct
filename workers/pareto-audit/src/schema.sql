-- Pareto-Audit D1 Database Schema
-- Run with: wrangler d1 execute pareto-audit --file=./src/schema.sql

-- Audit results table
CREATE TABLE IF NOT EXISTS audit_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id TEXT NOT NULL,
    compliant INTEGER NOT NULL DEFAULT 0,
    violations TEXT, -- JSON array
    roi_estimate REAL,
    recommendation TEXT CHECK(recommendation IN ('approve', 'reject', 'escalate')),
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_results(timestamp);

-- Index for opportunity lookups
CREATE INDEX IF NOT EXISTS idx_audit_opportunity ON audit_results(opportunity_id);

-- Index for compliance filtering
CREATE INDEX IF NOT EXISTS idx_audit_compliant ON audit_results(compliant);

-- Pipeline opportunities cache (for deduplication)
CREATE TABLE IF NOT EXISTS opportunity_cache (
    opportunity_id TEXT PRIMARY KEY,
    source TEXT,
    acv_usd REAL,
    arr_usd REAL,
    stage TEXT,
    deployment_type TEXT,
    last_audit TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Thermodynamic state log
CREATE TABLE IF NOT EXISTS thermodynamic_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    power_watts REAL,
    efficiency_eta REAL,
    cold_snap_active INTEGER,
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Index for thermodynamic queries
CREATE INDEX IF NOT EXISTS idx_thermo_timestamp ON thermodynamic_log(timestamp);
