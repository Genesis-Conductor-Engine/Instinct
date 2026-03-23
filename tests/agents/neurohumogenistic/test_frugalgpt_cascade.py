"""Tests for the FrugalGPT Cascade component."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.neurohumogenistic.frugalgpt_cascade import (
    CascadeConfig,
    CascadeResult,
    FrugalGPTCascade,
    ModelTier,
)
from src.agents.neurohumogenistic.edge_agent import (
    DirectiveType,
    WorkspaceDirective,
)


class TestCascadeConfig:
    """Tests for cascade configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CascadeConfig()

        assert config.tier_1_cost_per_1k == 0.00025
        assert config.tier_2_cost_per_1k == 0.003
        assert config.tier_3_cost_per_1k == 0.015
        assert config.escalation_confidence_threshold == 0.7
        assert config.max_joules_per_directive == 100.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = CascadeConfig(
            tier_1_cost_per_1k=0.0005,
            max_joules_per_directive=50.0,
        )

        assert config.tier_1_cost_per_1k == 0.0005
        assert config.max_joules_per_directive == 50.0


class TestModelTier:
    """Tests for model tier enum."""

    def test_tier_model_values(self):
        """Test model names are correct."""
        assert ModelTier.TIER_1_HAIKU.value == "claude-haiku-4-5-20251001"
        assert ModelTier.TIER_2_SONNET.value == "claude-sonnet-4-6"
        assert ModelTier.TIER_3_OPUS.value == "claude-opus-4-6"


class TestEnergyCalculation:
    """Tests for Landauer energy calculation."""

    def setup_method(self):
        self.cascade = FrugalGPTCascade()

    def test_energy_increases_with_tokens(self):
        """More tokens should mean more energy."""
        energy_100 = self.cascade.calculate_energy_cost(100, tier=1)
        energy_1000 = self.cascade.calculate_energy_cost(1000, tier=1)

        assert energy_1000 > energy_100

    def test_energy_increases_with_tier(self):
        """Higher tiers should use more energy."""
        energy_tier_1 = self.cascade.calculate_energy_cost(100, tier=1)
        energy_tier_3 = self.cascade.calculate_energy_cost(100, tier=3)

        assert energy_tier_3 > energy_tier_1

    def test_landauer_penalty_applied(self):
        """Landauer penalty factor should increase energy."""
        config = CascadeConfig(landauer_penalty_factor=0.5)
        cascade = FrugalGPTCascade(config=config)

        energy_with_penalty = cascade.calculate_energy_cost(100, tier=1)
        energy_without = self.cascade.calculate_energy_cost(100, tier=1)

        assert energy_with_penalty > energy_without


class TestCascadeProcessing:
    """Tests for cascade directive processing."""

    @pytest.fixture
    def mock_directive(self):
        """Create a mock directive."""
        return WorkspaceDirective(
            id="test_cascade_1",
            source="keep",
            content="Wolfspeed SiC integration strategy",
            directive_type=DirectiveType.HIGH_LEVERAGE_PORTFOLIO,
            priority=8,
        )

    @pytest.mark.asyncio
    async def test_process_returns_result(self, mock_directive):
        """Processing should return a CascadeResult."""
        cascade = FrugalGPTCascade()

        result = await cascade.process(mock_directive, tier=3)

        assert isinstance(result, CascadeResult)
        assert result.directive_id == "test_cascade_1"
        assert result.tier_used == 3
        assert result.model == "claude-opus-4-6"

    @pytest.mark.asyncio
    async def test_process_clamps_tier(self, mock_directive):
        """Tier should be clamped to valid range."""
        cascade = FrugalGPTCascade()

        result = await cascade.process(mock_directive, tier=5)
        assert result.tier_used == 3

        result = await cascade.process(mock_directive, tier=0)
        assert result.tier_used == 1

    @pytest.mark.asyncio
    async def test_process_tracks_cost(self, mock_directive):
        """Processing should track cumulative cost."""
        cascade = FrugalGPTCascade()

        initial_cost = cascade._total_cost_usd

        await cascade.process(mock_directive, tier=1)

        assert cascade._total_cost_usd > initial_cost

    @pytest.mark.asyncio
    async def test_process_tracks_tier_usage(self, mock_directive):
        """Processing should track tier usage."""
        cascade = FrugalGPTCascade()

        await cascade.process(mock_directive, tier=2)

        assert cascade._tier_usage[2] == 1

    @pytest.mark.asyncio
    async def test_mock_response_tier_1(self, mock_directive):
        """Tier 1 mock should return compliance JSON."""
        cascade = FrugalGPTCascade()

        result = await cascade.process(mock_directive, tier=1)

        assert "compliant" in result.response
        assert "confidence" in result.response

    @pytest.mark.asyncio
    async def test_mock_response_tier_3(self, mock_directive):
        """Tier 3 mock should return strategic analysis."""
        cascade = FrugalGPTCascade()

        result = await cascade.process(mock_directive, tier=3)

        assert "strategic_assessment" in result.response
        assert "recommendations" in result.response


