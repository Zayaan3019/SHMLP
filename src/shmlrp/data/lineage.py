from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from shmlrp.utils import utc_now_iso


@dataclass
class LineageTracker:
    lineage_path: Path

    def record_step(
        self,
        run_id: str,
        step_name: str,
        inputs: dict[str, str],
        outputs: dict[str, str],
        metadata: dict[str, str] | None = None,
    ) -> None:
        record = {
            "run_id": run_id,
            "timestamp": utc_now_iso(),
            "step": step_name,
            "inputs": inputs,
            "outputs": outputs,
            "metadata": metadata or {},
        }
        self.lineage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lineage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
