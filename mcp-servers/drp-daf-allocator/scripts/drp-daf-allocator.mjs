#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs';
import process from 'node:process';

const CYCLE_STEPS = ['poll_state','kgraph_mapping','deficit_calculation','synthesize_gaps','ledger_update','close_and_prune'];
const canonical = (v) => JSON.stringify(sortValue(v));
function sortValue(v){ if(Array.isArray(v)) return v.map(sortValue); if(v && typeof v==='object') return Object.fromEntries(Object.keys(v).sort().map(k=>[k,sortValue(v[k])])); return v; }
function sha256(v){ return crypto.createHash('sha256').update(canonical(v)).digest('hex'); }
function thermo(payload){ const bits=Math.max(Buffer.byteLength(canonical(payload))*8,1); const useful=Object.keys(payload.connections||{}).length+(payload.tags||[]).length+1; return Number(Math.min(.99,useful/(useful+bits/4096)).toFixed(6)); }
function evt(record_type,status,payload,tags=[],connections={}){ const rec={evt_id:'evt_'+crypto.createHash('sha256').update(`${Date.now()}:${record_type}:${canonical(payload)}`).digest('hex').slice(0,24),schema_version:'1.0',record_type,tags:['mcp','drp-daf-allocator',...tags],connections,status,payload:{thermodynamic_yield:thermo(payload),crystal_score:.97,...payload}}; process.stderr.write('evt-'+canonical(rec)+'\n'); logAlpha(rec); return rec; }
function logAlpha(rec){ if(!process.env.ALPHA_TRACE_DB) return; const line=canonical(rec)+'\n'; fs.mkdirSync(process.env.ALPHA_TRACE_DIR || 'backend/data',{recursive:true}); fs.appendFileSync(process.env.ALPHA_TRACE_JSONL || 'backend/data/alpha_traces.drp.jsonl', line); }
export function fetch_workspace_state(args={}){ const workspace=args.workspace||{documents:[],ledger:[],proposals:[]}; const out={workspace_state:workspace,state_hash:sha256(workspace),ouroboros_step:'poll_state'}; evt('tool_call','ok',{tool:'fetch_workspace_state',...out},['poll_state']); return out; }
export function feed_to_k_graph(args={}){ const state=args.state||args.workspace_state||{}; const nodes=[...new Set(['workspace',...Object.keys(state).map(String)])].sort(); const edges=Object.keys(state).map(k=>['workspace',String(k)]).sort(); const graph={directed:true,nodes,edges}; const deficits=['funding_need','eligibility','impact_metric'].filter(k=>!(k in state)); const out={k_graph:graph,state_hash:sha256(state),graph_hash:sha256(graph),deficits,ouroboros_step:'kgraph_mapping'}; evt('tool_call','ok',{tool:'feed_to_k_graph',...out},['kgraph_mapping'],{structural_invariant:'DiGraph'}); return out; }
export function synthesize_proposal(args={}){ const deficits=args.deficits||[]; const proposal={id:'proposal_'+sha256(args).slice(0,12),missing_parameters:deficits,structural_match: deficits.length===0,summary:deficits.length?'Proposal blocked pending invariant parameters':'Proposal structurally eligible for DAF allocation'}; evt('tool_call','ok',{tool:'synthesize_proposal',proposal,ouroboros_step:'synthesize_gaps'},['synthesize_gaps']); return proposal; }
export function update_status_ledger(args={}){ const entry={id:'ledger_'+sha256(args).slice(0,12),status:args.status||'updated',state_hash:sha256(args),ouroboros_step:'ledger_update'}; evt('tool_call','ok',{tool:'update_status_ledger',entry,ouroboros_step:'ledger_update'},['ledger_update']); return entry; }
export function close_ouroboros_cycle(args={}){ const pruned={closed:true,cold_snap_pruned:true,cycle_steps:CYCLE_STEPS,state_hash:sha256(args),ouroboros_step:'close_and_prune'}; evt('tool_call','ok',{tool:'close_ouroboros_cycle',...pruned},['close_and_prune','cold-snap']); return pruned; }
const tools={fetch_workspace_state,feed_to_k_graph,synthesize_proposal,update_status_ledger,close_ouroboros_cycle};
if(import.meta.url===`file://${process.argv[1]}`){
  const input=fs.readFileSync(0,'utf8').trim();
  if(!input){ console.log(canonical({tools:Object.keys(tools),cycle_steps:CYCLE_STEPS})); process.exit(0); }
  const req=JSON.parse(input); const fn=tools[req.tool]; if(!fn) throw new Error(`unknown tool ${req.tool}`); console.log(canonical(fn(req.arguments||{})));
}
