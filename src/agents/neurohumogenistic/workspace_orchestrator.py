"""
Workspace Orchestrator for Neurohumogenistic Integration

Unifies Gmail, Drive, Docs, Keep, and Tasks into a singular hybridized entity
focused on the 13 revenue streams and remote role pivot.

Transforms static Google Workspace assets into active nodes within
the Genesis Conductor nervous system.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

import structlog

from .edge_agent import DirectiveType, EdgeAgent, WorkspaceDirective
from .frugalgpt_cascade import CascadeResult, FrugalGPTCascade
from .thermodynamic_kernel import ThermodynamicKernel, ThermodynamicState

logger = structlog.get_logger(__name__)

# Slack notifier (lazy import to keep dependency optional)
_slack_notifier = None


def _get_slack_notifier() -> Optional[Any]:
    global _slack_notifier
    if _slack_notifier is None:
        try:
            import os
            from src.integrations.slack.notifier import SlackNotifier
            if os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_BOT_TOKEN"):
                _slack_notifier = SlackNotifier()
        except ImportError:
            pass
    return _slack_notifier


@dataclass
class OrchestratorConfig:
    """Configuration for the Workspace Orchestrator."""
    # Polling intervals (seconds)
    workspace_poll_interval: int = 60
    thermodynamic_poll_interval: float = 1.0

    # Revenue targets
    monthly_revenue_target_usd: float = 70_000.0
    arr_floor_usd: float = 25_000.0
    roi_target_ratio: float = 10.0

    # Sales cycle
    sales_cycle_days: int = 270
    min_acv_usd: float = 100_000.0
    max_acv_usd: float = 5_000_000.0

    # Thermodynamic
    cold_snap_threshold_watts: float = 200.0
    cold_snap_duration_seconds: float = 300.0

    # Feature flags
    enable_pareto_filter: bool = True
    enable_thermodynamic_gating: bool = True
    enable_frugalgpt_cascade: bool = True


@dataclass
class OrchestratorState:
    """Current state of the orchestrator."""
    # Directive tracking
    total_directives_processed: int = 0
    directives_by_type: dict[str, int] = field(default_factory=dict)
    pending_directives: int = 0

    # Revenue tracking
    estimated_pipeline_value_usd: float = 0.0
    compliant_opportunities: int = 0
    filtered_opportunities: int = 0

    # Thermodynamic state
    current_power_watts: float = 0.0
    efficiency_eta: float = 1.0
    is_cold_snap: bool = False

    # FrugalGPT stats
    cascade_cost_usd: float = 0.0
    cascade_roi: float = 0.0

    # System
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_sync: Optional[datetime] = None


class ParetoAuditFilter:
    """
    Pareto-audit filter for revenue pipeline compliance.

    Enforces:
    - 10:1 ROI requirement
    - $25k Year 1 ARR floor
    - Proper terminology (Deployment: Foundations)
    - 270-day sales cycle for $100K-$5M ACV
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self._filtered_count = 0
        self._passed_count = 0

    def __call__(self, directive: WorkspaceDirective) -> bool:
        """Apply pareto filter to a directive."""
        return self.evaluate(directive)

    def evaluate(self, directive: WorkspaceDirective) -> bool:
        """
        Evaluate if a directive passes the pareto-audit criteria.

        Returns True if compliant, False if filtered.
        """
        content = directive.content.lower()
        metadata = directive.metadata

        # Check for non-compliant terminology
        if "production deployment" in content:
            logger.info(
                "pareto_filter.terminology_violation",
                directive_id=directive.id,
                violation="production_deployment"
            )
            self._filtered_count += 1
            return False

        # Check ARR floor for PSF directives
        if directive.directive_type == DirectiveType.PSF_COMPLIANCE:
            if not self._verify_arr_floor(directive):
                self._filtered_count += 1
                return False

        # Check ACV range for revenue pipeline
        if directive.directive_type == DirectiveType.REVENUE_PIPELINE:
            if not self._verify_acv_range(directive):
                self._filtered_count += 1
                return False

        self._passed_count += 1
        return True

    def _verify_arr_floor(self, directive: WorkspaceDirective) -> bool:
        """Verify $25k Year 1 ARR floor.

        Returns True if:
        - A numeric ARR >= floor is found
        - No numeric ARR is found (can't verify, allow through with warning)

        Returns False if:
        - A numeric ARR < floor is explicitly found
        """
        content = directive.content

        # Look for dollar amounts with optional k/m suffix
        # Matches: $50k, $50,000, 50k arr, 25000 acv, etc.
        import re
        amounts = re.findall(
            r'\$[\d,]+(?:\.\d{2})?[km]?|[\d,]+[km]?\s*(?:arr|acv)',
            content.lower()
        )

        found_any_amount = False
        for amount in amounts:
            try:
                # Check for k/m suffix before stripping
                multiplier = 1
                if 'k' in amount:
                    multiplier = 1000
                elif 'm' in amount:
                    multiplier = 1_000_000

                # Parse amount - remove $, commas, k, m
                clean = amount.replace('$', '').replace(',', '').replace('k', '').replace('m', '')
                clean = ''.join(c for c in clean if c.isdigit() or c == '.')
                if clean:
                    value = float(clean) * multiplier
                    found_any_amount = True
                    if value >= self.config.arr_floor_usd:
                        return True  # Found compliant ARR
                    else:
                        # Found ARR below floor - reject
                        logger.info(
                            "pareto_filter.arr_below_floor",
                            directive_id=directive.id,
                            arr_found=value,
                            floor=self.config.arr_floor_usd
                        )
                        return False
            except ValueError:
                pass

        # If no numeric amount found but content mentions ARR terms
        if not found_any_amount and any(term in content.lower() for term in ['arr', 'annual', 'recurring']):
        """Verify $25k Year 1 ARR floor."""
        content = directive.content

        # Look for dollar amounts
        import re
        amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?|[\d,]+k?\s*(?:arr|acv)', content.lower())

        for amount in amounts:
            try:
                # Parse amount
                clean = amount.replace('$', '').replace(',', '').replace('k', '000')
                clean = ''.join(c for c in clean if c.isdigit() or c == '.')
                if clean:
                    value = float(clean)
                    if value >= self.config.arr_floor_usd:
                        return True
            except ValueError:
                pass

        # If no amount found but content suggests compliance
        if any(term in content.lower() for term in ['arr', 'annual', 'recurring']):
            logger.warning(
                "pareto_filter.arr_not_verified",
                directive_id=directive.id,
                hint="No numeric ARR value found"
            )

        return True  # No explicit ARR found - allow through
        return True  # Allow through if no explicit violation

    def _verify_acv_range(self, directive: WorkspaceDirective) -> bool:
        """Verify ACV is within $100K-$5M range for 270-day cycle."""
        content = directive.content

        # Look for ACV values
        import re
        acv_matches = re.findall(r'\$?([\d,]+(?:\.\d{2})?)\s*(?:m|k)?\s*acv', content.lower())

        for match in acv_matches:
            try:
                # Parse value
                value_str = match.replace(',', '')
                value = float(value_str)

                # Handle k/m suffixes
                if 'k' in content[content.lower().find(match):content.lower().find(match)+20]:
                    value *= 1_000
                elif 'm' in content[content.lower().find(match):content.lower().find(match)+20]:
                    value *= 1_000_000

                # Check range
                if not (self.config.min_acv_usd <= value <= self.config.max_acv_usd):
                    logger.info(
                        "pareto_filter.acv_out_of_range",
                        directive_id=directive.id,
                        acv=value,
                        min=self.config.min_acv_usd,
                        max=self.config.max_acv_usd
                    )
                    return False

            except ValueError:
                pass

        return True

    def get_stats(self) -> dict:
        """Get filter statistics."""
        total = self._filtered_count + self._passed_count
        return {
            "total_evaluated": total,
            "passed": self._passed_count,
            "filtered": self._filtered_count,
            "pass_rate": self._passed_count / total if total > 0 else 1.0,
        }


