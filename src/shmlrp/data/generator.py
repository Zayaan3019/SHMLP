from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DatasetBundle:
    baseline: pd.DataFrame
    current: pd.DataFrame
    drift_map: dict[str, bool]


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _make_target(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    segment_effect = {"A": 0.1, "B": -0.1, "C": 0.2}
    channel_effect = {"web": 0.1, "mobile": 0.0, "api": -0.05}
    logit = (
        0.8 * df["feature_1"].to_numpy()
        - 0.5 * df["feature_2"].to_numpy()
        + 0.2 * df["feature_3"].to_numpy()
        + 0.3 * df["feature_4"].to_numpy()
    )
    logit += df["segment"].map(segment_effect).to_numpy()
    logit += df["channel"].map(channel_effect).to_numpy()
    logit += rng.normal(0.0, 0.3, size=len(df))
    prob = _sigmoid(logit)
    return rng.binomial(1, prob)


def generate_datasets(
    sample_size: int,
    drift_probability: float,
    seed: int,
) -> DatasetBundle:
    rng = np.random.default_rng(seed)

    baseline = pd.DataFrame(
        {
            "feature_1": rng.normal(0.0, 1.0, size=sample_size),
            "feature_2": rng.normal(1.0, 1.5, size=sample_size),
            "feature_3": rng.lognormal(0.0, 0.5, size=sample_size),
            "feature_4": rng.uniform(-1.0, 1.0, size=sample_size),
            "segment": rng.choice(["A", "B", "C"], p=[0.5, 0.3, 0.2], size=sample_size),
            "channel": rng.choice(["web", "mobile", "api"], p=[0.6, 0.3, 0.1], size=sample_size),
        }
    )

    drift_map: dict[str, bool] = {}

    def maybe_drift(flag: bool) -> bool:
        return flag and rng.random() < drift_probability

    drift_map["feature_1"] = maybe_drift(True)
    drift_map["feature_2"] = maybe_drift(True)
    drift_map["feature_3"] = maybe_drift(True)
    drift_map["feature_4"] = maybe_drift(True)
    drift_map["segment"] = maybe_drift(True)
    drift_map["channel"] = maybe_drift(True)

    current = pd.DataFrame(index=baseline.index)
    current["feature_1"] = (
        rng.normal(0.6, 1.2, size=sample_size)
        if drift_map["feature_1"]
        else rng.normal(0.0, 1.0, size=sample_size)
    )
    current["feature_2"] = (
        rng.normal(1.8, 1.6, size=sample_size)
        if drift_map["feature_2"]
        else rng.normal(1.0, 1.5, size=sample_size)
    )
    current["feature_3"] = (
        rng.lognormal(0.4, 0.6, size=sample_size)
        if drift_map["feature_3"]
        else rng.lognormal(0.0, 0.5, size=sample_size)
    )
    current["feature_4"] = (
        rng.uniform(-1.6, 1.2, size=sample_size)
        if drift_map["feature_4"]
        else rng.uniform(-1.0, 1.0, size=sample_size)
    )

    current["segment"] = rng.choice(
        ["A", "B", "C"],
        p=[0.3, 0.4, 0.3] if drift_map["segment"] else [0.5, 0.3, 0.2],
        size=sample_size,
    )
    current["channel"] = rng.choice(
        ["web", "mobile", "api"],
        p=[0.4, 0.4, 0.2] if drift_map["channel"] else [0.6, 0.3, 0.1],
        size=sample_size,
    )

    baseline["target"] = _make_target(baseline, rng)
    current["target"] = _make_target(current, rng)

    return DatasetBundle(baseline=baseline, current=current, drift_map=drift_map)
