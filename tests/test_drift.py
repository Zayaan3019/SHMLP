from shmlrp.data.generator import generate_datasets
from shmlrp.drift.detector import detect_drift


def test_detects_strong_drift() -> None:
    bundle = generate_datasets(sample_size=400, drift_probability=1.0, seed=11)
    result = detect_drift(bundle.baseline, bundle.current, threshold=0.1)
    assert result.is_drifted
    assert len(result.drifted_features) > 0
