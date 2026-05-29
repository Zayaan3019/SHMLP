from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

import pandas as pd
from sklearn.model_selection import train_test_split

from shmlrp.causal.root_cause import RootCauseResult, analyze_root_causes
from shmlrp.config import AppConfig
from shmlrp.data.generator import DatasetBundle, generate_datasets
from shmlrp.data.lineage import LineageTracker
from shmlrp.data.quality import QualityReport, run_quality_checks
from shmlrp.data.schema import SchemaValidationResult, default_schema
from shmlrp.drift.detector import DriftResult, detect_drift
from shmlrp.incident.manager import IncidentManager
from shmlrp.model.evaluator import evaluate_model
from shmlrp.model.registry import ModelRegistry
from shmlrp.model.trainer import TrainResult, train_model
from shmlrp.monitoring.metrics import MetricsStore
from shmlrp.rollout.canary import CanaryResult, decide_canary
from shmlrp.utils import ensure_dir, utc_now_iso


def _serialize_path(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def run_pipeline(
    config: AppConfig,
    drift_probability: float | None = None,
    sample_size: int | None = None,
    seed: int | None = None,
) -> dict:
    logger = logging.getLogger("shmlrp.pipeline")
    run_id = f"run_{uuid4().hex[:10]}"
    started_at = utc_now_iso()

    drift_probability = drift_probability if drift_probability is not None else config.drift_probability
    sample_size = sample_size if sample_size is not None else config.sample_size
    seed = seed if seed is not None else config.random_seed

    run_dir = ensure_dir(config.artifacts_dir / "runs" / run_id)
    data_dir = ensure_dir(run_dir / "data")
    report_dir = ensure_dir(run_dir / "reports")

    metrics_store = MetricsStore(config.artifacts_dir / "metrics.jsonl")
    incident_manager = IncidentManager(config.artifacts_dir / "incidents.jsonl")
    lineage_tracker = LineageTracker(config.artifacts_dir / "lineage.jsonl")
    registry = ModelRegistry(run_dir)

    logger.info("Generating datasets")
    dataset_bundle: DatasetBundle = generate_datasets(sample_size, drift_probability, seed)
    baseline_df = dataset_bundle.baseline
    current_df = dataset_bundle.current

    baseline_path = data_dir / "baseline.csv"
    current_path = data_dir / "current.csv"
    baseline_df.to_csv(baseline_path, index=False)
    current_df.to_csv(current_path, index=False)

    lineage_tracker.record_step(
        run_id=run_id,
        step_name="data_generation",
        inputs={"seed": str(seed)},
        outputs={"baseline": str(baseline_path), "current": str(current_path)},
        metadata={"drift_probability": f"{drift_probability:.3f}"},
    )

    schema = default_schema()
    schema_result_baseline: SchemaValidationResult = schema.validate(baseline_df)
    schema_result_current: SchemaValidationResult = schema.validate(current_df)

    if not schema_result_baseline.is_valid or not schema_result_current.is_valid:
        issues = schema_result_baseline.issues + schema_result_current.issues
        incident_manager.create_incident(
            severity="high",
            title="Schema contract violation",
            details={"issues": issues},
            tags=["schema", "blocking"],
        )
        report = {
            "run_id": run_id,
            "status": "failed",
            "timestamps": {"started_at": started_at, "ended_at": utc_now_iso()},
            "schema": {"baseline": asdict(schema_result_baseline), "current": asdict(schema_result_current)},
        }
        _write_json(report_dir / "pipeline_report.json", report)
        return report

    quality_report: QualityReport = run_quality_checks(
        baseline_df, schema, max_missing_rate=config.max_missing_rate
    )

    drift_result: DriftResult = detect_drift(
        baseline_df,
        current_df,
        threshold=config.drift_threshold,
    )

    root_cause_result: RootCauseResult | None = None
    if drift_result.is_drifted:
        root_cause_result = analyze_root_causes(
            baseline_df,
            current_df,
            top_k=5,
            seed=seed,
        )
        incident_manager.create_incident(
            severity="medium",
            title="Data drift detected",
            details={"drifted_features": drift_result.drifted_features},
            tags=["drift"],
        )

    if not quality_report.is_acceptable:
        incident_manager.create_incident(
            severity="high",
            title="Data quality gate failed",
            details={"issues": quality_report.issues},
            tags=["quality", "blocking"],
        )

    baseline_train, baseline_eval = train_test_split(
        baseline_df,
        test_size=0.2,
        random_state=seed,
        stratify=baseline_df[schema.target],
    )
    current_train, current_eval = train_test_split(
        current_df,
        test_size=0.2,
        random_state=seed,
        stratify=current_df[schema.target],
    )

    logger.info("Training baseline model")
    baseline_train_result: TrainResult = train_model(
        baseline_train,
        target_column=schema.target,
        seed=seed,
    )
    baseline_metrics = evaluate_model(
        baseline_train_result.model,
        baseline_eval,
        target_column=schema.target,
    )
    baseline_on_current = evaluate_model(
        baseline_train_result.model,
        current_eval,
        target_column=schema.target,
    )

    baseline_artifacts = registry.save(
        baseline_train_result.model,
        metadata={"role": "baseline", "metrics": baseline_metrics},
        model_name="baseline_model",
    )

    retrain_needed = drift_result.is_drifted or not quality_report.is_acceptable
    performance_drop = baseline_metrics["accuracy"] - baseline_on_current["accuracy"]
    if performance_drop > config.performance_drop_threshold:
        retrain_needed = True
        incident_manager.create_incident(
            severity="medium",
            title="Performance regression detected",
            details={"accuracy_drop": performance_drop},
            tags=["performance"],
        )

    candidate_metrics: dict[str, float] | None = None
    canary_result: CanaryResult | None = None
    candidate_artifacts = None
    promoted = False

    if retrain_needed:
        logger.info("Retraining candidate model")
        candidate_train_result = train_model(
            current_train,
            target_column=schema.target,
            seed=seed,
        )
        candidate_metrics = evaluate_model(
            candidate_train_result.model,
            current_eval,
            target_column=schema.target,
        )
        canary_result = decide_canary(
            baseline_metrics=baseline_on_current,
            candidate_metrics=candidate_metrics,
            min_improvement=config.canary_min_improvement,
        )

        candidate_artifacts = registry.save(
            candidate_train_result.model,
            metadata={"role": "candidate", "metrics": candidate_metrics},
            model_name="candidate_model",
        )

        if canary_result.approved:
            promoted = True
        else:
            incident_manager.create_incident(
                severity="medium",
                title="Canary rollout rejected",
                details={"reason": canary_result.reason, "delta": canary_result.metrics_delta},
                tags=["canary"],
            )

    metrics_store.record(
        run_id=run_id,
        payload={
            "baseline": baseline_metrics,
            "baseline_on_current": baseline_on_current,
            "candidate": candidate_metrics,
            "drift": asdict(drift_result),
        },
        tags=["pipeline"],
    )

    lineage_tracker.record_step(
        run_id=run_id,
        step_name="model_training",
        inputs={"baseline": str(baseline_path), "current": str(current_path)},
        outputs={
            "baseline_model": str(baseline_artifacts.model_path),
            "candidate_model": str(candidate_artifacts.model_path) if candidate_artifacts else "",
        },
        metadata={"promoted": str(promoted)},
    )

    report = {
        "run_id": run_id,
        "status": "completed",
        "timestamps": {"started_at": started_at, "ended_at": utc_now_iso()},
        "config": {
            "sample_size": sample_size,
            "drift_probability": drift_probability,
            "seed": seed,
        },
        "data": {
            "baseline_path": _serialize_path(baseline_path),
            "current_path": _serialize_path(current_path),
            "drift_map": dataset_bundle.drift_map,
        },
        "schema": {
            "baseline": asdict(schema_result_baseline),
            "current": asdict(schema_result_current),
        },
        "quality": asdict(quality_report),
        "drift": asdict(drift_result),
        "root_cause": asdict(root_cause_result) if root_cause_result else None,
        "performance": {
            "baseline": baseline_metrics,
            "baseline_on_current": baseline_on_current,
            "performance_drop": performance_drop,
        },
        "retrain": {
            "needed": retrain_needed,
            "candidate_metrics": candidate_metrics,
            "canary": asdict(canary_result) if canary_result else None,
            "promoted": promoted,
        },
        "artifacts": {
            "baseline_model": _serialize_path(baseline_artifacts.model_path),
            "candidate_model": _serialize_path(candidate_artifacts.model_path) if candidate_artifacts else None,
        },
    }

    _write_json(report_dir / "pipeline_report.json", report)
    return report
