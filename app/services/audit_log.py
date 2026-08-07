from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor: str
    details: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AuditLog:
    events: list[AuditEvent] = field(default_factory=list)

    def record(self, event_type: str, *, actor: str = "system", **details: Any) -> dict[str, Any]:
        event = AuditEvent(event_type=event_type, actor=actor, details=dict(details))
        self.events.append(event)
        return asdict(event)

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        return [asdict(event) for event in self.events[-limit:]]
