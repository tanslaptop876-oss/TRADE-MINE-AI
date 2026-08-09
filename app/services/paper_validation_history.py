from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.observability_security import redact_sensitive


DEFAULT_HISTORY_PATH = Path("data/paper_validation_history.jsonl")
DEFAULT_MAX_RECORDS = 10_000


class PaperValidationHistory:
    def __init__(
        self,
        path: str | Path,
        *,
        max_records: int = DEFAULT_MAX_RECORDS,
    ) -> None:
        if max_records < 1:
            raise ValueError("max_records must be positive")
        self.path = Path(path)
        self.max_records = max_records

    @classmethod
    def from_environment(cls) -> "PaperValidationHistory":
        configured_path = os.getenv("PAPER_VALIDATION_HISTORY_PATH")
        configured_retention = os.getenv("PAPER_VALIDATION_HISTORY_MAX_RECORDS")
        max_records = DEFAULT_MAX_RECORDS
        if configured_retention:
            try:
                parsed_retention = int(configured_retention)
            except ValueError:
                parsed_retention = DEFAULT_MAX_RECORDS
            if parsed_retention > 0:
                max_records = parsed_retention
        return cls(configured_path or DEFAULT_HISTORY_PATH, max_records=max_records)

    def append(self, snapshot: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        persisted = redact_sensitive(dict(snapshot))
        persisted.setdefault(
            "recorded_at",
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        with self.path.open("a", encoding="utf-8") as history_file:
            history_file.write(json.dumps(persisted, separators=(",", ":"), sort_keys=True))
            history_file.write("\n")
        self._compact_if_needed()

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        snapshots: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as history_file:
            for line in history_file:
                try:
                    snapshot = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(snapshot, dict):
                    snapshots.append(redact_sensitive(snapshot))
        return snapshots

    def recent(self, limit: int) -> list[dict[str, Any]]:
        return self.load()[-limit:]

    def _compact_if_needed(self) -> None:
        snapshots = self.load()
        if len(snapshots) <= self.max_records:
            return

        retained = snapshots[-self.max_records :]
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            with temporary_path.open("w", encoding="utf-8") as compacted_file:
                for snapshot in retained:
                    compacted_file.write(
                        json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
                    )
                    compacted_file.write("\n")
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()
