"""
OpenTelemetry Provider Configuration

Configures exporters for the Diamond Vault UI with useOptimistic rendering.
Supports OTLP export to Grafana Cloud, Honeycomb, or local collectors.
"""

import os
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

# Global instances
_tracer_provider = None
_meter_provider = None
_tracer = None
_meter = None


def create_tracer_provider(
    service_name: str = "neurohumogenistic-agent",
    otlp_endpoint: Optional[str] = None,
) -> Optional["TracerProvider"]:
    """
    Create and configure OpenTelemetry tracer provider.

    Args:
        service_name: Name of the service for trace identification
        otlp_endpoint: OTLP exporter endpoint (default: env OTEL_EXPORTER_OTLP_ENDPOINT)

    Returns:
        Configured TracerProvider or None if dependencies missing
    """
    global _tracer_provider

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource

        # Get endpoint from env or parameter
        endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

        # Create resource with service info
        resource = Resource.create({
            "service.name": service_name,
            "service.namespace": "genesis-conductor",
            "service.version": "0.1.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })

        # Create provider
        _tracer_provider = TracerProvider(resource=resource)

        # Add exporters
        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
                _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info("otel.otlp_exporter_configured", endpoint=endpoint)
            except ImportError:
                logger.warning("otel.otlp_exporter_not_available")

        # Always add console exporter for development
        if os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
            _tracer_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

        # Set as global provider
        trace.set_tracer_provider(_tracer_provider)

        logger.info("otel.tracer_provider_created", service_name=service_name)
        return _tracer_provider

    except ImportError:
        logger.warning(
            "otel.not_installed",
            hint="pip install opentelemetry-sdk opentelemetry-exporter-otlp"
        )
        return None


def create_meter_provider(
    service_name: str = "neurohumogenistic-agent",
    otlp_endpoint: Optional[str] = None,
    export_interval_ms: int = 60000,
) -> Optional["MeterProvider"]:
    """
    Create and configure OpenTelemetry meter provider.

    Exports thermodynamic metrics (η_thermo) for Diamond Vault UI.

    Args:
        service_name: Name of the service for metric identification
        otlp_endpoint: OTLP exporter endpoint
        export_interval_ms: Metric export interval in milliseconds

    Returns:
        Configured MeterProvider or None if dependencies missing
    """
    global _meter_provider

    try:
        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import (
            ConsoleMetricExporter,
            PeriodicExportingMetricReader,
        )
        from opentelemetry.sdk.resources import Resource

        endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

        resource = Resource.create({
            "service.name": service_name,
            "service.namespace": "genesis-conductor",
        })

        readers = []

        # OTLP exporter
        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                    OTLPMetricExporter,
                )
                otlp_exporter = OTLPMetricExporter(endpoint=endpoint)
                readers.append(PeriodicExportingMetricReader(
                    otlp_exporter,
                    export_interval_millis=export_interval_ms
                ))
                logger.info("otel.otlp_metric_exporter_configured", endpoint=endpoint)
            except ImportError:
                logger.warning("otel.otlp_metric_exporter_not_available")

        # Console exporter for development
        if os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
            readers.append(PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=export_interval_ms
            ))

        _meter_provider = MeterProvider(resource=resource, metric_readers=readers)
        metrics.set_meter_provider(_meter_provider)

        logger.info("otel.meter_provider_created", service_name=service_name)
        return _meter_provider

    except ImportError:
        logger.warning(
            "otel.not_installed",
            hint="pip install opentelemetry-sdk opentelemetry-exporter-otlp"
        )
        return None


def get_tracer(name: str = "neurohumogenistic") -> Optional["Tracer"]:
    """Get or create a tracer instance."""
    global _tracer

    try:
        from opentelemetry import trace

        if _tracer is None:
            if _tracer_provider is None:
                create_tracer_provider()
            _tracer = trace.get_tracer(name, version="0.1.0")

        return _tracer

    except ImportError:
        return None


def get_meter(name: str = "neurohumogenistic") -> Optional["Meter"]:
    """Get or create a meter instance."""
    global _meter

    try:
        from opentelemetry import metrics

        if _meter is None:
            if _meter_provider is None:
                create_meter_provider()
            _meter = metrics.get_meter(name, version="0.1.0")

        return _meter

    except ImportError:
        return None
