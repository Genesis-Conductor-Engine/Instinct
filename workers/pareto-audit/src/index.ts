/**
 * Pareto-Audit Cloudflare Worker
 *
 * Intercepts Google Cloud pipeline emails and filters non-compliant
 * opportunities to ensure the 270-day sales cycle is reserved
 * exclusively for $100K–$5M ACV targets.
 *
 * Deployed at pareto.genesisconductor.io
 */

interface Env {
  ARR_FLOOR_USD: string;
  ROI_TARGET: string;
  MIN_ACV_USD: string;
  MAX_ACV_USD: string;
  SALES_CYCLE_DAYS: string;
  AUDIT_CACHE: KVNamespace;
  AUDIT_DB: D1Database;
}

interface PipelineOpportunity {
  id: string;
  source: string;
  acv_usd: number;
  arr_usd: number;
  stage: string;
  deployment_type: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

interface AuditResult {
  opportunity_id: string;
  compliant: boolean;
  violations: string[];
  roi_estimate: number;
  recommendation: 'approve' | 'reject' | 'escalate';
  timestamp: string;
}

interface ThermodynamicMetrics {
  power_watts: number;
  efficiency_eta: number;
  cold_snap_active: boolean;
}

/**
 * Compliance rules for the pareto filter
 */
const COMPLIANCE_RULES = {
  // Terminology compliance
  VALID_DEPLOYMENT_TYPES: ['Deployment: Foundations', 'Deployment: Modernization', 'Deployment: Migration'],
  INVALID_DEPLOYMENT_TYPES: ['Production Deployment', 'Direct Deployment'],

  // Minimum thresholds
  MIN_ARR_FIRST_YEAR: 25000,
  MIN_ACV: 100000,
  MAX_ACV: 5000000,

  // ROI requirements
  MIN_ROI_RATIO: 10,

  // Sales cycle
  MAX_SALES_CYCLE_DAYS: 270,
};

/**
 * Main worker handler
 */
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route handling
      switch (url.pathname) {
        case '/api/audit':
          return handleAudit(request, env, corsHeaders);

        case '/api/audit/batch':
          return handleBatchAudit(request, env, corsHeaders);

        case '/api/metrics':
          return handleMetrics(request, env, corsHeaders);

        case '/api/thermodynamic':
          return handleThermodynamic(request, env, corsHeaders);

        case '/health':
          return new Response(JSON.stringify({ status: 'healthy', timestamp: new Date().toISOString() }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders },
          });

        default:
          return new Response(JSON.stringify({ error: 'Not found' }), {
            status: 404,
            headers: { 'Content-Type': 'application/json', ...corsHeaders },
          });
      }
    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({ error: 'Internal server error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }
  },
};

/**
 * Handle single opportunity audit
 */
