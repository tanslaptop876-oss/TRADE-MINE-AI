from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_AUDIT_PATH = Path("data/observability_audit.jsonl")
SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "broker_token",
    "password",
    "secret",
    "token",
}


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                "[REDACTED]"
                if key.lower() in SENSITIVE_KEYS
                else redact_sensitive(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value


class ObservabilityAuditJournal:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @classmethod
    def from_environment(cls) -> "ObservabilityAuditJournal":
        configured = os.getenv("OBSERVABILITY_AUDIT_PATH")
        return cls(configured or DEFAULT_AUDIT_PATH)

    def append(self, event_type: str, details: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "event_type": event_type,
            "recorded_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "details": redact_sensitive(details),
        }
        with self.path.open("a", encoding="utf-8") as audit_file:
            audit_file.write(json.dumps(event, separators=(",", ":"), sort_keys=True))
            audit_file.write("\n")

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as audit_file:
            for line in audit_file:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    events.append(redact_sensitive(event))
        return events[-limit:]
