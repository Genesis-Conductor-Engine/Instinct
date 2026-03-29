"""Tests for the Workspace Orchestrator component."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.agents.neurohumogenistic.workspace_orchestrator import (
    OrchestratorConfig,
    OrchestratorState,
    ParetoAuditFilter,
    WorkspaceOrchestrator,
)
from src.agents.neurohumogenistic.edge_agent import (
    DirectiveType,
    WorkspaceDirective,
)


class TestOrchestratorConfig:
    """Tests for orchestrator configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OrchestratorConfig()

        assert config.monthly_revenue_target_usd == 70_000.0
        assert config.arr_floor_usd == 25_000.0
        assert config.roi_target_ratio == 10.0
        assert config.sales_cycle_days == 270
        assert config.min_acv_usd == 100_000.0
        assert config.max_acv_usd == 5_000_000.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = OrchestratorConfig(
            monthly_revenue_target_usd=100_000.0,
            arr_floor_usd=50_000.0,
        )

        assert config.monthly_revenue_target_usd == 100_000.0
        assert config.arr_floor_usd == 50_000.0


class TestParetoAuditFilter:
    """Tests for the Pareto audit filter."""

    @pytest.fixture
    def filter(self):
        config = OrchestratorConfig()
        return ParetoAuditFilter(config)

    def test_rejects_production_deployment_terminology(self, filter):
        """Production Deployment should be rejected."""
        directive = WorkspaceDirective(
            id="test_1",
            source="gmail",
            content="Schedule Production Deployment for next week",
            directive_type=DirectiveType.REVENUE_PIPELINE,
        )

        assert filter.evaluate(directive) is False
        assert filter._filtered_count == 1

    def test_accepts_deployment_foundations_terminology(self, filter):
        """Deployment: Foundations should be accepted."""
        directive = WorkspaceDirective(
            id="test_2",
            source="gmail",
            content="Deployment: Foundations scheduled with $150k ACV",
            directive_type=DirectiveType.REVENUE_PIPELINE,
        )

        assert filter.evaluate(directive) is True
        assert filter._passed_count == 1

    def test_arr_floor_validation(self, filter):
        """ARR floor should be validated for PSF directives."""
        directive = WorkspaceDirective(
            id="test_3",
            source="gmail",
            content="Deal Registration with $30,000 ARR commitment",
            directive_type=DirectiveType.PSF_COMPLIANCE,
        )

        # Should pass - $30k > $25k floor
        assert filter.evaluate(directive) is True

    def test_acv_range_validation(self, filter):
        """ACV should be within $100K-$5M range."""
        directive = WorkspaceDirective(
            id="test_4",
            source="gmail",
            content="Pipeline opportunity with $200k ACV",
            directive_type=DirectiveType.REVENUE_PIPELINE,
        )

        # Should pass - $200k within range
        assert filter.evaluate(directive) is True

    def test_get_stats(self, filter):
        """Statistics should be tracked correctly."""
        directive1 = WorkspaceDirective(
            id="test_5",
            source="gmail",
            content="Production Deployment",
            directive_type=DirectiveType.REVENUE_PIPELINE,
        )
        directive2 = WorkspaceDirective(
            id="test_6",
            source="gmail",
            content="Deployment: Foundations $100k ACV",
            directive_type=DirectiveType.REVENUE_PIPELINE,
        )

        filter.evaluate(directive1)  # Should fail
        filter.evaluate(directive2)  # Should pass

        stats = filter.get_stats()

        assert stats["total_evaluated"] == 2
        assert stats["passed"] == 1
        assert stats["filtered"] == 1
        assert stats["pass_rate"] == 0.5


class TestOrchestratorState:
    """Tests for orchestrator state."""

    def test_default_state(self):
        """Test default state values."""
        state = OrchestratorState()

        assert state.total_directives_processed == 0
        assert state.estimated_pipeline_value_usd == 0.0
        assert state.is_cold_snap is False

    def test_state_initialization_timestamp(self):
        """Started timestamp should be set."""
        state = OrchestratorState()

        assert isinstance(state.started_at, datetime)