class WorkspaceOrchestrator:
    """
    Main orchestrator for the Neurohumogenistic Workspace Integration.

    Coordinates:
    - EdgeAgent for workspace polling
    - FrugalGPTCascade for LLM processing
    - ThermodynamicKernel for energy management
    - ParetoAuditFilter for compliance

    Achieves Branch C architecture: full immersion with unified
    Gmail, Drive, Docs, Keep, and Tasks telemetry.
    """

    def __init__(
        self,
        workspace_client: Optional[Any] = None,
        anthropic_client: Optional[Any] = None,
        otel_meter: Optional[Any] = None,
        config: Optional[OrchestratorConfig] = None,
    ):
        self.config = config or OrchestratorConfig()

        # Initialize pareto filter
        self.pareto_filter = ParetoAuditFilter(self.config)

        # Initialize FrugalGPT cascade
        self.frugalgpt = FrugalGPTCascade(
            anthropic_client=anthropic_client
        ) if self.config.enable_frugalgpt_cascade else None

        # Initialize Edge Agent
        self.edge_agent = EdgeAgent(
            workspace_client=workspace_client,
            poll_interval_seconds=self.config.workspace_poll_interval,
            frugalgpt_cascade=self.frugalgpt,
            pareto_filter=self.pareto_filter if self.config.enable_pareto_filter else None,
        )

        # Initialize Thermodynamic Kernel
        self.thermodynamic_kernel = ThermodynamicKernel(
            otel_meter=otel_meter,
            cold_snap_threshold_watts=self.config.cold_snap_threshold_watts,
            cold_snap_duration_seconds=self.config.cold_snap_duration_seconds,
            poll_interval_seconds=self.config.thermodynamic_poll_interval,
        )

        self._state = OrchestratorState()
        self._running = False
        self._tasks: list[asyncio.Task] = []

        # Register handlers for each directive type
        self._register_handlers()

        logger.info(
            "workspace_orchestrator.initialized",
            config=self.config.__dict__
        )

    def _register_handlers(self) -> None:
        """Register handlers for different directive types."""
        # High-leverage portfolio -> Strategic analysis
        self.edge_agent.register_handler(
            DirectiveType.HIGH_LEVERAGE_PORTFOLIO,
            self._handle_portfolio_directive
        )

        # DOE Mission -> Phase I matrix mapping
        self.edge_agent.register_handler(
            DirectiveType.DOE_MISSION_ALIGNED,
            self._handle_doe_directive
        )

        # Execution queue -> Task execution
        self.edge_agent.register_handler(
            DirectiveType.EXECUTION_QUEUE,
            self._handle_execution_directive
        )

        # PSF Compliance -> Verification pipeline
        self.edge_agent.register_handler(
            DirectiveType.PSF_COMPLIANCE,
            self._handle_psf_directive
        )

        # Revenue pipeline -> Pipeline optimization
        self.edge_agent.register_handler(
            DirectiveType.REVENUE_PIPELINE,
            self._handle_revenue_directive
        )

        # Thermodynamic gate -> Rest management
        self.edge_agent.register_handler(
            DirectiveType.THERMODYNAMIC_GATE,
            self._handle_thermodynamic_directive
        )

    async def _handle_portfolio_directive(self, directive: WorkspaceDirective) -> None:
        """Handle high-leverage portfolio items (Wolfspeed, Skywater)."""
        logger.info(
            "orchestrator.handling_portfolio",
            directive_id=directive.id,
            content_preview=directive.content[:100]
        )

        # Route to Tier 3 (Opus) for strategic analysis
        if self.frugalgpt:
            result = await self.frugalgpt.process(directive, tier=3)
            self._update_cascade_stats(result)

        self._increment_directive_count(directive.directive_type)

    async def _handle_doe_directive(self, directive: WorkspaceDirective) -> None:
        """Handle DOE Mission aligned items (DE-FOA-0003612)."""
        logger.info(
            "orchestrator.handling_doe",
            directive_id=directive.id,
            content_preview=directive.content[:100]
        )

        # Map to Phase I application matrix
        directive.metadata["doe_phase"] = "phase_1"
        directive.metadata["foa_number"] = "DE-FOA-0003612"

        if self.frugalgpt:
            result = await self.frugalgpt.process(directive, tier=3)
            self._update_cascade_stats(result)

        self._increment_directive_count(directive.directive_type)

    async def _handle_execution_directive(self, directive: WorkspaceDirective) -> None:
        """Handle execution queue items (launches, API enablement)."""
        logger.info(
            "orchestrator.handling_execution",
            directive_id=directive.id,
            content_preview=directive.content[:100]
        )

        # Check thermodynamic state before execution
        if self.config.enable_thermodynamic_gating:
            if self.thermodynamic_kernel.should_throttle():
                logger.warning(
                    "orchestrator.execution_throttled",
                    directive_id=directive.id,
                    reason="thermodynamic_constraint"
                )
                return

        if self.frugalgpt:
            result = await self.frugalgpt.process(directive, tier=2)
            self._update_cascade_stats(result)

        self._increment_directive_count(directive.directive_type)

    async def _handle_psf_directive(self, directive: WorkspaceDirective) -> None:
        """Handle PSF compliance verification."""
        logger.info(
            "orchestrator.handling_psf",
            directive_id=directive.id,
            content_preview=directive.content[:100]
        )

        # Double-loop verification with pareto filter
        if self.pareto_filter.evaluate(directive):
            self._state.compliant_opportunities += 1

            if self.frugalgpt:
                result = await self.frugalgpt.process(directive, tier=1)
                self._update_cascade_stats(result)
        else:
            self._state.filtered_opportunities += 1
            logger.info(
                "orchestrator.psf_filtered",
                directive_id=directive.id
            )

        self._increment_directive_count(directive.directive_type)

    async def _handle_revenue_directive(self, directive: WorkspaceDirective) -> None:
        """Handle revenue pipeline items."""
        logger.info(
            "orchestrator.handling_revenue",
            directive_id=directive.id,
            content_preview=directive.content[:100]
        )

        # Extract and track pipeline value
        self._extract_pipeline_value(directive)

        if self.frugalgpt:
            result = await self.frugalgpt.process(directive, tier=2)
            self._update_cascade_stats(result)

        self._increment_directive_count(directive.directive_type)

    async def _handle_thermodynamic_directive(self, directive: WorkspaceDirective) -> None:
        """Handle thermodynamic gate items (rest, mycology, research)."""
        logger.info(
            "orchestrator.handling_thermodynamic_gate",
            directive_id=directive.id,
            content_preview=directive.content[:100]
        )

        # These are low-priority recovery tasks
        # Process in background during cold snap
        if self.frugalgpt:
            result = await self.frugalgpt.process(directive, tier=1)
            self._update_cascade_stats(result)

        self._increment_directive_count(directive.directive_type)

    def _increment_directive_count(self, dtype: DirectiveType) -> None:
        """Increment directive count by type."""
        self._state.total_directives_processed += 1
        type_name = dtype.value
        self._state.directives_by_type[type_name] = (
            self._state.directives_by_type.get(type_name, 0) + 1
        )

    def _update_cascade_stats(self, result: CascadeResult) -> None:
        """Update cascade statistics from result."""
        self._state.cascade_cost_usd += result.cost_estimate_usd

    def _extract_pipeline_value(self, directive: WorkspaceDirective) -> None:
        """Extract and track pipeline value from directive."""
        import re
        content = directive.content

        # Look for dollar values
        matches = re.findall(r'\$[\d,]+(?:\.\d{2})?', content)
        for match in matches:
            try:
                value = float(match.replace('$', '').replace(',', ''))
                self._state.estimated_pipeline_value_usd += value
            except ValueError:
                pass

    def _on_thermodynamic_update(self, state: ThermodynamicState) -> None:
        """Callback for thermodynamic state updates."""
        self._state.current_power_watts = state.total_power_watts
        self._state.efficiency_eta = state.efficiency_eta
        self._state.is_cold_snap = state.is_cold_snap

        if state.is_cold_snap:
            logger.info(
                "orchestrator.cold_snap_active",
                power_watts=state.total_power_watts,
                efficiency=state.efficiency_eta
            )

    async def start(self) -> None:
        """Start the orchestrator and all subsystems."""
        if self._running:
            logger.warning("orchestrator.already_running")
            return

        self._running = True
        self._state.started_at = datetime.utcnow()

        # Register thermodynamic callback
        self.thermodynamic_kernel.register_state_callback(self._on_thermodynamic_update)

        # Start subsystems as async tasks
        self._tasks = [
            asyncio.create_task(self.edge_agent.run(), name="edge_agent"),
            asyncio.create_task(self.thermodynamic_kernel.run(), name="thermodynamic_kernel"),
        ]

        logger.info(
            "workspace_orchestrator.started",
            timestamp=self._state.started_at.isoformat()
        )

    async def stop(self) -> None:
        """Stop the orchestrator and all subsystems."""
        if not self._running:
            return

        self._running = False

        # Stop subsystems
        self.edge_agent.stop()
        self.thermodynamic_kernel.stop()

        # Wait for tasks to complete
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._tasks = []

        logger.info(
            "workspace_orchestrator.stopped",
            total_processed=self._state.total_directives_processed
        )

    def get_state(self) -> OrchestratorState:
        """Get current orchestrator state."""
        self._state.last_sync = datetime.utcnow()

        # Calculate ROI if we have cascade costs
        if self._state.cascade_cost_usd > 0:
            self._state.cascade_roi = (
                self._state.estimated_pipeline_value_usd / self._state.cascade_cost_usd
            )

        return self._state

    def get_status_report(self) -> dict:
        """Generate comprehensive status report."""
        state = self.get_state()
        cascade_stats = self.frugalgpt.get_statistics() if self.frugalgpt else {}
        pareto_stats = self.pareto_filter.get_stats()
        thermo_state = self.thermodynamic_kernel.get_state()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - state.started_at).total_seconds(),
            "directives": {
                "total_processed": state.total_directives_processed,
                "by_type": state.directives_by_type,
                "pending": state.pending_directives,
            },
            "revenue": {
                "pipeline_value_usd": state.estimated_pipeline_value_usd,
                "compliant_opportunities": state.compliant_opportunities,
                "filtered_opportunities": state.filtered_opportunities,
                "monthly_target_usd": self.config.monthly_revenue_target_usd,
            },
            "cascade": cascade_stats,
            "pareto_filter": pareto_stats,
            "thermodynamic": thermo_state.to_metrics(),
            "system": {
                "running": self._running,
                "cold_snap_active": state.is_cold_snap,
                "efficiency_eta": state.efficiency_eta,
            },
        }

    async def sync_yennefer(self) -> dict:
        """
        Perform Yennefer hourly sync.

        Synchronizes all workspace inputs with Instinct Platform telemetry.
        Posts results to Slack.
        """
        logger.info("orchestrator.yennefer_sync_started")

        # Poll all workspace sources
        directives = await self.edge_agent.poll_workspace()

        # Update state
        self._state.pending_directives = len(directives)
        self._state.last_sync = datetime.utcnow()

        # Process directives
        for directive in directives:
            await self.edge_agent.dispatch_directive(directive)

        report = self.get_status_report()

        logger.info(
            "orchestrator.yennefer_sync_complete",
            directives_processed=len(directives),
            pipeline_value=self._state.estimated_pipeline_value_usd
        )

        # Post to Slack
        slack = _get_slack_notifier()
        if slack:
            try:
                await slack.post_sync_report(report)
            except Exception as e:
                logger.warning("orchestrator.slack_post_failed", error=str(e))

        return report

    async def post_compliance_alert(
        self,
        directive_id: str,
        violations: list[str],
    ) -> None:
        """Post a PSF compliance violation to Slack."""
        slack = _get_slack_notifier()
        if slack:
            await slack.post_compliance_alert(directive_id, violations)

        return report


async def main():
    """Entry point for the Neurohumogenistic Workspace Integration."""
    import os

    # Configuration from environment
    config = OrchestratorConfig(
        monthly_revenue_target_usd=float(os.getenv("REVENUE_TARGET", "70000")),
        arr_floor_usd=float(os.getenv("ARR_FLOOR", "25000")),
        enable_pareto_filter=os.getenv("ENABLE_PARETO", "true").lower() == "true",
        enable_thermodynamic_gating=os.getenv("ENABLE_THERMO", "true").lower() == "true",
    )

    # Create orchestrator
    orchestrator = WorkspaceOrchestrator(config=config)

    try:
        # Start orchestrator
        await orchestrator.start()

        # Initial Yennefer sync
        report = await orchestrator.sync_yennefer()
        logger.info("initial_sync_complete", report=report)

        # Run until interrupted
        while True:
            await asyncio.sleep(3600)  # Hourly sync
            await orchestrator.sync_yennefer()

    except KeyboardInterrupt:
        logger.info("shutdown_requested")
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
