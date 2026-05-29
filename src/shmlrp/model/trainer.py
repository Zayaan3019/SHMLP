from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class TrainResult:
    model: Pipeline
    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]


def train_model(
    train_df: pd.DataFrame,
    target_column: str,
    seed: int,
) -> TrainResult:
    X = train_df.drop(columns=[target_column])
    y = train_df[target_column]

    numeric_features = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    categorical_features = [c for c in X.columns if c not in numeric_features]

    preprocess = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ],
        remainder="drop",
    )

    model = LogisticRegression(max_iter=500, random_state=seed)
    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocess),
            ("model", model),
        ]
    )
    pipeline.fit(X, y)

    return TrainResult(
        model=pipeline,
        feature_columns=list(X.columns),
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )
