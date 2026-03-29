"""
FrugalGPT Cascade for Neurohumogenistic Workspace Integration

Implements a tiered LLM processing architecture optimized for cost and capability:
- Tier 1 (Haiku): Fast, low-cost processing for compliance checks
- Tier 2 (Sonnet): Balanced processing for execution tasks
- Tier 3 (Opus): Strategic analysis for high-leverage portfolio items

Follows the Landauer-Context energy constraints from the Instinct platform.
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class ModelTier(Enum):
    """LLM tiers in the FrugalGPT cascade."""
    TIER_1_HAIKU = "claude-haiku-4-5-20251001"
    TIER_2_SONNET = "claude-sonnet-4-6"
    TIER_3_OPUS = "claude-opus-4-6"


@dataclass
class CascadeResult:
    """Result from FrugalGPT cascade processing."""
    directive_id: str
    tier_used: int
    model: str
    response: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    cost_estimate_usd: float
    escalated: bool = False
    escalation_reason: Optional[str] = None


@dataclass
class CascadeConfig:
    """Configuration for the FrugalGPT cascade."""
    # Cost per 1K tokens (approximate)
    tier_1_cost_per_1k: float = 0.00025
    tier_2_cost_per_1k: float = 0.003
    tier_3_cost_per_1k: float = 0.015

    # Confidence thresholds for escalation
    escalation_confidence_threshold: float = 0.7

    # Max retries per tier
    max_retries: int = 2

    # Energy budget (joules per directive, aligned with matter.yaml)
    max_joules_per_directive: float = 100.0

    # Landauer limit factor (thermodynamic penalty)
    landauer_penalty_factor: float = 0.1


class FrugalGPTCascade:
    """
    Cost-optimized LLM cascade following FrugalGPT principles.

    Architecture:
    - Starts at lowest cost tier capable of handling the task
    - Escalates to higher tiers on low confidence or complex tasks
    - Applies Landauer-Context energy penalties for thermodynamic efficiency
    - Tracks all costs for 10:1 ROI verification
    """

    def __init__(
        self,
        anthropic_client: Optional[Any] = None,
        config: Optional[CascadeConfig] = None,
    ):
        self.client = anthropic_client
        self.config = config or CascadeConfig()

        self._total_cost_usd: float = 0.0
        self._total_tokens: int = 0
        self._tier_usage: dict[int, int] = {1: 0, 2: 0, 3: 0}

        # Tier configurations
        self._tier_models = {
            1: ModelTier.TIER_1_HAIKU.value,
            2: ModelTier.TIER_2_SONNET.value,
            3: ModelTier.TIER_3_OPUS.value,
        }

        self._tier_costs = {
            1: self.config.tier_1_cost_per_1k,
            2: self.config.tier_2_cost_per_1k,
            3: self.config.tier_3_cost_per_1k,
        }

        # System prompts per tier
        self._tier_prompts = {
            1: self._get_tier_1_prompt(),
            2: self._get_tier_2_prompt(),
            3: self._get_tier_3_prompt(),
        }

        logger.info("frugalgpt.initialized", config=self.config.__dict__)

    def _get_tier_1_prompt(self) -> str:
        """Tier 1 (Haiku): Fast compliance and filtering."""
        return """You are a compliance verification agent for the Genesis Conductor platform.

Your role:
1. Validate PSF (Partner Services Funds) criteria
2. Check $25,000 Year 1 ARR floor requirement
3. Verify dual-staffing mandate (DRP Tier 1 + Technical Certification)
4. Flag non-compliant terminology (e.g., "Production Deployment" should be "Deployment: Foundations")

Respond with a JSON object:
{
    "compliant": boolean,
    "arr_verified": boolean,
    "staffing_verified": boolean,
    "issues": ["list of compliance issues"],
    "confidence": float (0-1)
}

If confidence < 0.7, indicate that escalation to Tier 2 is recommended."""

    def _get_tier_2_prompt(self) -> str:
        """Tier 2 (Sonnet): Execution and task processing."""
        return """You are an execution agent for the Genesis Conductor platform.

Your role:
1. Process execution queue directives (launches, API enablement, deployments)
2. Generate actionable implementation steps
3. Map tasks to OpenTelemetry metrics and thermodynamic efficiency targets
4. Coordinate with the Diamond Vault UI using useOptimistic patterns

For each directive, provide:
{
    "action_plan": ["ordered list of steps"],
    "telemetry_mappings": {"metric_name": "target_value"},
    "estimated_duration": "human readable time",
    "dependencies": ["list of prerequisites"],
    "confidence": float (0-1)
}

