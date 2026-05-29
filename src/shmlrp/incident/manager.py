from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from shmlrp.utils import utc_now_iso


@dataclass
class Incident:
    severity: str
    title: str
    details: dict
    tags: list[str]


class IncidentManager:
    def __init__(self, incident_path: Path) -> None:
        self.incident_path = incident_path

    def create_incident(
        self,
        severity: str,
        title: str,
        details: dict,
        tags: list[str],
    ) -> Incident:
        incident = Incident(severity=severity, title=title, details=details, tags=tags)
        record = {
            "timestamp": utc_now_iso(),
            "severity": severity,
            "title": title,
            "details": details,
            "tags": tags,
        }
        self.incident_path.parent.mkdir(parents=True, exist_ok=True)
        with self.incident_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        return incident
