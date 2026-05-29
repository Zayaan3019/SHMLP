from pathlib import Path

from shmlrp.config import AppConfig
from shmlrp.orchestration.pipeline import run_pipeline


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    config = AppConfig(
        artifacts_dir=tmp_path,
        sample_size=500,
        drift_probability=0.8,
        random_seed=7,
    )
    report = run_pipeline(
        config,
        drift_probability=0.8,
        sample_size=500,
        seed=7,
    )

    assert report["status"] == "completed"
    assert "run_id" in report
    report_path = tmp_path / "runs" / report["run_id"] / "reports" / "pipeline_report.json"
    assert report_path.exists()