If the directive involves strategic portfolio decisions (Wolfspeed, Skywater, DOE proposals),
recommend escalation to Tier 3 (Opus) for strategic analysis."""

    def _get_tier_3_prompt(self) -> str:
        """Tier 3 (Opus): Strategic analysis and high-leverage decisions."""
        return """You are the strategic intelligence layer for the Genesis Conductor platform.

Your role is to analyze high-leverage portfolio assets and strategic decisions:

1. **Portfolio Analysis** (Vector 1):
   - Wolfspeed SiC scrap integration opportunities
   - Skywater Technologies partnership proposals
   - Strategic asset valuations and risk assessment

2. **DOE Mission Alignment** (DE-FOA-0003612):
   - Technical addendum generation for Project Vivarium
   - Alpha Persistence log structuring
   - Phase I application matrix optimization

3. **Revenue Pipeline Optimization**:
   - 13 revenue streams synthesis
   - $70k/mo target alignment
   - 270-day sales cycle optimization for $100K-$5M ACV targets

4. **Thermodynamic Arbitration**:
   - Apply Landauer-Context energy efficiency principles
   - Balance computational load with recovery ("Cold Snap") periods
   - Optimize for sustainable neurohumogenistic hybridization

Provide comprehensive strategic analysis with:
{
    "strategic_assessment": "detailed analysis",
    "recommendations": ["prioritized actions"],
    "risk_factors": ["identified risks"],
    "roi_projection": "10:1 ROI analysis",
    "thermodynamic_allocation": {"compute_percent": int, "recovery_percent": int},
    "confidence": float (0-1)
}"""

    def calculate_energy_cost(self, tokens: int, tier: int) -> float:
        """
        Calculate energy cost in joules using Landauer principle.
        Energy = k_B * T * ln(2) * bits, with tier multiplier.
        """
        # Approximate bits per token
        bits_per_token = 32
        total_bits = tokens * bits_per_token

        # Landauer limit at room temperature (300K)
        k_B = 1.380649e-23  # Boltzmann constant
        T = 300  # Kelvin
        landauer_min = k_B * T * 0.693  # ln(2)

        # Base energy with tier multiplier (higher tiers use more compute)
        tier_multipliers = {1: 1.0, 2: 3.0, 3: 10.0}
        energy_joules = total_bits * landauer_min * tier_multipliers.get(tier, 1.0) * 1e12

        # Apply penalty factor from config
        return energy_joules * (1 + self.config.landauer_penalty_factor)

    async def process(
        self,
        directive: Any,
        tier: int = 1,
        force_tier: bool = False,
    ) -> CascadeResult:
        """
        Process a directive through the FrugalGPT cascade.

        Args:
            directive: WorkspaceDirective to process
            tier: Starting tier (1, 2, or 3)
            force_tier: If True, don't escalate regardless of confidence

        Returns:
            CascadeResult with processing details
        """
        tier = max(1, min(3, tier))  # Clamp to valid range
        start_time = time.time()

        logger.info(
            "frugalgpt.processing",
            directive_id=directive.id,
            starting_tier=tier,
            directive_type=directive.directive_type.value
        )

        model = self._tier_models[tier]
        system_prompt = self._tier_prompts[tier]

        # Prepare the message
        user_message = f"""Process this workspace directive:

Source: {directive.source}
Type: {directive.directive_type.value}
Priority: {directive.priority}
Content: {directive.content}

