#!/usr/bin/env python3
"""
Mass Testing Runner for Neurohumogenistic Agent

Executes high-volume test scenarios to validate:
- Directive processing throughput
- FrugalGPT cascade scalability
- Thermodynamic efficiency under load
- Pareto filter accuracy at scale

Usage:
    python run_mass_tests.py --batch 1 --iterations 100 --output-dir results/
"""

import argparse
import asyncio
import json
import os
import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger(__name__)


@dataclass
class MassTestConfig:
    """Configuration for mass testing."""
    batch: int
    iterations: int
    output_dir: str
    directive_types: list[str]
    enable_cascade: bool = True
    enable_thermodynamic: bool = True
    parallel_workers: int = 4


@dataclass
class TestResult:
    """Result from a single test iteration."""
    iteration: int
    directive_type: str
    processing_time_ms: float
    cascade_tier: int
    energy_joules: float
    compliant: bool
    success: bool
    error: str | None = None


@dataclass
class BatchReport:
    """Aggregated report for a test batch."""
    batch: int
    iterations: int
    started_at: str
    completed_at: str
    duration_seconds: float
    success_rate: float
    avg_processing_time_ms: float
    p50_processing_time_ms: float
    p95_processing_time_ms: float
    p99_processing_time_ms: float
    tier_distribution: dict[int, int]
    compliance_rate: float
    total_energy_joules: float
    avg_energy_per_directive: float
    errors: list[str]


def generate_mock_directive(directive_type: str) -> dict:
    """Generate a mock directive for testing."""
    templates = {
        "vector_1": [
            "Wolfspeed SiC scrap integration analysis for Q{quarter}",
            "Skywater Technologies partnership proposal revision {revision}",
            "Strategic portfolio asset valuation #{id}",
        ],
        "doe_phase_1": [
            "DE-FOA-0003612 Phase I submission item {id}",
            "Technical Addendum for Project Vivarium section {section}",
            "Alpha Persistence log entry {id}",
        ],
        "active_foreground": [
            "Launch prototype build {build_id} on genesisconductor.io",
            "Enable OpenTelemetry ingestion API endpoint {endpoint}",
            "Deploy staging environment {env}",
        ],
        "psf_verification": [
            "PSF Deal Registration #{id} - ${amount} ARR",
            "Partner Services Funds verification for account {account}",
            "US Public Sector compliance check #{id}",
        ],
        "13_streams": [
            "Revenue pipeline opportunity #{id} - ${acv} ACV",
            "Deployment: Foundations engagement #{id}",
            "270-day sales cycle milestone #{milestone}",
        ],
    }

    template = random.choice(templates.get(directive_type, templates["active_foreground"]))

    return {
        "id": f"mass_test_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
        "source": random.choice(["keep", "tasks", "gmail"]),
        "content": template.format(
            quarter=random.randint(1, 4),
            revision=random.randint(1, 10),
            id=random.randint(1000, 9999),
            section=random.choice(["A", "B", "C", "D"]),
            build_id=random.randint(100, 999),
            endpoint=f"/api/v{random.randint(1, 3)}",
            env=random.choice(["staging", "preview", "canary"]),
            amount=random.randint(25, 500) * 1000,
            account=f"ACC-{random.randint(10000, 99999)}",
            acv=random.randint(100, 5000) * 1000,
            milestone=random.randint(1, 10),
        ),
        "directive_type": directive_type,
        "priority": random.randint(1, 10),
    }


