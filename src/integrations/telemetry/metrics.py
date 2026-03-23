"""
OpenTelemetry Metrics for Neurohumogenistic Agent

Provides metric instruments for:
- Directive processing (count, latency, types)
- Thermodynamic state (power, efficiency, cold snap)
- FrugalGPT cascade (tier usage, cost, tokens)
- Pareto filter (compliance rate, pipeline value)
"""

from dataclasses import dataclass
from typing import Any, Optional

import structlog

from .otel_provider import get_meter

logger = structlog.get_logger(__name__)


@dataclass
class DirectiveMetrics:
    """
    Metrics for workspace directive processing.

    Tracks:
    - Directives processed by type
    - Processing latency
    - Queue depth
    """

    def __init__(self, meter: Optional[Any] = None):
        self.meter = meter or get_meter()

        if self.meter:
            # Counter for directives processed
            self.directives_processed = self.meter.create_counter(
                name="instinct.directives.processed",
                description="Number of workspace directives processed",
                unit="1",
            )

            # Histogram for processing latency
            self.processing_latency = self.meter.create_histogram(
                name="instinct.directives.latency",
                description="Directive processing latency",
                unit="ms",
            )

            # Gauge for queue depth
            self.queue_depth = self.meter.create_up_down_counter(
                name="instinct.directives.queue_depth",
                description="Current directive queue depth",
                unit="1",
            )

            logger.info("otel.directive_metrics_created")
        else:
            self.directives_processed = None
            self.processing_latency = None
            self.queue_depth = None

    def record_processed(
        self,
        directive_type: str,
        source: str,
        priority: int,
    ) -> None:
        """Record a processed directive."""
        if self.directives_processed:
            self.directives_processed.add(
                1,
                attributes={
                    "directive.type": directive_type,
                    "directive.source": source,
                    "directive.priority": str(priority),
                }
            )

    def record_latency(
        self,
        latency_ms: float,
        directive_type: str,
    ) -> None:
        """Record processing latency."""
        if self.processing_latency:
            self.processing_latency.record(
                latency_ms,
                attributes={"directive.type": directive_type}
            )

    def update_queue_depth(self, delta: int) -> None:
        """Update queue depth."""
        if self.queue_depth:
            self.queue_depth.add(delta)


@dataclass
class ThermodynamicMetrics:
    """
    Metrics for thermodynamic state.

    Tracks η_thermo efficiency for Diamond Vault UI:
    - Power consumption (watts)
    - Energy efficiency (η)
    - Cold snap state
    - Temperature
    """

    def __init__(self, meter: Optional[Any] = None):
        self.meter = meter or get_meter()

        if self.meter:
            # Gauge for current power
            self._power_callback_value = 0.0
            self.power_watts = self.meter.create_observable_gauge(
                name="instinct.thermodynamic.power_watts",
                description="Current power consumption",
                unit="W",
                callbacks=[self._power_callback],
            )

            # Gauge for efficiency
            self._efficiency_callback_value = 1.0
            self.efficiency_eta = self.meter.create_observable_gauge(
                name="instinct.thermodynamic.efficiency_eta",
                description="Thermodynamic efficiency (η_thermo)",
                unit="1",
                callbacks=[self._efficiency_callback],
            )

            # Counter for energy consumed
            self.energy_joules = self.meter.create_counter(
                name="instinct.thermodynamic.energy_joules",
                description="Cumulative energy consumption",
                unit="J",
            )

            # Gauge for cold snap state
            self._cold_snap_callback_value = 0
            self.cold_snap_active = self.meter.create_observable_gauge(
                name="instinct.thermodynamic.cold_snap",
                description="Cold snap recovery state (0=inactive, 1=active)",
                unit="1",
                callbacks=[self._cold_snap_callback],
            )

            # Gauge for temperature
            self._temperature_callback_value = 25.0
            self.temperature_celsius = self.meter.create_observable_gauge(
                name="instinct.thermodynamic.temperature_celsius",
                description="System temperature estimate",
                unit="Cel",
                callbacks=[self._temperature_callback],
            )

            logger.info("otel.thermodynamic_metrics_created")
        else:
            self.power_watts = None
            self.efficiency_eta = None
            self.energy_joules = None
            self.cold_snap_active = None
            self.temperature_celsius = None

    def _power_callback(self, options):
        """Callback for power gauge."""
        yield self._power_callback_value, {}

    def _efficiency_callback(self, options):
        """Callback for efficiency gauge."""
        yield self._efficiency_callback_value, {}

    def _cold_snap_callback(self, options):
        """Callback for cold snap gauge."""
        yield self._cold_snap_callback_value, {}

    def _temperature_callback(self, options):
        """Callback for temperature gauge."""
        yield self._temperature_callback_value, {}

    def update(
        self,
        power_watts: float,
        efficiency_eta: float,
        cold_snap: bool,
        temperature_celsius: float,
    ) -> None:
        """Update all thermodynamic metrics."""
        self._power_callback_value = power_watts
        self._efficiency_callback_value = efficiency_eta
        self._cold_snap_callback_value = 1 if cold_snap else 0
        self._temperature_callback_value = temperature_celsius

    def record_energy(self, joules: float, domain: str = "total") -> None:
        """Record energy consumption."""
        if self.energy_joules:
            self.energy_joules.add(joules, attributes={"domain": domain})


