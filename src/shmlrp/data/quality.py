from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from shmlrp.data.schema import SchemaContract


@dataclass
class QualityReport:
    missing_rate: float
    duplicate_rate: float
    outlier_rate: float
    issues: list[str] = field(default_factory=list)
    is_acceptable: bool = True


def run_quality_checks(
    df: pd.DataFrame,
    schema: SchemaContract,
    max_missing_rate: float,
) -> QualityReport:
    total_cells = df.shape[0] * df.shape[1]
    missing_rate = float(df.isna().sum().sum()) / max(total_cells, 1)

    duplicate_rate = float(df.duplicated().sum()) / max(len(df), 1)

    numeric_cols = [c for c, s in schema.columns.items() if s.kind == "numeric"]
    outlier_count = 0
    for col in numeric_cols:
        series = df[col].to_numpy(dtype=float)
        if series.size == 0:
            continue
        mean = np.mean(series)
        std = np.std(series) or 1.0
        z_scores = np.abs((series - mean) / std)
        outlier_count += int((z_scores > 4.0).sum())

    outlier_rate = float(outlier_count) / max(len(df), 1)
    issues: list[str] = []

    if missing_rate > max_missing_rate:
        issues.append(f"Missing rate too high: {missing_rate:.4f}")
    if duplicate_rate > 0.01:
        issues.append(f"Duplicate rate too high: {duplicate_rate:.4f}")
    if outlier_rate > 0.05:
        issues.append(f"Outlier rate too high: {outlier_rate:.4f}")

    return QualityReport(
        missing_rate=missing_rate,
        duplicate_rate=duplicate_rate,
        outlier_rate=outlier_rate,
        issues=issues,
        is_acceptable=len(issues) == 0,
    )
