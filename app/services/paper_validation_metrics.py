from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.paper_validation_history import PaperValidationHistory


@dataclass
class PaperValidationMetrics:
    max_recent_runs: int = 20
    health_valid_rate_threshold: float = 0.95
    health_min_runs: int = 5
    history: PaperValidationHistory | None = None
    total_runs: int = 0
    valid_runs: int = 0
    invalid_runs: int = 0
    recent_issues: list[str] = field(default_factory=list)
    recent_runs: list[dict[str, Any]] = field(default_factory=list)
    history_status: str = field(init=False)

    def __post_init__(self) -> None:
        self.history_status = "disabled" if self.history is None else "ok"
        if self.history is None:
            return
        try:
            for persisted in self.history.load():
                self._apply_snapshot(persisted)
        except OSError:
            self.history_status = "error"

    def _apply_snapshot(self, snapshot: dict[str, Any]) -> None:
        valid = snapshot.get("valid") is True
        issues = [
            issue
            for issue in snapshot.get("issues") or []
            if isinstance(issue, str) and issue
        ]
        self.total_runs += 1
        if valid:
            self.valid_runs += 1
        else:
            self.invalid_runs += 1

        self.recent_issues.extend(issues)
        self.recent_issues = self.recent_issues[-self.max_recent_runs :]
        self.recent_runs.append(
            {
                "run_number": self.total_runs,
                "valid": valid,
                "issue_count": len(issues),
                "issues": issues[-self.max_recent_runs :],
            }
        )
        self.recent_runs = self.recent_runs[-self.max_recent_runs :]

    def record(self, validation: dict[str, Any]) -> None:
        snapshot = {
            "valid": validation.get("valid") is True,
            "issues": [
                issue
                for issue in validation.get("issues") or []
                if isinstance(issue, str) and issue
            ],
        }
        self._apply_snapshot(snapshot)
        if self.history is not None:
            persisted = dict(self.recent_runs[-1])
            try:
                self.history.append(persisted)
                self.history_status = "ok"
            except OSError:
                self.history_status = "error"

    def _valid_rate(self) -> float:
        return 0.0 if self.total_runs == 0 else self.valid_runs / self.total_runs

    def health_status(self) -> str:
        if self.total_runs < self.health_min_runs:
            return "insufficient_data"
        if self._valid_rate() >= self.health_valid_rate_threshold:
            return "healthy"
        return "degraded"

    def alerts(self) -> list[dict[str, str]]:
        alerts: list[dict[str, str]] = []
        if self.history_status == "error":
            alerts.append(
                {
                    "code": "paper_validation_history_unavailable",
                    "severity": "warning",
                    "status": "active",
                    "message": "Paper validation history could not be persisted.",
                }
            )
        if self.health_status() == "degraded":
            alerts.append(
                {
                    "code": "paper_validation_rate_below_threshold",
                    "severity": "warning",
                    "status": "active",
                    "message": (
                        "Paper validation valid rate is below the configured "
                        "health threshold."
                    ),
                }
            )
        return alerts

    def history_snapshots(self, limit: int = 20) -> list[dict[str, Any]]:
        snapshots = self.recent_runs[-limit:]
        if self.history is not None and self.history_status == "ok":
            try:
                snapshots = self.history.recent(limit)
            except OSError:
                self.history_status = "error"

        public_snapshots: list[dict[str, Any]] = []
        for index, snapshot in enumerate(snapshots, start=1):
            issues = [
                issue
                for issue in snapshot.get("issues") or []
                if isinstance(issue, str) and issue
            ]
            run_number = snapshot.get("run_number", index)
            public_snapshots.append(
                {
                    "run_number": run_number if isinstance(run_number, int) else index,
                    "valid": snapshot.get("valid") is True,
                    "issue_count": len(issues),
                    "issues": issues[-self.max_recent_runs :],
                }
            )
        return public_snapshots

    def summary(self) -> dict[str, Any]:
        return {
            "total_runs": self.total_runs,
            "valid_runs": self.valid_runs,
            "invalid_runs": self.invalid_runs,
            "valid_rate": round(self._valid_rate(), 4),
            "recent_issues": list(self.recent_issues),
            "recent_runs": self.history_snapshots(self.max_recent_runs),
            "health_status": self.health_status(),
            "health_threshold": {
                "minimum_runs": self.health_min_runs,
                "minimum_valid_rate": self.health_valid_rate_threshold,
            },
            "history_persistence": {
                "enabled": self.history is not None,
                "status": self.history_status,
            },
            "real_broker_dispatch_enabled": False,
        }
