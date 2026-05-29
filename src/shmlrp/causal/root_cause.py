from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.ensemble import RandomForestClassifier


@dataclass
class RootCauseResult:
    top_features: list[str]
    importances: dict[str, float]


def analyze_root_causes(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    target_column: str = "target",
    top_k: int = 5,
    seed: int = 42,
) -> RootCauseResult:
    baseline = baseline_df.copy()
    current = current_df.copy()
    baseline["drift_label"] = 0
    current["drift_label"] = 1
    combined = pd.concat([baseline, current], axis=0, ignore_index=True)

    X = combined.drop(columns=[target_column, "drift_label"])
    y = combined["drift_label"]
    X_encoded = pd.get_dummies(X, drop_first=False)

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=seed,
        n_jobs=-1,
        class_weight="balanced",
    )
    model.fit(X_encoded, y)

    importances = dict(zip(X_encoded.columns, model.feature_importances_))
    top_features = sorted(importances, key=importances.get, reverse=True)[:top_k]
    return RootCauseResult(top_features=top_features, importances=importances)