Metadata: {directive.metadata}"""

        response_text = ""
        tokens_input = 0
        tokens_output = 0
        escalated = False
        escalation_reason = None

        if self.client:
            try:
                response = await self._call_model(model, system_prompt, user_message)
                response_text = response.get("content", "")
                tokens_input = response.get("input_tokens", 0)
                tokens_output = response.get("output_tokens", 0)

                # Check for escalation signal
                if not force_tier and tier < 3:
                    if self._should_escalate(response_text, directive):
                        escalated = True
                        escalation_reason = "Low confidence or strategic content detected"

                        # Recursive escalation
                        return await self.process(
                            directive,
                            tier=tier + 1,
                            force_tier=False
                        )

            except Exception as e:
                logger.error("frugalgpt.model_error", tier=tier, error=str(e))
                response_text = f"Error processing: {str(e)}"
        else:
            # Mock response for testing
            response_text = self._mock_response(directive, tier)
            tokens_input = len(directive.content.split()) * 2
            tokens_output = len(response_text.split()) * 2

        # Calculate costs
        total_tokens = tokens_input + tokens_output
        cost_usd = (total_tokens / 1000) * self._tier_costs[tier]
        energy_joules = self.calculate_energy_cost(total_tokens, tier)

        # Check energy budget
        if energy_joules > self.config.max_joules_per_directive:
            logger.warning(
                "frugalgpt.energy_budget_exceeded",
                directive_id=directive.id,
                energy_joules=energy_joules,
                budget=self.config.max_joules_per_directive
            )

        latency_ms = (time.time() - start_time) * 1000

        # Update tracking
        self._total_cost_usd += cost_usd
        self._total_tokens += total_tokens
        self._tier_usage[tier] += 1

        result = CascadeResult(
            directive_id=directive.id,
            tier_used=tier,
            model=model,
            response=response_text,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            cost_estimate_usd=cost_usd,
            escalated=escalated,
            escalation_reason=escalation_reason,
        )

        logger.info(
            "frugalgpt.processed",
            directive_id=directive.id,
            tier=tier,
            tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            escalated=escalated
        )

        return result

    async def _call_model(
        self,
        model: str,
        system_prompt: str,
        user_message: str
    ) -> dict:
        """Call the Anthropic API with the specified model."""
        if not self.client:
            return {"content": "", "input_tokens": 0, "output_tokens": 0}

        response = await self.client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        return {
            "content": response.content[0].text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

    def _should_escalate(self, response: str, directive: Any) -> bool:
        """Determine if the directive should be escalated to a higher tier."""
        # Check for explicit escalation signals
        escalation_signals = [
            "escalate", "tier 3", "opus", "strategic",
            "wolfspeed", "skywater", "doe", "high-leverage"
        ]

        response_lower = response.lower()
        if any(signal in response_lower for signal in escalation_signals):
            return True

        # Check for low confidence in JSON response
        if '"confidence":' in response:
            try:
                import json
                # Extract JSON from response
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(response[start:end])
                    confidence = data.get("confidence", 1.0)
                    if confidence < self.config.escalation_confidence_threshold:
                        return True
            except (json.JSONDecodeError, ValueError):
                pass

        return False

    def _mock_response(self, directive: Any, tier: int) -> str:
        """Generate mock response for testing without API."""
        from .edge_agent import DirectiveType

        if tier == 1:
            return """{
    "compliant": true,
    "arr_verified": true,
    "staffing_verified": true,
    "issues": [],
    "confidence": 0.85
}"""
        elif tier == 2:
            return f"""{{
    "action_plan": [
        "Review directive content: {directive.content[:50]}...",
        "Map to execution pipeline",
        "Configure OpenTelemetry metrics",
        "Deploy to staging environment"
    ],
    "telemetry_mappings": {{
        "directive_processing_time": "< 100ms",
        "success_rate": "> 0.95"
    }},
    "estimated_duration": "2-4 hours",
    "dependencies": ["API credentials", "Infrastructure access"],
    "confidence": 0.88
}}"""
        else:  # tier == 3
            return f"""{{
    "strategic_assessment": "High-leverage opportunity identified in {directive.directive_type.value}. This aligns with Genesis Conductor's 13 revenue streams strategy and the $70k/mo target.",
    "recommendations": [
        "Prioritize integration with existing portfolio",
        "Align with DOE Phase I application timeline",
        "Coordinate with Partner Advantage program"
    ],
    "risk_factors": [
        "Market timing dependency",
        "Resource allocation constraints"
    ],
    "roi_projection": "10:1 ROI achievable within 270-day sales cycle",
    "thermodynamic_allocation": {{"compute": 70, "recovery": 30}},
    "confidence": 0.92
}}"""

    def get_statistics(self) -> dict:
        """Get cascade usage statistics."""
        return {
            "total_cost_usd": self._total_cost_usd,
            "total_tokens": self._total_tokens,
            "tier_usage": self._tier_usage.copy(),
            "average_cost_per_directive": (
                self._total_cost_usd / sum(self._tier_usage.values())
                if sum(self._tier_usage.values()) > 0 else 0
            ),
        }

    def verify_roi(self, revenue_generated_usd: float) -> dict:
        """
        Verify 10:1 ROI target.

        Args:
            revenue_generated_usd: Total revenue attributed to cascade processing

        Returns:
            ROI verification result
        """
        roi_ratio = (
            revenue_generated_usd / self._total_cost_usd
            if self._total_cost_usd > 0 else float('inf')
        )

        return {
            "revenue_usd": revenue_generated_usd,
            "cost_usd": self._total_cost_usd,
            "roi_ratio": roi_ratio,
            "meets_target": roi_ratio >= 10.0,
            "target": "10:1",
        }