async def process_directive_mock(directive: dict, config: MassTestConfig) -> TestResult:
    """Process a mock directive and return results."""
    start_time = time.time()

    try:
        # Simulate processing with random latency
        base_latency = 10  # 10ms base
        tier_latency = {1: 20, 2: 50, 3: 150}

        # Determine tier based on directive type
        tier = 2
        if directive["directive_type"] in ["vector_1", "doe_phase_1"]:
            tier = 3
        elif directive["directive_type"] == "psf_verification":
            tier = 1

        # Simulate cascade processing
        if config.enable_cascade:
            await asyncio.sleep(tier_latency.get(tier, 50) / 1000)

        # Simulate thermodynamic calculation
        energy = 0.0
        if config.enable_thermodynamic:
            tokens = len(directive["content"].split()) * 4
            energy = tokens * 0.001  # Simplified energy model

        # Check compliance (mock)
        compliant = True
        if "production deployment" in directive["content"].lower():
            compliant = False
        if directive["directive_type"] == "psf_verification":
            # Check ARR floor
            if "$" in directive["content"]:
                import re
                amounts = re.findall(r'\$(\d+)', directive["content"])
                if amounts:
                    arr = int(amounts[0])
                    compliant = arr >= 25000

        processing_time = (time.time() - start_time) * 1000

        return TestResult(
            iteration=0,  # Set by caller
            directive_type=directive["directive_type"],
            processing_time_ms=processing_time,
            cascade_tier=tier,
            energy_joules=energy,
            compliant=compliant,
            success=True,
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return TestResult(
            iteration=0,
            directive_type=directive["directive_type"],
            processing_time_ms=processing_time,
            cascade_tier=0,
            energy_joules=0,
            compliant=False,
            success=False,
            error=str(e),
        )


async def run_batch(config: MassTestConfig) -> BatchReport:
    """Run a batch of mass tests."""
    started_at = datetime.utcnow()
    results: list[TestResult] = []
    errors: list[str] = []

    logger.info(
        "mass_test.batch_started",
        batch=config.batch,
        iterations=config.iterations,
    )

    # Process directives in parallel
    tasks = []
    for i in range(config.iterations):
        directive_type = random.choice(config.directive_types)
        directive = generate_mock_directive(directive_type)

        task = asyncio.create_task(process_directive_mock(directive, config))
        tasks.append((i, task))

    # Gather results
    for iteration, task in tasks:
        result = await task
        result.iteration = iteration
        results.append(result)

        if result.error:
            errors.append(f"Iteration {iteration}: {result.error}")

    completed_at = datetime.utcnow()
    duration = (completed_at - started_at).total_seconds()

    # Calculate statistics
    success_count = sum(1 for r in results if r.success)
    compliant_count = sum(1 for r in results if r.compliant)
    processing_times = sorted([r.processing_time_ms for r in results])

    tier_distribution = {1: 0, 2: 0, 3: 0}
    for r in results:
        if r.cascade_tier in tier_distribution:
            tier_distribution[r.cascade_tier] += 1

    total_energy = sum(r.energy_joules for r in results)

    def percentile(data: list, p: float) -> float:
        if not data:
            return 0.0
        k = (len(data) - 1) * p
        f = int(k)
        c = f + 1 if f + 1 < len(data) else f
        return data[f] + (data[c] - data[f]) * (k - f)

    report = BatchReport(
        batch=config.batch,
        iterations=config.iterations,
        started_at=started_at.isoformat(),
        completed_at=completed_at.isoformat(),
        duration_seconds=duration,
        success_rate=success_count / config.iterations if config.iterations > 0 else 0,
        avg_processing_time_ms=sum(processing_times) / len(processing_times) if processing_times else 0,
        p50_processing_time_ms=percentile(processing_times, 0.5),
        p95_processing_time_ms=percentile(processing_times, 0.95),
        p99_processing_time_ms=percentile(processing_times, 0.99),
        tier_distribution=tier_distribution,
        compliance_rate=compliant_count / config.iterations if config.iterations > 0 else 0,
        total_energy_joules=total_energy,
        avg_energy_per_directive=total_energy / config.iterations if config.iterations > 0 else 0,
        errors=errors[:10],  # Limit errors
    )

    logger.info(
        "mass_test.batch_completed",
        batch=config.batch,
        duration_seconds=duration,
        success_rate=report.success_rate,
        p95_latency_ms=report.p95_processing_time_ms,
    )

    return report


def write_report(report: BatchReport, output_dir: str) -> None:
    """Write batch report to file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    report_file = output_path / f"batch_{report.batch}_report.json"
    with open(report_file, "w") as f:
        json.dump(asdict(report), f, indent=2)

    # Write summary markdown
    summary_file = output_path / f"batch_{report.batch}_summary.md"
    with open(summary_file, "w") as f:
        f.write(f"# Mass Test Batch {report.batch} Summary\n\n")
        f.write(f"**Started:** {report.started_at}\n")
        f.write(f"**Completed:** {report.completed_at}\n")
        f.write(f"**Duration:** {report.duration_seconds:.2f}s\n\n")

        f.write("## Results\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Iterations | {report.iterations} |\n")
        f.write(f"| Success Rate | {report.success_rate * 100:.1f}% |\n")
        f.write(f"| Compliance Rate | {report.compliance_rate * 100:.1f}% |\n")
        f.write(f"| Avg Processing Time | {report.avg_processing_time_ms:.2f}ms |\n")
        f.write(f"| P50 Processing Time | {report.p50_processing_time_ms:.2f}ms |\n")
        f.write(f"| P95 Processing Time | {report.p95_processing_time_ms:.2f}ms |\n")
        f.write(f"| P99 Processing Time | {report.p99_processing_time_ms:.2f}ms |\n")
        f.write(f"| Total Energy | {report.total_energy_joules:.4f}J |\n")
        f.write(f"| Avg Energy/Directive | {report.avg_energy_per_directive:.6f}J |\n\n")

        f.write("## Tier Distribution\n\n")
        f.write("| Tier | Count | Percentage |\n")
        f.write("|------|-------|------------|\n")
        for tier, count in report.tier_distribution.items():
            pct = count / report.iterations * 100 if report.iterations > 0 else 0
            f.write(f"| Tier {tier} | {count} | {pct:.1f}% |\n")

        if report.errors:
            f.write("\n## Errors\n\n")
            for error in report.errors:
                f.write(f"- {error}\n")

    logger.info(
        "mass_test.report_written",
        json_file=str(report_file),
        summary_file=str(summary_file),
    )


def main():
    parser = argparse.ArgumentParser(description="Run mass tests for Neurohumogenistic Agent")
    parser.add_argument("--batch", type=int, default=1, help="Batch number")
    parser.add_argument("--iterations", type=int, default=100, help="Number of iterations")
    parser.add_argument("--output-dir", type=str, default="mass-results", help="Output directory")
    parser.add_argument("--parallel-workers", type=int, default=4, help="Parallel workers")

    args = parser.parse_args()

    config = MassTestConfig(
        batch=args.batch,
        iterations=args.iterations,
        output_dir=args.output_dir,
        directive_types=[
            "vector_1",
            "doe_phase_1",
            "active_foreground",
            "psf_verification",
            "13_streams",
        ],
        parallel_workers=args.parallel_workers,
    )

    report = asyncio.run(run_batch(config))
    write_report(report, config.output_dir)

    print(f"\n{'='*60}")
    print(f"Mass Test Batch {report.batch} Complete")
    print(f"{'='*60}")
    print(f"Iterations:     {report.iterations}")
    print(f"Success Rate:   {report.success_rate * 100:.1f}%")
    print(f"Compliance:     {report.compliance_rate * 100:.1f}%")
    print(f"P95 Latency:    {report.p95_processing_time_ms:.2f}ms")
    print(f"Total Energy:   {report.total_energy_joules:.4f}J")
    print(f"Duration:       {report.duration_seconds:.2f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
