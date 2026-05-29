from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class DriftResult:
    feature_scores: dict[str, float]
    drifted_features: list[str]
    global_score: float
    is_drifted: bool
    threshold: float
    details: dict[str, str] = field(default_factory=dict)


def _compute_bins(expected: np.ndarray, bins: int) -> np.ndarray:
    quantiles = np.quantile(expected, np.linspace(0, 1, bins + 1))
    edges = np.unique(quantiles)
    if len(edges) < 3:
        min_val = float(np.min(expected))
        max_val = float(np.max(expected))
        if min_val == max_val:
            max_val += 1.0
        edges = np.linspace(min_val, max_val, bins + 1)
    return edges


def _psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    edges = _compute_bins(expected, bins)
    expected_counts, _ = np.histogram(expected, bins=edges)
    actual_counts, _ = np.histogram(actual, bins=edges)

    expected_perc = expected_counts / max(expected_counts.sum(), 1)
    actual_perc = actual_counts / max(actual_counts.sum(), 1)

    eps = 1e-6
    psi_values = (actual_perc - expected_perc) * np.log((actual_perc + eps) / (expected_perc + eps))
    return float(np.sum(psi_values))


def _psi_categorical(expected: pd.Series, actual: pd.Series) -> float:
    categories = sorted(set(expected.dropna().unique()).union(set(actual.dropna().unique())))
    expected_counts = expected.value_counts(normalize=True).reindex(categories, fill_value=0.0)
    actual_counts = actual.value_counts(normalize=True).reindex(categories, fill_value=0.0)
    eps = 1e-6
    psi_values = (actual_counts - expected_counts) * np.log((actual_counts + eps) / (expected_counts + eps))
    return float(psi_values.sum())


def detect_drift(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    threshold: float,
    target_column: str = "target",
) -> DriftResult:
    feature_scores: dict[str, float] = {}

    for column in baseline_df.columns:
        if column == target_column:
            continue
        baseline_series = baseline_df[column]
        current_series = current_df[column]

        if pd.api.types.is_numeric_dtype(baseline_series):
            score = _psi(
                baseline_series.to_numpy(dtype=float),
                current_series.to_numpy(dtype=float),
            )
        else:
            score = _psi_categorical(baseline_series, current_series)
        feature_scores[column] = score

    drifted_features = [name for name, score in feature_scores.items() if score >= threshold]
    global_score = float(np.mean(list(feature_scores.values()))) if feature_scores else 0.0
    return DriftResult(
        feature_scores=feature_scores,
        drifted_features=drifted_features,
        global_score=global_score,
        is_drifted=len(drifted_features) > 0,
        threshold=threshold,
    )
