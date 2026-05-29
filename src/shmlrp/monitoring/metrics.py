from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from shmlrp.utils import utc_now_iso


@dataclass
class MetricsStore:
    metrics_path: Path

    def record(self, run_id: str, payload: dict, tags: list[str] | None = None) -> None:
        record = {
            "run_id": run_id,
            "timestamp": utc_now_iso(),
            "tags": tags or [],
            "metrics": payload,
        }
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with self.metrics_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
