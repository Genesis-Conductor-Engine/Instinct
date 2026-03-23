"""
Neurohumogenistic Workspace Integration Agent

Hybridization of Human and Artificial Intelligence via Google Workspace Telemetry.
Implements Branch C architecture: Neuro-Symbolic convergence binding Edge-Agent
to Google Keep Genesis Mission and Tasks queue.

Components:
- EdgeAgent: Polls Google Workspace (Keep, Tasks, Gmail, Drive, Docs)
- FrugalGPTCascade: Tier 1-3 LLM processing with cost optimization
- ThermodynamicKernel: RAPL/IPMI sensor integration
- ParetoAuditFilter: Revenue stream compliance (10:1 ROI, $25k ARR floor)
"""

from .edge_agent import EdgeAgent
from .frugalgpt_cascade import FrugalGPTCascade
from .thermodynamic_kernel import ThermodynamicKernel
from .workspace_orchestrator import WorkspaceOrchestrator

__all__ = [
    "EdgeAgent",
    "FrugalGPTCascade",
    "ThermodynamicKernel",
    "WorkspaceOrchestrator",
]

__version__ = "0.1.0"
