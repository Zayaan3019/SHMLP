from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, f1_score, roc_auc_score


def evaluate_model(model, eval_df: pd.DataFrame, target_column: str) -> dict[str, float]:
    X = eval_df.drop(columns=[target_column])
    y_true = eval_df[target_column]

    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= 0.5).astype(int)

    metrics: dict[str, float] = {}
    metrics["accuracy"] = float(accuracy_score(y_true, preds))
    metrics["f1"] = float(f1_score(y_true, preds))
    metrics["brier"] = float(brier_score_loss(y_true, probs))

    if len(np.unique(y_true)) > 1:
        metrics["auc"] = float(roc_auc_score(y_true, probs))
    else:
        metrics["auc"] = 0.0

    return metrics