class TestWorkspaceOrchestrator:
    """Tests for the Workspace Orchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = WorkspaceOrchestrator()

        assert orchestrator.config is not None
        assert orchestrator.pareto_filter is not None
        assert orchestrator.edge_agent is not None
        assert orchestrator.thermodynamic_kernel is not None

    def test_orchestrator_with_custom_config(self):
        """Test orchestrator with custom config."""
        config = OrchestratorConfig(
            monthly_revenue_target_usd=100_000.0,
            enable_frugalgpt_cascade=False,
        )

        orchestrator = WorkspaceOrchestrator(config=config)

        assert orchestrator.config.monthly_revenue_target_usd == 100_000.0
        assert orchestrator.frugalgpt is None

    def test_handlers_registered(self):
        """Test that handlers are registered for all directive types."""
        orchestrator = WorkspaceOrchestrator()

        # Check that handlers were registered
        for dtype in DirectiveType:
            assert len(orchestrator.edge_agent._handlers[dtype]) > 0

    def test_get_state(self):
        """Test getting orchestrator state."""
        orchestrator = WorkspaceOrchestrator()

        state = orchestrator.get_state()

        assert isinstance(state, OrchestratorState)
        assert state.last_sync is not None

    def test_get_status_report(self):
        """Test generating status report."""
        orchestrator = WorkspaceOrchestrator()

        report = orchestrator.get_status_report()

        assert "timestamp" in report
        assert "directives" in report
        assert "revenue" in report
        assert "thermodynamic" in report
        assert "system" in report

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Test starting and stopping orchestrator."""
        orchestrator = WorkspaceOrchestrator()

        await orchestrator.start()
        assert orchestrator._running is True
        assert len(orchestrator._tasks) == 2

        await orchestrator.stop()
        assert orchestrator._running is False
        assert len(orchestrator._tasks) == 0


class TestDirectiveHandlers:
    """Tests for directive-specific handlers."""

    @pytest.fixture
    def orchestrator(self):
        return WorkspaceOrchestrator()

    @pytest.mark.asyncio
    async def test_handle_portfolio_directive(self, orchestrator):
        """Test handling high-leverage portfolio directives."""
        directive = WorkspaceDirective(
            id="test_portfolio",
            source="keep",
            content="Wolfspeed SiC strategy",
            directive_type=DirectiveType.HIGH_LEVERAGE_PORTFOLIO,
            priority=8,
        )

        await orchestrator._handle_portfolio_directive(directive)

        state = orchestrator.get_state()
        assert state.directives_by_type.get("vector_1") == 1

    @pytest.mark.asyncio
    async def test_handle_doe_directive(self, orchestrator):
        """Test handling DOE mission directives."""
        directive = WorkspaceDirective(
            id="test_doe",
            source="keep",
            content="DE-FOA-0003612 Phase I",
            directive_type=DirectiveType.DOE_MISSION_ALIGNED,
            priority=7,
        )

        await orchestrator._handle_doe_directive(directive)

        assert directive.metadata.get("doe_phase") == "phase_1"
        assert directive.metadata.get("foa_number") == "DE-FOA-0003612"

    @pytest.mark.asyncio
    async def test_handle_psf_directive_compliant(self, orchestrator):
        """Test handling compliant PSF directives."""
        directive = WorkspaceDirective(
            id="test_psf",
            source="gmail",
            content="Deal Registration with $50k ARR verified",
            directive_type=DirectiveType.PSF_COMPLIANCE,
            priority=9,
        )

        await orchestrator._handle_psf_directive(directive)

        state = orchestrator.get_state()
        assert state.compliant_opportunities == 1

    @pytest.mark.asyncio
    async def test_handle_revenue_directive(self, orchestrator):
        """Test handling revenue pipeline directives."""
        directive = WorkspaceDirective(
            id="test_revenue",
            source="gmail",
            content="Pipeline opportunity worth $250,000",
            directive_type=DirectiveType.REVENUE_PIPELINE,
            priority=8,
        )

        await orchestrator._handle_revenue_directive(directive)

        state = orchestrator.get_state()
        assert state.estimated_pipeline_value_usd == 250000.0


class TestYenneeferSync:
    """Tests for Yennefer hourly sync."""

    @pytest.fixture
    def mock_workspace_client(self):
        client = AsyncMock()
        client.get_keep_notes = AsyncMock(return_value=[])
        client.get_tasks = AsyncMock(return_value=[])
        client.get_emails = AsyncMock(return_value=[])
        return client

    @pytest.mark.asyncio
    async def test_yennefer_sync(self, mock_workspace_client):
        """Test Yennefer sync operation."""
        orchestrator = WorkspaceOrchestrator(workspace_client=mock_workspace_client)

        report = await orchestrator.sync_yennefer()

        assert "timestamp" in report
        assert "directives" in report
        assert orchestrator.get_state().last_sync is not None
