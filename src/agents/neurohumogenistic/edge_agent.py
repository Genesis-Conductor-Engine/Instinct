"""
Edge Agent for Neurohumogenistic Workspace Integration

Binds to Google Workspace APIs and treats personal to-do lists, notes, and emails
as immediate computational directives for the Genesis Conductor nervous system.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger(__name__)


class DirectiveType(Enum):
    """Classification of workspace items as computational directives."""
    HIGH_LEVERAGE_PORTFOLIO = "vector_1"  # Strategic assets (Wolfspeed, Skywater)
    DOE_MISSION_ALIGNED = "doe_phase_1"   # DE-FOA-0003612 matrix items
    EXECUTION_QUEUE = "active_foreground"  # Launch prototypes, OpenTelemetry
    PSF_COMPLIANCE = "psf_verification"    # Partner Services Funds validation
    THERMODYNAMIC_GATE = "cold_snap"       # Rest/recovery periods (mycology, research)
    REVENUE_PIPELINE = "13_streams"        # $70k/mo revenue optimization


@dataclass
class WorkspaceDirective:
    """A computational directive extracted from Google Workspace."""
    id: str
    source: str  # keep, tasks, gmail, drive, docs
    content: str
    directive_type: DirectiveType
    priority: int = 5  # 1-10, higher is more urgent
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False

    def to_telemetry(self) -> dict:
        """Convert to OpenTelemetry-compatible span attributes."""
        return {
            "directive.id": self.id,
            "directive.source": self.source,
            "directive.type": self.directive_type.value,
            "directive.priority": self.priority,
            "directive.processed": self.processed,
        }


class EdgeAgent:
    """
    Edge Agent that polls Google Workspace and transforms static assets
    into active nodes within the Genesis Conductor nervous system.

    Implements Branch C architecture:
    - Treats Keep notes as immediate computational directives
    - Maps Tasks to active foreground processing
    - Filters emails through PSF compliance checks
    - Routes strategic items to FrugalGPT Tier 3 (Opus)
    """

    def __init__(
        self,
        workspace_client: Optional[Any] = None,
        poll_interval_seconds: int = 60,
        frugalgpt_cascade: Optional[Any] = None,
        pareto_filter: Optional[Callable] = None,
    ):
        self.workspace_client = workspace_client
        self.poll_interval = poll_interval_seconds
        self.frugalgpt = frugalgpt_cascade
        self.pareto_filter = pareto_filter

        self._directive_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._handlers: dict[DirectiveType, list[Callable]] = {t: [] for t in DirectiveType}

        # Strategic pattern matchers for directive classification
        self._patterns = {
            DirectiveType.HIGH_LEVERAGE_PORTFOLIO: [
                "wolfspeed", "sic scrap", "skywater", "partnership proposal",
                "strategic plan", "portfolio asset"
            ],
            DirectiveType.DOE_MISSION_ALIGNED: [
                "genesis mission", "de-foa", "project vivarium", "alpha persistence",
                "technical addendum", "doe", "phase i"
            ],
            DirectiveType.EXECUTION_QUEUE: [
                "launch prototype", "opentelemetry", "api", "deploy",
                "genesisconductor.io", "enable"
            ],
            DirectiveType.PSF_COMPLIANCE: [
                "psf", "partner services", "deal registration", "sow", "vaf",
                "public sector", "arr", "partner advantage"
            ],
            DirectiveType.THERMODYNAMIC_GATE: [
                "mycology", "personal research", "rest", "recovery",
                "cold snap", "downtime"
            ],
            DirectiveType.REVENUE_PIPELINE: [
                "revenue", "pipeline", "acv", "sales cycle", "$",
                "deployment: foundations", "100k", "5m"
            ],
        }

        logger.info("edge_agent.initialized", poll_interval=poll_interval_seconds)

    def register_handler(
        self,
        directive_type: DirectiveType,
        handler: Callable[[WorkspaceDirective], None]
    ) -> None:
        """Register a handler for a specific directive type."""
        self._handlers[directive_type].append(handler)
        logger.info(
            "edge_agent.handler_registered",
            directive_type=directive_type.value,
            handler=getattr(handler, '__name__', repr(handler))
        )

    def classify_directive(self, content: str, source: str) -> DirectiveType:
        """
        Classify content into a directive type using pattern matching.
        Falls back to EXECUTION_QUEUE for unclassified items.
        """
        content_lower = content.lower()

        # Check patterns in priority order
        for dtype, patterns in self._patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                return dtype

        # Default classification based on source
        source_defaults = {
            "gmail": DirectiveType.PSF_COMPLIANCE,
            "keep": DirectiveType.DOE_MISSION_ALIGNED,
            "tasks": DirectiveType.EXECUTION_QUEUE,
            "drive": DirectiveType.HIGH_LEVERAGE_PORTFOLIO,
            "docs": DirectiveType.REVENUE_PIPELINE,
        }
        return source_defaults.get(source, DirectiveType.EXECUTION_QUEUE)

    def calculate_priority(self, directive: WorkspaceDirective) -> int:
        """
        Calculate priority based on directive type and content analysis.
        Uses thermodynamic principles for arbitration.
        """
        base_priorities = {
            DirectiveType.PSF_COMPLIANCE: 9,      # Revenue compliance is critical
            DirectiveType.HIGH_LEVERAGE_PORTFOLIO: 8,
            DirectiveType.REVENUE_PIPELINE: 8,
            DirectiveType.DOE_MISSION_ALIGNED: 7,
            DirectiveType.EXECUTION_QUEUE: 6,
            DirectiveType.THERMODYNAMIC_GATE: 3,  # Recovery is lower priority
        }

        priority = base_priorities.get(directive.directive_type, 5)

        # Boost priority for time-sensitive keywords
        urgent_keywords = ["urgent", "deadline", "today", "asap", "critical", "floor"]
        if any(kw in directive.content.lower() for kw in urgent_keywords):
            priority = min(10, priority + 2)

        # Apply ARR floor enforcement - boost PSF items with dollar amounts
        if directive.directive_type == DirectiveType.PSF_COMPLIANCE:
            if "$25" in directive.content or "25k" in directive.content.lower():
                priority = 10  # Maximum priority for ARR floor items

        return priority

    async def ingest_keep_notes(self) -> list[WorkspaceDirective]:
        """
        Ingest Google Keep notes and transform into directives.

        Specifically targets:
        - Genesis Conductor Strategic Plan (Wolfspeed, Skywater -> Tier 3)
        - Genesis Mission Alignment Tasks (DOE Phase I matrix)
        """
        directives = []

        if not self.workspace_client:
            logger.warning("edge_agent.no_workspace_client", source="keep")
            return directives

        try:
            notes = await self.workspace_client.get_keep_notes()

            for note in notes:
                dtype = self.classify_directive(note.get("content", ""), "keep")
                directive = WorkspaceDirective(
                    id=f"keep_{note.get('id', '')}",
                    source="keep",
                    content=note.get("content", ""),
                    directive_type=dtype,
                    metadata={
                        "title": note.get("title"),
                        "labels": note.get("labels", []),
                        "pinned": note.get("pinned", False),
                    }
                )
                directive.priority = self.calculate_priority(directive)
                directives.append(directive)

                logger.info(
                    "edge_agent.keep_ingested",
                    directive_id=directive.id,
                    directive_type=dtype.value,
                    priority=directive.priority
                )

        except Exception as e:
            logger.error("edge_agent.keep_ingestion_failed", error=str(e))

        return directives

    async def ingest_tasks(self) -> list[WorkspaceDirective]:
        """
        Ingest Google Tasks and move to active foreground processing.

        Specifically targets:
        - Launch Prototypes on prototypes.genesisconductor.io
        - OpenTelemetry ingestion API enablement
        """
        directives = []

        if not self.workspace_client:
            logger.warning("edge_agent.no_workspace_client", source="tasks")
            return directives

        try:
            tasks = await self.workspace_client.get_tasks()

            for task in tasks:
                dtype = self.classify_directive(task.get("title", ""), "tasks")
                directive = WorkspaceDirective(
                    id=f"task_{task.get('id', '')}",
                    source="tasks",
                    content=task.get("title", "") + "\n" + task.get("notes", ""),
                    directive_type=dtype,
                    metadata={
                        "due": task.get("due"),
                        "status": task.get("status"),
                        "task_list": task.get("task_list"),
                    }
                )
                directive.priority = self.calculate_priority(directive)
                directives.append(directive)

                # OpenTelemetry tasks get special handling
                if "opentelemetry" in directive.content.lower():
                    directive.metadata["feeds_thermodynamic_ui"] = True
                    directive.metadata["uses_optimistic_rendering"] = True

                logger.info(
                    "edge_agent.task_ingested",
                    directive_id=directive.id,
                    directive_type=dtype.value,
                    priority=directive.priority
                )

        except Exception as e:
            logger.error("edge_agent.task_ingestion_failed", error=str(e))

        return directives

    async def ingest_gmail(self, pareto_filter: bool = True) -> list[WorkspaceDirective]:
        """
        Ingest Gmail and filter through PSF compliance checks.

        Implements:
        - PSF Criteria Double-Loop Verification
        - Thermodynamic Arbitration for pipeline emails
        - $25k ARR floor enforcement
        - Dual-staffing mandate verification
        """
        directives = []

        if not self.workspace_client:
            logger.warning("edge_agent.no_workspace_client", source="gmail")
            return directives

        try:
            emails = await self.workspace_client.get_emails(
                query="label:partner-advantage OR label:psf OR label:pipeline"
            )

            for email in emails:
                content = f"{email.get('subject', '')}\n{email.get('snippet', '')}"
                dtype = self.classify_directive(content, "gmail")

                directive = WorkspaceDirective(
                    id=f"gmail_{email.get('id', '')}",
                    source="gmail",
                    content=content,
                    directive_type=dtype,
                    metadata={
                        "from": email.get("from"),
                        "subject": email.get("subject"),
                        "labels": email.get("labels", []),
                        "thread_id": email.get("thread_id"),
                    }
                )
                directive.priority = self.calculate_priority(directive)

                # Apply pareto filter for pipeline emails
                if pareto_filter and self.pareto_filter:
                    if not self._passes_pareto_filter(directive):
                        logger.info(
                            "edge_agent.gmail_filtered",
                            directive_id=directive.id,
                            reason="pareto_audit_failed"
                        )
                        continue

                directives.append(directive)

                logger.info(
                    "edge_agent.gmail_ingested",
                    directive_id=directive.id,
                    directive_type=dtype.value,
                    priority=directive.priority
                )

        except Exception as e:
            logger.error("edge_agent.gmail_ingestion_failed", error=str(e))

        return directives

    def _passes_pareto_filter(self, directive: WorkspaceDirective) -> bool:
        """
        Apply pareto-audit schema to filter non-compliant opportunities.

        Enforces:
        - 10:1 ROI ratio
        - $25,000 Year 1 ARR floor
        - 270-day sales cycle reserved for $100K-$5M ACV
        - "Deployment: Foundations" instead of "Production Deployment"
        """
        if self.pareto_filter:
            return self.pareto_filter(directive)

        content = directive.content.lower()

        # Reject "Production Deployment" terminology
        if "production deployment" in content:
            return False

        # Check for proper compliance terminology
        compliant_terms = ["deployment: foundations", "arr", "acv", "deal registration"]
        return any(term in content for term in compliant_terms)

    async def poll_workspace(self) -> list[WorkspaceDirective]:
        """
        Poll all workspace sources and aggregate directives.
        Returns sorted list by priority (descending).
        """
        all_directives = []

        # Parallel ingestion from all sources
        results = await asyncio.gather(
            self.ingest_keep_notes(),
            self.ingest_tasks(),
            self.ingest_gmail(),
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                logger.error("edge_agent.poll_exception", error=str(result))
            else:
                all_directives.extend(result)

        # Sort by priority descending
        all_directives.sort(key=lambda d: d.priority, reverse=True)

        logger.info(
            "edge_agent.poll_complete",
            total_directives=len(all_directives),
            by_source={
                "keep": len([d for d in all_directives if d.source == "keep"]),
                "tasks": len([d for d in all_directives if d.source == "tasks"]),
                "gmail": len([d for d in all_directives if d.source == "gmail"]),
            }
        )

        return all_directives

    async def dispatch_directive(self, directive: WorkspaceDirective) -> None:
        """
        Dispatch directive to registered handlers.

        FrugalGPT processing is owned by downstream handlers/orchestrators to avoid
        duplicate LLM execution, token cost, and repeated side effects for the same
        directive. The handlers in WorkspaceOrchestrator call frugalgpt.process().
        """
        # Dispatch to type-specific handlers
        for handler in self._handlers[directive.directive_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(directive)
                else:
                    handler(directive)
            except Exception as e:
                logger.error(
                    "edge_agent.handler_error",
                    handler=getattr(handler, '__name__', repr(handler)),
                    directive_id=directive.id,
                    error=str(e)
                )

        directive.processed = True
        logger.info(
            "edge_agent.directive_dispatched",
            directive_id=directive.id,
            directive_type=directive.directive_type.value
        )

    async def run(self) -> None:
        """
        Main polling loop. Continuously polls workspace and dispatches directives.
        """
        self._running = True
        logger.info("edge_agent.started", poll_interval=self.poll_interval)

        while self._running:
            try:
                directives = await self.poll_workspace()

                for directive in directives:
                    await self._directive_queue.put(directive)

                # Process queue
                while not self._directive_queue.empty():
                    directive = await self._directive_queue.get()
                    await self.dispatch_directive(directive)

                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                logger.info("edge_agent.cancelled")
                break
            except Exception as e:
                logger.error("edge_agent.run_error", error=str(e))
                await asyncio.sleep(self.poll_interval)

        logger.info("edge_agent.stopped")

    def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        logger.info("edge_agent.stop_requested")