async function handleAudit(request: Request, env: Env, headers: Record<string, string>): Promise<Response> {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', ...headers },
    });
  }

  const opportunity: PipelineOpportunity = await request.json();
  const result = auditOpportunity(opportunity, env);

  // Store result in D1
  await storeAuditResult(result, env);

  return new Response(JSON.stringify(result), {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

/**
 * Handle batch audit of multiple opportunities
 */
async function handleBatchAudit(request: Request, env: Env, headers: Record<string, string>): Promise<Response> {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', ...headers },
    });
  }

  const { opportunities }: { opportunities: PipelineOpportunity[] } = await request.json();

  // Guard against empty array to avoid NaN from division by zero
  if (!opportunities || opportunities.length === 0) {
    return new Response(JSON.stringify({
      results: [],
      summary: {
        total: 0,
        approved: 0,
        rejected: 0,
        escalated: 0,
        compliance_rate: 1.0,
        avg_roi: 0,
      }
    }), {
      headers: { 'Content-Type': 'application/json', ...headers },
    });
  }

  const results = opportunities.map(opp => auditOpportunity(opp, env));

  // Store results in parallel
  await Promise.all(results.map(r => storeAuditResult(r, env)));

  // Calculate summary statistics
  const summary = {
    total: results.length,
    approved: results.filter(r => r.recommendation === 'approve').length,
    rejected: results.filter(r => r.recommendation === 'reject').length,
    escalated: results.filter(r => r.recommendation === 'escalate').length,
    compliance_rate: results.filter(r => r.compliant).length / results.length,
    avg_roi: results.reduce((sum, r) => sum + r.roi_estimate, 0) / results.length,
  };

  return new Response(JSON.stringify({ results, summary }), {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

/**
 * Core audit logic for a single opportunity
 */
function auditOpportunity(opportunity: PipelineOpportunity, env: Env): AuditResult {
  const violations: string[] = [];
  let compliant = true;

  const arrFloor = parseInt(env.ARR_FLOOR_USD);
  const minAcv = parseInt(env.MIN_ACV_USD);
  const maxAcv = parseInt(env.MAX_ACV_USD);
  const roiTarget = parseInt(env.ROI_TARGET);

  // Check ARR floor
  if (opportunity.arr_usd < arrFloor) {
    violations.push(`ARR ${opportunity.arr_usd} below ${arrFloor} floor`);
    compliant = false;
  }

  // Check ACV range
  if (opportunity.acv_usd < minAcv) {
    violations.push(`ACV ${opportunity.acv_usd} below ${minAcv} minimum for 270-day cycle`);
    compliant = false;
  }
  if (opportunity.acv_usd > maxAcv) {
    violations.push(`ACV ${opportunity.acv_usd} above ${maxAcv} maximum`);
    compliant = false;
  }

  // Check deployment type terminology
  if (COMPLIANCE_RULES.INVALID_DEPLOYMENT_TYPES.includes(opportunity.deployment_type)) {
    violations.push(`Invalid deployment type: "${opportunity.deployment_type}" - use "Deployment: Foundations" instead`);
    compliant = false;
  }

  if (!COMPLIANCE_RULES.VALID_DEPLOYMENT_TYPES.includes(opportunity.deployment_type)) {
    violations.push(`Unrecognized deployment type: "${opportunity.deployment_type}"`);
    // This is a warning, not a violation
  }

  // Calculate estimated ROI (simplified model)
  const estimatedCost = opportunity.acv_usd * 0.05; // 5% of ACV as sales cost
  const roiEstimate = estimatedCost > 0 ? opportunity.acv_usd / estimatedCost : 0;

  if (roiEstimate < roiTarget) {
    violations.push(`ROI estimate ${roiEstimate.toFixed(1)}:1 below ${roiTarget}:1 target`);
    compliant = false;
  }

  // Determine recommendation
  let recommendation: 'approve' | 'reject' | 'escalate' = 'approve';

  if (!compliant) {
    if (violations.length > 2) {
      recommendation = 'reject';
    } else {
      recommendation = 'escalate';
    }
  }

  // Special case: high-value opportunities get escalated for review
  if (opportunity.acv_usd > 1000000) {
    recommendation = 'escalate';
  }

  return {
    opportunity_id: opportunity.id,
    compliant,
    violations,
    roi_estimate: roiEstimate,
    recommendation,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Store audit result in D1 database
 */
async function storeAuditResult(result: AuditResult, env: Env): Promise<void> {
  try {
    await env.AUDIT_DB.prepare(`
      INSERT INTO audit_results (opportunity_id, compliant, violations, roi_estimate, recommendation, timestamp)
      VALUES (?, ?, ?, ?, ?, ?)
    `).bind(
      result.opportunity_id,
      result.compliant ? 1 : 0,
      JSON.stringify(result.violations),
      result.roi_estimate,
      result.recommendation,
      result.timestamp
    ).run();
  } catch (error) {
    console.error('Failed to store audit result:', error);
  }
}

/**
 * Handle metrics endpoint for OpenTelemetry integration
 */
async function handleMetrics(request: Request, env: Env, headers: Record<string, string>): Promise<Response> {
  // Get metrics from D1
  const stats = await env.AUDIT_DB.prepare(`
    SELECT
      COUNT(*) as total,
      SUM(CASE WHEN compliant = 1 THEN 1 ELSE 0 END) as compliant_count,
      AVG(roi_estimate) as avg_roi,
      SUM(CASE WHEN recommendation = 'approve' THEN 1 ELSE 0 END) as approved,
      SUM(CASE WHEN recommendation = 'reject' THEN 1 ELSE 0 END) as rejected,
      SUM(CASE WHEN recommendation = 'escalate' THEN 1 ELSE 0 END) as escalated
    FROM audit_results
    WHERE timestamp > datetime('now', '-24 hours')
  `).first();

  const metrics = {
    timestamp: new Date().toISOString(),
    period: '24h',
    audits: {
      total: stats?.total ?? 0,
      compliant: stats?.compliant_count ?? 0,
      compliance_rate: stats?.total ? (stats.compliant_count as number) / (stats.total as number) : 1.0,
    },
    recommendations: {
      approved: stats?.approved ?? 0,
      rejected: stats?.rejected ?? 0,
      escalated: stats?.escalated ?? 0,
    },
    roi: {
      average: (stats?.avg_roi as number) ?? 0,
      target: parseInt(env.ROI_TARGET),
      meets_target: ((stats?.avg_roi as number) ?? 0) >= parseInt(env.ROI_TARGET),
    },
    config: {
      arr_floor: parseInt(env.ARR_FLOOR_USD),
      min_acv: parseInt(env.MIN_ACV_USD),
      max_acv: parseInt(env.MAX_ACV_USD),
      sales_cycle_days: parseInt(env.SALES_CYCLE_DAYS),
    },
  };

  return new Response(JSON.stringify(metrics), {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

/**
 * Handle thermodynamic metrics from Instinct platform
 */
async function handleThermodynamic(request: Request, env: Env, headers: Record<string, string>): Promise<Response> {
  if (request.method === 'POST') {
    // Receive thermodynamic metrics
    const metrics: ThermodynamicMetrics = await request.json();

    // Store in KV for quick access
    await env.AUDIT_CACHE.put('thermodynamic_state', JSON.stringify(metrics), {
      expirationTtl: 60, // 1 minute TTL
    });

    // If cold snap is active, pause high-compute operations
    if (metrics.cold_snap_active) {
      await env.AUDIT_CACHE.put('processing_throttled', 'true', {
        expirationTtl: 300, // 5 minutes
      });
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { 'Content-Type': 'application/json', ...headers },
    });
  }

  // GET: return current thermodynamic state
  const state = await env.AUDIT_CACHE.get('thermodynamic_state');
  const throttled = await env.AUDIT_CACHE.get('processing_throttled');

  return new Response(JSON.stringify({
    state: state ? JSON.parse(state) : null,
    throttled: throttled === 'true',
  }), {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}
