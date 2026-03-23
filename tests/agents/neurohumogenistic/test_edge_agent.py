"""Tests for the Edge Agent component."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.neurohumogenistic.edge_agent import (
    DirectiveType,
    EdgeAgent,
    WorkspaceDirective,
)


class TestDirectiveClassification:
    """Tests for directive classification logic."""

    def setup_method(self):
        self.agent = EdgeAgent()

    def test_classify_wolfspeed_as_high_leverage(self):
        """Wolfspeed mentions should be classified as high-leverage portfolio."""
        dtype = self.agent.classify_directive(
            "Wolfspeed SiC scrap integration proposal", "keep"
        )
        assert dtype == DirectiveType.HIGH_LEVERAGE_PORTFOLIO

    def test_classify_skywater_as_high_leverage(self):
        """Skywater mentions should be classified as high-leverage portfolio."""
        dtype = self.agent.classify_directive(
            "Skywater Technologies partnership discussion", "keep"
        )
        assert dtype == DirectiveType.HIGH_LEVERAGE_PORTFOLIO

    def test_classify_doe_mission(self):
        """DOE mission mentions should be classified correctly."""
        dtype = self.agent.classify_directive(
            "DE-FOA-0003612 Phase I application", "keep"
        )
        assert dtype == DirectiveType.DOE_MISSION_ALIGNED

    def test_classify_project_vivarium(self):
        """Project Vivarium mentions should be DOE mission aligned."""
        dtype = self.agent.classify_directive(
            "Technical Addendum for Project Vivarium", "keep"
        )
        assert dtype == DirectiveType.DOE_MISSION_ALIGNED

    def test_classify_opentelemetry_as_execution(self):
        """OpenTelemetry tasks should be execution queue."""
        dtype = self.agent.classify_directive(
            "Enable OpenTelemetry ingestion API", "tasks"
        )
        assert dtype == DirectiveType.EXECUTION_QUEUE

    def test_classify_psf_as_compliance(self):
        """PSF mentions should be compliance."""
        dtype = self.agent.classify_directive(
            "PSF Deal Registration for US Public Sector", "gmail"
        )
        assert dtype == DirectiveType.PSF_COMPLIANCE

    def test_classify_mycology_as_thermodynamic_gate(self):
        """Mycology/personal research should be thermodynamic gate."""
        dtype = self.agent.classify_directive(
            "Mycology research (1-3 hours)", "keep"
        )
        assert dtype == DirectiveType.THERMODYNAMIC_GATE

    def test_classify_revenue_pipeline(self):
        """Revenue mentions should be pipeline."""
        dtype = self.agent.classify_directive(
            "$100k ACV opportunity in the sales pipeline", "gmail"
        )
        assert dtype == DirectiveType.REVENUE_PIPELINE


class TestPriorityCalculation:
    """Tests for priority calculation."""

    def setup_method(self):
        self.agent = EdgeAgent()

    def test_psf_compliance_high_priority(self):
        """PSF compliance directives should have high base priority."""
        directive = WorkspaceDirective(
            id="test_1",
            source="gmail",
            content="PSF deal registration",
            directive_type=DirectiveType.PSF_COMPLIANCE,
        )
        priority = self.agent.calculate_priority(directive)
        assert priority >= 9

    def test_arr_floor_boosts_priority(self):
        """$25k ARR floor mentions should boost to max priority."""
        directive = WorkspaceDirective(
            id="test_2",
            source="gmail",
            content="Verify $25k ARR floor requirement",
            directive_type=DirectiveType.PSF_COMPLIANCE,
        )
        priority = self.agent.calculate_priority(directive)
        assert priority == 10

    def test_urgent_keywords_boost_priority(self):
        """Urgent keywords should boost priority."""
        directive = WorkspaceDirective(
            id="test_3",
            source="tasks",
            content="URGENT: Deploy by deadline today",
            directive_type=DirectiveType.EXECUTION_QUEUE,
        )
        priority = self.agent.calculate_priority(directive)
        assert priority >= 8

    def test_thermodynamic_gate_low_priority(self):
        """Thermodynamic gate tasks should have low priority."""
        directive = WorkspaceDirective(
            id="test_4",
            source="keep",
            content="Mycology personal research",
            directive_type=DirectiveType.THERMODYNAMIC_GATE,
        )
        priority = self.agent.calculate_priority(directive)
        assert priority <= 5


class TestDirectiveToTelemetry:
    """Tests for telemetry conversion."""

    def test_directive_to_telemetry_attributes(self):
        """Directive should convert to OTel attributes correctly."""
        directive = WorkspaceDirective(
            id="test_1",
            source="keep",
            content="Test content",
            directive_type=DirectiveType.HIGH_LEVERAGE_PORTFOLIO,
            priority=8,
            processed=False,
        )

        attrs = directive.to_telemetry()

        assert attrs["directive.id"] == "test_1"
        assert attrs["directive.source"] == "keep"
        assert attrs["directive.type"] == "vector_1"
        assert attrs["directive.priority"] == 8
        assert attrs["directive.processed"] is False


class TestEdgeAgentPolling:
    """Tests for workspace polling."""

    @pytest.fixture
    def mock_workspace_client(self):
        """Create a mock workspace client."""
        client = AsyncMock()
        client.get_keep_notes = AsyncMock(return_value=[
            {
                "id": "note_1",
                "title": "Genesis Conductor Strategic Plan",
                "content": "Wolfspeed SiC integration",
                "labels": ["strategic"],
                "pinned": True,
            }
        ])
        client.get_tasks = AsyncMock(return_value=[
            {
                "id": "task_1",
                "title": "Launch OpenTelemetry API",
                "notes": "Deploy to staging",
                "status": "needsAction",
            }
        ])
        client.get_emails = AsyncMock(return_value=[
            {
                "id": "email_1",
                "subject": "PSF Deal Registration",
                "snippet": "$25k ARR floor verified",
                "from": "partner@google.com",
                "labels": ["psf"],
            }
        ])
        return client

    @pytest.mark.asyncio
    async def test_ingest_keep_notes(self, mock_workspace_client):
        """Test Keep notes ingestion."""
        agent = EdgeAgent(workspace_client=mock_workspace_client)
        directives = await agent.ingest_keep_notes()

        assert len(directives) == 1
        assert directives[0].source == "keep"
        assert directives[0].directive_type == DirectiveType.HIGH_LEVERAGE_PORTFOLIO

    @pytest.mark.asyncio
    async def test_ingest_tasks(self, mock_workspace_client):
        """Test Tasks ingestion."""
        agent = EdgeAgent(workspace_client=mock_workspace_client)
        directives = await agent.ingest_tasks()

        assert len(directives) == 1
        assert directives[0].source == "tasks"
        assert "opentelemetry" in directives[0].content.lower()

    @pytest.mark.asyncio
    async def test_poll_workspace_aggregates_sources(self, mock_workspace_client):
        """Test that poll_workspace aggregates all sources."""
        agent = EdgeAgent(workspace_client=mock_workspace_client)
        directives = await agent.poll_workspace()

        assert len(directives) == 3  # Keep + Tasks + Gmail
        sources = {d.source for d in directives}
        assert sources == {"keep", "tasks", "gmail"}

    @pytest.mark.asyncio
    async def test_poll_workspace_sorts_by_priority(self, mock_workspace_client):
        """Test that directives are sorted by priority descending."""
        agent = EdgeAgent(workspace_client=mock_workspace_client)
        directives = await agent.poll_workspace()

        priorities = [d.priority for d in directives]
        assert priorities == sorted(priorities, reverse=True)


class TestHandlerRegistration:
    """Tests for directive handler registration."""

    def test_register_handler(self):
        """Test handler registration."""
        agent = EdgeAgent()
        handler = MagicMock()

        agent.register_handler(DirectiveType.HIGH_LEVERAGE_PORTFOLIO, handler)

        assert handler in agent._handlers[DirectiveType.HIGH_LEVERAGE_PORTFOLIO]

    @pytest.mark.asyncio
    async def test_dispatch_calls_handlers(self):
        """Test that dispatch calls registered handlers."""
        agent = EdgeAgent()
        handler = MagicMock()
        agent.register_handler(DirectiveType.HIGH_LEVERAGE_PORTFOLIO, handler)

        directive = WorkspaceDirective(
            id="test_1",
            source="keep",
            content="Wolfspeed",
            directive_type=DirectiveType.HIGH_LEVERAGE_PORTFOLIO,
        )

        await agent.dispatch_directive(directive)

        handler.assert_called_once_with(directive)
        assert directive.processed is True


class TestParetoFilter:
    """Tests for pareto filter integration."""

    def test_passes_pareto_filter_accepts_compliant(self):
        """Compliant directives should pass filter."""
        agent = EdgeAgent()

        directive = WorkspaceDirective(
            id="test_1",
            source="gmail",
            content="Deal Registration with $50k ARR",
            directive_type=DirectiveType.PSF_COMPLIANCE,
        )

        assert agent._passes_pareto_filter(directive) is True

    def test_passes_pareto_filter_rejects_production_deployment(self):
        """Production Deployment terminology should fail filter."""
        agent = EdgeAgent()

        directive = WorkspaceDirective(
            id="test_2",
            source="gmail",
            content="Production Deployment scheduled",
            directive_type=DirectiveType.REVENUE_PIPELINE,
        )

        assert agent._passes_pareto_filter(directive) is False
