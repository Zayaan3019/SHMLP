from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ColumnSpec:
    kind: str
    min_value: float | None = None
    max_value: float | None = None
    allow_nulls: bool = False
    categories: list[str] | None = None


@dataclass
class SchemaValidationResult:
    is_valid: bool
    issues: list[str] = field(default_factory=list)


@dataclass
class SchemaContract:
    columns: dict[str, ColumnSpec]
    target: str

    def validate(self, df: pd.DataFrame) -> SchemaValidationResult:
        issues: list[str] = []

        for column, spec in self.columns.items():
            if column not in df.columns:
                issues.append(f"Missing column: {column}")
                continue

            series = df[column]
            if not spec.allow_nulls and series.isna().any():
                issues.append(f"Nulls not allowed in column: {column}")

            if spec.kind == "numeric":
                if not pd.api.types.is_numeric_dtype(series):
                    issues.append(f"Expected numeric dtype for column: {column}")
                if spec.min_value is not None and series.min() < spec.min_value:
                    issues.append(f"Column {column} below min {spec.min_value}")
                if spec.max_value is not None and series.max() > spec.max_value:
                    issues.append(f"Column {column} above max {spec.max_value}")
            elif spec.kind == "categorical":
                is_categorical = isinstance(series.dtype, pd.CategoricalDtype)
                is_string = pd.api.types.is_string_dtype(series)
                if not pd.api.types.is_object_dtype(series) and not is_categorical and not is_string:
                    issues.append(f"Expected categorical dtype for column: {column}")
                if spec.categories is not None:
                    unexpected = set(series.dropna().unique()) - set(spec.categories)
                    if unexpected:
                        issues.append(f"Unexpected categories in {column}: {sorted(unexpected)}")
            else:
                issues.append(f"Unknown column kind for {column}: {spec.kind}")

        if self.target not in df.columns:
            issues.append(f"Missing target column: {self.target}")

        return SchemaValidationResult(is_valid=len(issues) == 0, issues=issues)


def default_schema() -> SchemaContract:
    return SchemaContract(
        columns={
            "feature_1": ColumnSpec(kind="numeric", min_value=-8.0, max_value=8.0),
            "feature_2": ColumnSpec(kind="numeric", min_value=-8.0, max_value=8.0),
            "feature_3": ColumnSpec(kind="numeric", min_value=0.0, max_value=20.0),
            "feature_4": ColumnSpec(kind="numeric", min_value=-4.0, max_value=4.0),
            "segment": ColumnSpec(kind="categorical", categories=["A", "B", "C"]),
            "channel": ColumnSpec(kind="categorical", categories=["web", "mobile", "api"]),
        },
        target="target",
    )
