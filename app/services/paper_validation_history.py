from __future__ import annotations

import json
import os
import shutil
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from app.services.observability_security import ObservabilityAuditJournal, redact_sensitive


DEFAULT_HISTORY_PATH = Path("data/paper_validation_history.jsonl")
DEFAULT_MAX_RECORDS = 10_000
DEFAULT_LOCK_TIMEOUT_SECONDS = 5.0


class PaperValidationHistory:
    def __init__(
        self,
        path: str | Path,
        *,
        max_records: int = DEFAULT_MAX_RECORDS,
        max_age_days: int | None = None,
        lock_timeout_seconds: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
        audit_journal: ObservabilityAuditJournal | None = None,
    ) -> None:
        if max_records < 1:
            raise ValueError("max_records must be positive")
        if max_age_days is not None and max_age_days < 1:
            raise ValueError("max_age_days must be positive")
        if lock_timeout_seconds <= 0:
            raise ValueError("lock_timeout_seconds must be positive")
        self.path = Path(path)
        self.max_records = max_records
        self.max_age_days = max_age_days
        self.lock_timeout_seconds = lock_timeout_seconds
        self.audit_journal = audit_journal
        self.audit_status = "disabled" if audit_journal is None else "ok"
        self._recovery_reported = False

    @property
    def backup_path(self) -> Path:
        return self.path.with_suffix(f"{self.path.suffix}.bak")

    @property
    def lock_path(self) -> Path:
        return self.path.with_suffix(f"{self.path.suffix}.lock")

    @classmethod
    def from_environment(
        cls,
        *,
        audit_journal: ObservabilityAuditJournal | None = None,
    ) -> "PaperValidationHistory":
        configured_path = os.getenv("PAPER_VALIDATION_HISTORY_PATH")
        configured_retention = os.getenv("PAPER_VALIDATION_HISTORY_MAX_RECORDS")
        configured_age = os.getenv("PAPER_VALIDATION_HISTORY_MAX_AGE_DAYS")
        max_records = DEFAULT_MAX_RECORDS
        max_age_days = None
        if configured_retention:
            try:
                parsed_retention = int(configured_retention)
            except ValueError:
                parsed_retention = DEFAULT_MAX_RECORDS
            if parsed_retention > 0:
                max_records = parsed_retention
        if configured_age:
            try:
                parsed_age = int(configured_age)
            except ValueError:
                parsed_age = 0
            if parsed_age > 0:
                max_age_days = parsed_age
        return cls(
            configured_path or DEFAULT_HISTORY_PATH,
            max_records=max_records,
            max_age_days=max_age_days,
            audit_journal=audit_journal,
        )

    def _audit(self, event_type: str, details: dict[str, Any]) -> None:
        if self.audit_journal is None:
            return
        try:
            self.audit_journal.append(event_type, details)
            self.audit_status = "ok"
        except OSError:
            self.audit_status = "error"

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
                    raise TimeoutError("paper validation history lock timed out")
                time.sleep(0.01)
        try:
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            yield
        finally:
            os.close(descriptor)
            self.lock_path.unlink(missing_ok=True)

    def append(self, snapshot: dict[str, Any]) -> None:
        persisted = redact_sensitive(dict(snapshot))
        persisted.setdefault(
            "recorded_at",
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        with self._exclusive_lock():
            with self.path.open("a", encoding="utf-8") as history_file:
                history_file.write(json.dumps(persisted, separators=(",", ":"), sort_keys=True))
                history_file.write("\n")
                history_file.flush()
                os.fsync(history_file.fileno())
            self._compact_if_needed()
        self._audit(
            "paper_validation_history_appended",
            {
                "run_number": persisted.get("run_number"),
                "valid": persisted.get("valid"),
            },
        )

    def _load_path(self, path: Path) -> list[dict[str, Any]]:
        snapshots: list[dict[str, Any]] = []
        if not path.exists():
            return snapshots
        with path.open(encoding="utf-8") as history_file:
            for line in history_file:
                try:
                    snapshot = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(snapshot, dict):
                    snapshots.append(redact_sensitive(snapshot))
        return snapshots

    def load(self) -> list[dict[str, Any]]:
        snapshots = self._load_path(self.path)
        if snapshots or not self.path.exists():
            return snapshots
        recovered = self._load_path(self.backup_path)
        if recovered and not self._recovery_reported:
            self._audit(
                "paper_validation_history_recovered",
                {"recovered_record_count": len(recovered)},
            )
            self._recovery_reported = True
        return recovered

    def recent(self, limit: int) -> list[dict[str, Any]]:
        return self.load()[-limit:]

    def _within_age_limit(self, snapshot: dict[str, Any], cutoff: datetime) -> bool:
        recorded_at = snapshot.get("recorded_at")
        if not isinstance(recorded_at, str):
            return True
        try:
            parsed = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
        except ValueError:
            return True
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed >= cutoff

    def _compact_if_needed(self) -> None:
        snapshots = self._load_path(self.path)
        retained = snapshots
        if self.max_age_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
            retained = [
                snapshot
                for snapshot in retained
                if self._within_age_limit(snapshot, cutoff)
            ]
        retained = retained[-self.max_records :]
        if retained == snapshots:
            return

        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            if self.path.exists():
                shutil.copyfile(self.path, self.backup_path)
            with temporary_path.open("w", encoding="utf-8") as compacted_file:
                for snapshot in retained:
                    compacted_file.write(
                        json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
                    )
                    compacted_file.write("\n")
                compacted_file.flush()
                os.fsync(compacted_file.fileno())
            os.replace(temporary_path, self.path)
            self._audit(
                "paper_validation_history_compacted",
                {
                    "previous_record_count": len(snapshots),
                    "retained_record_count": len(retained),
                },
            )
        finally:
            temporary_path.unlink(missing_ok=True)


    def diagnostics(self) -> dict[str, Any]:
        valid_primary = 0
        malformed_primary = 0
        if self.path.exists():
            with self.path.open(encoding="utf-8") as history_file:
                for line in history_file:
                    try:
                        snapshot = json.loads(line)
                    except json.JSONDecodeError:
                        malformed_primary += 1
                        continue
                    if isinstance(snapshot, dict):
                        valid_primary += 1
                    else:
                        malformed_primary += 1
        backup_records = self._load_path(self.backup_path)
        recovery_active = (
            self.path.exists()
            and valid_primary == 0
            and bool(backup_records)
        )
        writer_lock_active = self.lock_path.exists()
        status = "ok"
        if malformed_primary or recovery_active:
            status = "degraded"
        if writer_lock_active:
            status = "busy"
        return {
            "available": self.path.exists(),
            "status": status,
            "valid_record_count": len(self.load()),
            "malformed_record_count": malformed_primary,
            "backup_available": bool(backup_records),
            "backup_recovery_active": recovery_active,
            "writer_lock_active": writer_lock_active,
            "retention": {
                "max_records": self.max_records,
                "max_age_days": self.max_age_days,
            },
            "audit_status": self.audit_status,
        }
