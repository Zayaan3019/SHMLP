from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CanaryResult:
    approved: bool
    reason: str
    metrics_delta: dict[str, float]


def decide_canary(
    baseline_metrics: dict[str, float],
    candidate_metrics: dict[str, float],
    min_improvement: float,
    max_brier_increase: float = 0.02,
) -> CanaryResult:
    accuracy_delta = candidate_metrics.get("accuracy", 0.0) - baseline_metrics.get("accuracy", 0.0)
    brier_delta = candidate_metrics.get("brier", 0.0) - baseline_metrics.get("brier", 0.0)

    if accuracy_delta < min_improvement:
        return CanaryResult(
            approved=False,
            reason="Accuracy improvement below threshold",
            metrics_delta={"accuracy": accuracy_delta, "brier": brier_delta},
        )

    if brier_delta > max_brier_increase:
        return CanaryResult(
            approved=False,
            reason="Calibration regression beyond limit",
            metrics_delta={"accuracy": accuracy_delta, "brier": brier_delta},
        )

    return CanaryResult(
        approved=True,
        reason="Candidate meets canary thresholds",
        metrics_delta={"accuracy": accuracy_delta, "brier": brier_delta},
    )