class TestEscalationLogic:
    """Tests for tier escalation."""

    def setup_method(self):
        self.cascade = FrugalGPTCascade()

    def test_should_escalate_on_explicit_signal(self):
        """Response with 'escalate' should trigger escalation."""
        response = "This requires escalation to Tier 3 for strategic analysis."

        directive = WorkspaceDirective(
            id="test_1",
            source="keep",
            content="Test",
            directive_type=DirectiveType.EXECUTION_QUEUE,
        )

        assert self.cascade._should_escalate(response, directive) is True

    def test_should_escalate_on_low_confidence(self):
        """Low confidence in JSON should trigger escalation."""
        response = '{"compliant": true, "confidence": 0.5}'

        directive = WorkspaceDirective(
            id="test_2",
            source="keep",
            content="Test",
            directive_type=DirectiveType.EXECUTION_QUEUE,
        )

        assert self.cascade._should_escalate(response, directive) is True

    def test_should_not_escalate_on_high_confidence(self):
        """High confidence should not trigger escalation."""
        response = '{"compliant": true, "confidence": 0.9}'

        directive = WorkspaceDirective(
            id="test_3",
            source="keep",
            content="Simple task",
            directive_type=DirectiveType.EXECUTION_QUEUE,
        )

        assert self.cascade._should_escalate(response, directive) is False


class TestStatistics:
    """Tests for cascade statistics."""

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Statistics should include all tracking data."""
        cascade = FrugalGPTCascade()

        directive = WorkspaceDirective(
            id="test_stats",
            source="keep",
            content="Test content",
            directive_type=DirectiveType.EXECUTION_QUEUE,
        )

        await cascade.process(directive, tier=2)

        stats = cascade.get_statistics()

        assert "total_cost_usd" in stats
        assert "total_tokens" in stats
        assert "tier_usage" in stats
        assert stats["tier_usage"][2] == 1


class TestROIVerification:
    """Tests for ROI verification."""

    @pytest.mark.asyncio
    async def test_verify_roi_meets_target(self):
        """ROI should be verified against 10:1 target."""
        cascade = FrugalGPTCascade()

        # Process some directives to generate cost
        directive = WorkspaceDirective(
            id="test_roi",
            source="gmail",
            content="Pipeline opportunity",
            directive_type=DirectiveType.REVENUE_PIPELINE,
        )
        await cascade.process(directive, tier=1)

        # Verify ROI with simulated revenue
        result = cascade.verify_roi(revenue_generated_usd=1000.0)

        assert "roi_ratio" in result
        assert "meets_target" in result
        assert result["target"] == "10:1"

    def test_verify_roi_with_zero_cost(self):
        """Zero cost should return infinite ROI."""
        cascade = FrugalGPTCascade()

        result = cascade.verify_roi(revenue_generated_usd=1000.0)

        assert result["roi_ratio"] == float('inf')
        assert result["meets_target"] is True