@dataclass
class CascadeMetrics:
    """
    Metrics for FrugalGPT cascade performance.

    Tracks:
    - Tier usage distribution
    - Token consumption
    - Cost per directive
    - Escalation rate
    - ROI tracking
    """

    def __init__(self, meter: Optional[Any] = None):
        self.meter = meter or get_meter()

        if self.meter:
            # Counter for requests by tier
            self.requests_by_tier = self.meter.create_counter(
                name="instinct.cascade.requests",
                description="Cascade requests by tier",
                unit="1",
            )

            # Counter for tokens
            self.tokens_used = self.meter.create_counter(
                name="instinct.cascade.tokens",
                description="Tokens consumed by cascade",
                unit="1",
            )

            # Histogram for cost
            self.cost_usd = self.meter.create_histogram(
                name="instinct.cascade.cost_usd",
                description="Cost per cascade request",
                unit="USD",
            )

            # Histogram for latency
            self.latency_ms = self.meter.create_histogram(
                name="instinct.cascade.latency_ms",
                description="Cascade request latency",
                unit="ms",
            )

            # Counter for escalations
            self.escalations = self.meter.create_counter(
                name="instinct.cascade.escalations",
                description="Tier escalation count",
                unit="1",
            )

            # Gauge for cumulative cost
            self._cumulative_cost = 0.0
            self.cumulative_cost_gauge = self.meter.create_observable_gauge(
                name="instinct.cascade.cumulative_cost_usd",
                description="Total cumulative cost",
                unit="USD",
                callbacks=[lambda _: [(self._cumulative_cost, {})]],
            )

            logger.info("otel.cascade_metrics_created")
        else:
            self.requests_by_tier = None
            self.tokens_used = None
            self.cost_usd = None
            self.latency_ms = None
            self.escalations = None

    def record_request(
        self,
        tier: int,
        tokens_input: int,
        tokens_output: int,
        cost: float,
        latency: float,
        escalated: bool,
        model: str,
    ) -> None:
        """Record a cascade request."""
        attrs = {"tier": str(tier), "model": model}

        if self.requests_by_tier:
            self.requests_by_tier.add(1, attributes=attrs)

        if self.tokens_used:
            self.tokens_used.add(tokens_input + tokens_output, attributes=attrs)

        if self.cost_usd:
            self.cost_usd.record(cost, attributes=attrs)
            self._cumulative_cost += cost

        if self.latency_ms:
            self.latency_ms.record(latency, attributes=attrs)

        if escalated and self.escalations:
            self.escalations.add(1, attributes={"from_tier": str(tier - 1)})


@dataclass
class ParetoMetrics:
    """
    Metrics for Pareto filter compliance.

    Tracks:
    - Compliance rate
    - Pipeline value
    - Violations by type
    - ROI achievement
    """

    def __init__(self, meter: Optional[Any] = None):
        self.meter = meter or get_meter()

        if self.meter:
            # Counter for evaluated opportunities
            self.opportunities_evaluated = self.meter.create_counter(
                name="instinct.pareto.evaluated",
                description="Opportunities evaluated",
                unit="1",
            )

            # Counter for compliant opportunities
            self.compliant = self.meter.create_counter(
                name="instinct.pareto.compliant",
                description="Compliant opportunities",
                unit="1",
            )

            # Counter for filtered opportunities
            self.filtered = self.meter.create_counter(
                name="instinct.pareto.filtered",
                description="Filtered (non-compliant) opportunities",
                unit="1",
            )

            # Counter for violations by type
            self.violations = self.meter.create_counter(
                name="instinct.pareto.violations",
                description="Violations by type",
                unit="1",
            )

            # Gauge for pipeline value
            self._pipeline_value = 0.0
            self.pipeline_value_usd = self.meter.create_observable_gauge(
                name="instinct.pareto.pipeline_value_usd",
                description="Estimated pipeline value",
                unit="USD",
                callbacks=[lambda _: [(self._pipeline_value, {})]],
            )

            logger.info("otel.pareto_metrics_created")
        else:
            self.opportunities_evaluated = None
            self.compliant = None
            self.filtered = None
            self.violations = None

    def record_evaluation(
        self,
        compliant: bool,
        violations: list[str],
        pipeline_value: float,
    ) -> None:
        """Record a pareto filter evaluation."""
        if self.opportunities_evaluated:
            self.opportunities_evaluated.add(1)

        if compliant:
            if self.compliant:
                self.compliant.add(1)
            self._pipeline_value += pipeline_value
        else:
            if self.filtered:
                self.filtered.add(1)
            if self.violations:
                for violation in violations:
                    # Categorize violations
                    violation_type = "other"
                    if "arr" in violation.lower():
                        violation_type = "arr_floor"
                    elif "acv" in violation.lower():
                        violation_type = "acv_range"
                    elif "deployment" in violation.lower():
                        violation_type = "terminology"
                    elif "roi" in violation.lower():
                        violation_type = "roi_target"

                    self.violations.add(1, attributes={"type": violation_type})
