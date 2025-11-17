"""Reusable arbiter demo helpers for CLI and scripts."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from ..models.arbiter import TensorPowerArbiter
from ..models.pareto import get_pareto_solutions

PlanNames = List[str]
MetricNames = List[str]
SegmentNames = List[str]


def create_mock_tensor() -> Tuple[np.ndarray, PlanNames, MetricNames, SegmentNames]:
    """Builds the mock tensor used in Task 030 demonstrations."""
    plan_names = [
        "P0: Balanced",
        "P1: High-Rev/High-Energy",
        "P2: Low-Energy/Low-Rev",
        "P3: High-Safety/Low-Rev",
    ]
    metric_names = ["revenue", "energy_J", "safety", "latency"]
    segment_names = ["Enterprise", "Free Tier"]

    num_p, num_m, num_s = len(plan_names), len(metric_names), len(segment_names)
    tensor = np.zeros((num_p, num_m, num_s))

    # Enterprise segment scores
    tensor[0, :, 0] = [0.7, 0.7, 0.7, 0.7]
    tensor[1, :, 0] = [1.0, 0.1, 0.5, 0.5]
    tensor[2, :, 0] = [0.2, 1.0, 0.8, 0.8]
    tensor[3, :, 0] = [0.3, 0.8, 1.0, 0.6]

    # Free tier segment scores
    tensor[0, :, 1] = [0.6, 0.7, 0.7, 0.7]
    tensor[1, :, 1] = [0.8, 0.1, 0.5, 0.2]
    tensor[2, :, 1] = [0.1, 1.0, 0.8, 1.0]
    tensor[3, :, 1] = [0.2, 0.8, 1.0, 0.8]

    # Inject Black-Box Substrate override with "real" value
    tensor[2, 1, 0] = 0.9

    return tensor, plan_names, metric_names, segment_names


def _format_rankings(plan_names: PlanNames, scores: np.ndarray) -> List[Tuple[str, float]]:
    """Returns plan rankings sorted from highest score to lowest."""

    return sorted(zip(plan_names, scores), key=lambda entry: entry[1], reverse=True)


def run_pareto_demo(tensor: np.ndarray, plan_names: PlanNames) -> Dict[str, Any]:
    """Calculates Pareto efficient plans and returns a printable summary."""
    costs = np.zeros((tensor.shape[0], 2))
    costs[:, 0] = 1.0 - tensor[:, 0, 0]
    costs[:, 1] = 1.0 - tensor[:, 1, 0]
    pareto_indices, knee_index = get_pareto_solutions(costs)
    return {
        "pareto_plans": [plan_names[idx] for idx in pareto_indices],
        "knee_plan": plan_names[knee_index] if knee_index >= 0 else None,
    }


def run_demo(iterations: int = 10, energy_penalty: float = 5.0) -> Dict[str, Any]:
    """Executes both arbitration scenarios and Pareto analysis."""
    tensor, plan_names, metric_names, _ = create_mock_tensor()
    energy_metric_index = metric_names.index("energy_J")

    metric_weights = {0: 1.0, 2: 0.5}
    segment_weights = {0: 1.0}

    def _run_case(label: str, penalty: float) -> Dict[str, object]:
        arbiter = TensorPowerArbiter(tensor, metric_weights, segment_weights)
        scores = arbiter.run_arbitration(
            iterations=iterations,
            energy_metric_index=energy_metric_index,
            energy_penalty=penalty,
        )
        return {
            "label": label,
            "penalty": penalty,
            "scores": _format_rankings(plan_names, scores),
        }

    no_penalty_case = _run_case("no_penalty", penalty=0.0)
    penalty_case = _run_case("energy_penalty", penalty=energy_penalty)
    pareto_summary = run_pareto_demo(tensor, plan_names)

    return {
        "plan_names": plan_names,
        "cases": [no_penalty_case, penalty_case],
        "pareto": pareto_summary,
    }
