"""Minimal CLI entry point for ingest and analyze demos."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from .pipelines.arbiter_demo import run_demo

LOGGER = logging.getLogger("cve.cli")


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def _load_json(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ingest_command(args: argparse.Namespace) -> None:
    data_path = Path(args.input).expanduser().resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"Ingest source not found: {data_path}")

    records = _load_json(data_path)
    LOGGER.info("Loaded %s CVE records from %s", len(records), data_path)

    if args.preview:
        for record in records[: args.preview]:
            LOGGER.info(
                "CVE %s | CVSS %.1f | %s",
                record.get("cve_id", "UNKNOWN"),
                record.get("cvss", 0.0),
                record.get("summary", "(no summary)"),
            )


def analyze_command(args: argparse.Namespace) -> None:
    if args.mode != "arbiter-demo":
        raise ValueError(f"Unsupported analyze mode: {args.mode}")

    LOGGER.info("Running arbiter demo analysis (thermodynamic constraint mode)...")
    summary: Dict[str, Any] = run_demo()
    for case in summary["cases"]:
        LOGGER.info("Scenario: %s (penalty=%s)", case["label"], case["penalty"])
        for name, score in case["scores"]:
            LOGGER.info("  %s => %.4f", name, score)

    pareto: Dict[str, Any] = summary["pareto"]
    LOGGER.info("Pareto-efficient plans: %s", ", ".join(pareto["pareto_plans"]))
    if pareto.get("knee_plan"):
        LOGGER.info("Recommended knee plan: %s", pareto["knee_plan"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CVE Matter-Analysis CLI")
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest CVE JSON into the pipeline")
    ingest_parser.add_argument("input", help="Path to CVE JSON file (see samples/cve_demo.json)")
    ingest_parser.add_argument(
        "--preview",
        type=int,
        default=3,
        help="Number of entries to preview from the ingest file",
    )
    ingest_parser.set_defaults(func=ingest_command)

    analyze_parser = subparsers.add_parser("analyze", help="Run analysis workflows")
    analyze_parser.add_argument(
        "--mode",
        default="arbiter-demo",
        choices=["arbiter-demo"],
        help="Analysis mode to execute",
    )
    analyze_parser.set_defaults(func=analyze_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _configure_logging(args.log_level)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
