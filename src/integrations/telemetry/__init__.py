"""
OpenTelemetry Integration for Neurohumogenistic Agent

Provides observability for:
- Directive processing traces
- Thermodynamic metrics (η_thermo)
- FrugalGPT cascade performance
- Pareto filter compliance rates
"""

from .otel_provider import (
    create_tracer_provider,
    create_meter_provider,
    get_tracer,
    get_meter,
)
from .metrics import (
    DirectiveMetrics,
    ThermodynamicMetrics,
    CascadeMetrics,
)

__all__ = [
    "create_tracer_provider",
    "create_meter_provider",
    "get_tracer",
    "get_meter",
    "DirectiveMetrics",
    "ThermodynamicMetrics",
    "CascadeMetrics",
]
