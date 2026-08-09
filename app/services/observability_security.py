from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DEFAULT_AUDIT_PATH = Path("data/observability_audit.jsonl")
DEFAULT_AUDIT_MAX_RECORDS = 10_000
DEFAULT_AUDIT_LOCK_TIMEOUT_SECONDS = 5.0
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
    def __init__(
        self,
        path: str | Path,
        *,
        max_records: int = DEFAULT_AUDIT_MAX_RECORDS,
        lock_timeout_seconds: float = DEFAULT_AUDIT_LOCK_TIMEOUT_SECONDS,
    ) -> None:
        if max_records < 1:
            raise ValueError("max_records must be positive")
        if lock_timeout_seconds <= 0:
            raise ValueError("lock_timeout_seconds must be positive")
        self.path = Path(path)
        self.max_records = max_records
        self.lock_timeout_seconds = lock_timeout_seconds

    @property
    def lock_path(self) -> Path:
        return self.path.with_suffix(f"{self.path.suffix}.lock")

    @classmethod
    def from_environment(cls) -> "ObservabilityAuditJournal":
        configured_path = os.getenv("OBSERVABILITY_AUDIT_PATH")
        configured_retention = os.getenv("OBSERVABILITY_AUDIT_MAX_RECORDS")
        max_records = DEFAULT_AUDIT_MAX_RECORDS
        if configured_retention:
            try:
                parsed_retention = int(configured_retention)
            except ValueError:
                parsed_retention = DEFAULT_AUDIT_MAX_RECORDS
            if parsed_retention > 0:
                max_records = parsed_retention
        return cls(configured_path or DEFAULT_AUDIT_PATH, max_records=max_records)

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.lock_timeout_seconds
        descriptor: int | None = None
        while descriptor is None:
            try:
                descriptor = os.open(
                    self.lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("observability audit lock timed out")
                time.sleep(0.01)
        try:
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            yield
        finally:
            os.close(descriptor)
            self.lock_path.unlink(missing_ok=True)

    def append(self, event_type: str, details: dict[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "recorded_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "details": redact_sensitive(details),
        }
        with self._exclusive_lock():
            with self.path.open("a", encoding="utf-8") as audit_file:
                audit_file.write(
                    json.dumps(event, separators=(",", ":"), sort_keys=True)
                )
                audit_file.write("\n")
                audit_file.flush()
                os.fsync(audit_file.fileno())
            self._compact_if_needed()

    def _load(self) -> list[dict[str, Any]]:
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
        return events

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._load()[-limit:]

    def _compact_if_needed(self) -> None:
        events = self._load()
        if len(events) <= self.max_records:
            return
        retained = events[-self.max_records :]
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            with temporary_path.open("w", encoding="utf-8") as compacted_file:
                for event in retained:
                    compacted_file.write(
                        json.dumps(event, separators=(",", ":"), sort_keys=True)
                    )
                    compacted_file.write("\n")
                compacted_file.flush()
                os.fsync(compacted_file.fileno())
            os.replace(temporary_path, self.path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def diagnostics(self) -> dict[str, Any]:
        valid_records = 0
        malformed_records = 0
        if self.path.exists():
            with self.path.open(encoding="utf-8") as audit_file:
                for line in audit_file:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        malformed_records += 1
                        continue
                    if isinstance(event, dict):
                        valid_records += 1
                    else:
                        malformed_records += 1
        writer_lock_active = self.lock_path.exists()
        status = "degraded" if malformed_records else "ok"
        if writer_lock_active:
            status = "busy"
        return {
            "available": self.path.exists(),
            "valid_record_count": valid_records,
            "malformed_record_count": malformed_records,
            "writer_lock_active": writer_lock_active,
            "retention": {"max_records": self.max_records},
            "status": status,
        }
