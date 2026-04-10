#!/usr/bin/env python3
"""
Generate comprehensive test reports from CI artifacts.

Aggregates:
- Unit test results (JUnit XML)
- Coverage reports
- Mass test batch results
- Integration test outcomes

Produces publishable documentation in HTML and Markdown.
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def find_artifacts(artifacts_dir: Path) -> dict[str, list[Path]]:
    """Find all artifact files by type."""
    artifacts = {
        "junit": [],
        "coverage": [],
        "mass_test": [],
    }

    for path in artifacts_dir.rglob("*"):
        if path.is_file():
            if path.suffix == ".xml" and "test" in path.stem.lower():
                artifacts["junit"].append(path)
            elif path.name == "coverage.xml":
                artifacts["coverage"].append(path)
            elif path.suffix == ".json" and "batch" in path.stem:
                artifacts["mass_test"].append(path)

    return artifacts


def parse_junit_results(junit_files: list[Path]) -> dict:
    """Parse JUnit XML results."""
    try:
        from junitparser import JUnitXml

        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        total_time = 0.0

        for junit_file in junit_files:
            xml = JUnitXml.fromfile(str(junit_file))
            for suite in xml:
                total_tests += suite.tests
                total_failures += suite.failures
                total_errors += suite.errors
                total_skipped += suite.skipped
                total_time += suite.time

        return {
            "total_tests": total_tests,
            "passed": total_tests - total_failures - total_errors - total_skipped,
            "failures": total_failures,
            "errors": total_errors,
            "skipped": total_skipped,
            "total_time_seconds": total_time,
        }
    except ImportError:
        return {"error": "junitparser not installed"}
    except Exception as e:
        return {"error": str(e)}


def parse_coverage(coverage_files: list[Path]) -> dict:
    """Parse coverage XML."""
    try:
        import xml.etree.ElementTree as ET

        for cov_file in coverage_files:
            tree = ET.parse(cov_file)
            root = tree.getroot()

            line_rate = float(root.attrib.get("line-rate", 0))
            branch_rate = float(root.attrib.get("branch-rate", 0))

            return {
                "line_coverage": line_rate * 100,
                "branch_coverage": branch_rate * 100,
            }

        return {"line_coverage": 0, "branch_coverage": 0}
    except Exception as e:
        return {"error": str(e)}


def parse_mass_tests(mass_test_files: list[Path]) -> dict:
    """Parse mass test batch results."""
    batches = []

    for batch_file in mass_test_files:
        try:
            with open(batch_file) as f:
                batch_data = json.load(f)
                batches.append(batch_data)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to parse mass test file {batch_file}: {e}")

    if not batches:
        return {"batches": []}

    # Aggregate statistics
    total_iterations = sum(b.get("iterations", 0) for b in batches)
    total_duration = sum(b.get("duration_seconds", 0) for b in batches)

    avg_success_rate = sum(b.get("success_rate", 0) for b in batches) / len(batches)
    avg_compliance_rate = sum(b.get("compliance_rate", 0) for b in batches) / len(batches)

    p95_latencies = [b.get("p95_processing_time_ms", 0) for b in batches]
    max_p95 = max(p95_latencies) if p95_latencies else 0

    total_energy = sum(b.get("total_energy_joules", 0) for b in batches)

    return {
        "batches": batches,
        "summary": {
            "total_iterations": total_iterations,
            "total_duration_seconds": total_duration,
            "avg_success_rate": avg_success_rate,
            "avg_compliance_rate": avg_compliance_rate,
            "max_p95_latency_ms": max_p95,
            "total_energy_joules": total_energy,
        },
    }


def generate_html_report(data: dict, output_dir: Path) -> None:
    """Generate HTML report."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neurohumogenistic Agent Test Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; border-bottom: 3px solid #4a90d9; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #4a90d9; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #1a1a1a; }}
        .metric-label {{ color: #666; font-size: 0.9em; }}
        .success {{ border-left-color: #28a745; }}
        .warning {{ border-left-color: #ffc107; }}
        .danger {{ border-left-color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Neurohumogenistic Agent Test Report</h1>
        <p><strong>Generated:</strong> {data['timestamp']}</p>

        <h2>Unit Test Results</h2>
        <div class="metric-grid">
            <div class="metric-card {'success' if data['unit_tests'].get('failures', 0) == 0 else 'danger'}">
                <div class="metric-value">{data['unit_tests'].get('passed', 0)}/{data['unit_tests'].get('total_tests', 0)}</div>
                <div class="metric-label">Tests Passed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{data['unit_tests'].get('total_time_seconds', 0):.2f}s</div>
                <div class="metric-label">Total Duration</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{data['coverage'].get('line_coverage', 0):.1f}%</div>
                <div class="metric-label">Line Coverage</div>
            </div>
        </div>

        <h2>Mass Test Results</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{data['mass_tests']['summary'].get('total_iterations', 0):,}</div>
                <div class="metric-label">Total Iterations</div>
            </div>
            <div class="metric-card {'success' if data['mass_tests']['summary'].get('avg_success_rate', 0) >= 0.95 else 'warning'}">
                <div class="metric-value">{data['mass_tests']['summary'].get('avg_success_rate', 0) * 100:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{data['mass_tests']['summary'].get('max_p95_latency_ms', 0):.1f}ms</div>
                <div class="metric-label">P95 Latency</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{data['mass_tests']['summary'].get('total_energy_joules', 0):.4f}J</div>
                <div class="metric-label">Total Energy</div>
            </div>
        </div>

        <h3>Batch Details</h3>
        <table>
            <thead>
                <tr>
                    <th>Batch</th>
                    <th>Iterations</th>
                    <th>Success Rate</th>
                    <th>Compliance</th>
                    <th>P95 Latency</th>
                    <th>Duration</th>
                </tr>
            </thead>
            <tbody>
"""

    for batch in data['mass_tests'].get('batches', []):
        success_rate = batch.get('success_rate', 0) * 100
        compliance = batch.get('compliance_rate', 0) * 100
        badge_class = 'success' if success_rate >= 95 else ('warning' if success_rate >= 80 else 'danger')

        html += f"""
                <tr>
                    <td>Batch {batch.get('batch', '?')}</td>
                    <td>{batch.get('iterations', 0):,}</td>
                    <td><span class="badge badge-{badge_class}">{success_rate:.1f}%</span></td>
                    <td>{compliance:.1f}%</td>
                    <td>{batch.get('p95_processing_time_ms', 0):.2f}ms</td>
                    <td>{batch.get('duration_seconds', 0):.2f}s</td>
                </tr>
"""

    html += """
            </tbody>
        </table>

        <footer>
            <p>Generated by Genesis Conductor CI Pipeline</p>
            <p>Neurohumogenistic Workspace Integration Agent v0.1.0</p>
        </footer>
    </div>
</body>
</html>
"""

    output_file = output_dir / "index.html"
    with open(output_file, "w") as f:
        f.write(html)

    print(f"HTML report written to: {output_file}")


def generate_markdown_report(data: dict, output_dir: Path) -> None:
    """Generate Markdown report."""
    md = f"""# Neurohumogenistic Agent Test Report

**Generated:** {data['timestamp']}

## Summary

| Category | Status |
|----------|--------|
| Unit Tests | {data['unit_tests'].get('passed', 0)}/{data['unit_tests'].get('total_tests', 0)} passed |
| Coverage | {data['coverage'].get('line_coverage', 0):.1f}% |
| Mass Tests | {data['mass_tests']['summary'].get('total_iterations', 0):,} iterations |
| Success Rate | {data['mass_tests']['summary'].get('avg_success_rate', 0) * 100:.1f}% |

## Unit Test Results

- **Total Tests:** {data['unit_tests'].get('total_tests', 0)}
- **Passed:** {data['unit_tests'].get('passed', 0)}
- **Failed:** {data['unit_tests'].get('failures', 0)}
- **Errors:** {data['unit_tests'].get('errors', 0)}
- **Skipped:** {data['unit_tests'].get('skipped', 0)}
- **Duration:** {data['unit_tests'].get('total_time_seconds', 0):.2f}s

## Coverage

- **Line Coverage:** {data['coverage'].get('line_coverage', 0):.1f}%
- **Branch Coverage:** {data['coverage'].get('branch_coverage', 0):.1f}%

## Mass Test Results

### Summary

| Metric | Value |
|--------|-------|
| Total Iterations | {data['mass_tests']['summary'].get('total_iterations', 0):,} |
| Average Success Rate | {data['mass_tests']['summary'].get('avg_success_rate', 0) * 100:.1f}% |
| Average Compliance Rate | {data['mass_tests']['summary'].get('avg_compliance_rate', 0) * 100:.1f}% |
| Max P95 Latency | {data['mass_tests']['summary'].get('max_p95_latency_ms', 0):.2f}ms |
| Total Energy | {data['mass_tests']['summary'].get('total_energy_joules', 0):.4f}J |
| Total Duration | {data['mass_tests']['summary'].get('total_duration_seconds', 0):.2f}s |

### Batch Details

| Batch | Iterations | Success Rate | Compliance | P95 Latency | Duration |
|-------|------------|--------------|------------|-------------|----------|
"""

    for batch in data['mass_tests'].get('batches', []):
        md += f"| {batch.get('batch', '?')} | {batch.get('iterations', 0):,} | {batch.get('success_rate', 0) * 100:.1f}% | {batch.get('compliance_rate', 0) * 100:.1f}% | {batch.get('p95_processing_time_ms', 0):.2f}ms | {batch.get('duration_seconds', 0):.2f}s |\n"

    md += """
---

*Generated by Genesis Conductor CI Pipeline*
"""

    output_file = output_dir / "REPORT.md"
    with open(output_file, "w") as f:
        f.write(md)

    print(f"Markdown report written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate test reports from CI artifacts")
    parser.add_argument("--artifacts-dir", type=str, required=True, help="Directory containing artifacts")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory for reports")

    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find and parse artifacts
    artifacts = find_artifacts(artifacts_dir)

    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "unit_tests": parse_junit_results(artifacts["junit"]),
        "coverage": parse_coverage(artifacts["coverage"]),
        "mass_tests": parse_mass_tests(artifacts["mass_test"]),
    }

    # Ensure mass_tests has summary
    if "summary" not in data["mass_tests"]:
        data["mass_tests"]["summary"] = {
            "total_iterations": 0,
            "total_duration_seconds": 0,
            "avg_success_rate": 0,
            "avg_compliance_rate": 0,
            "max_p95_latency_ms": 0,
            "total_energy_joules": 0,
        }

    # Write JSON data
    with open(output_dir / "report.json", "w") as f:
        json.dump(data, f, indent=2)

    # Generate reports
    generate_html_report(data, output_dir)
    generate_markdown_report(data, output_dir)

    print(f"\nReports generated in: {output_dir}")


if __name__ == "__main__":
    main()
