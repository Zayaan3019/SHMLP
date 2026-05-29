from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib

from shmlrp.utils import ensure_dir, utc_now_iso


@dataclass
class ModelArtifacts:
    model_path: Path
    metadata_path: Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


class ModelRegistry:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.models_dir = ensure_dir(base_dir / "models")
        self.metadata_dir = ensure_dir(base_dir / "metadata")

    def save(self, model, metadata: dict, model_name: str) -> ModelArtifacts:
        model_path = self.models_dir / f"{model_name}.joblib"
        metadata_path = self.metadata_dir / f"{model_name}.json"

        joblib.dump(model, model_path)
        metadata_with_time = {"saved_at": utc_now_iso(), **metadata}
        _write_json(metadata_path, metadata_with_time)

        return ModelArtifacts(model_path=model_path, metadata_path=metadata_path)
