from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PaperValidationMetrics:
    max_recent_runs: int = 20
    health_valid_rate_threshold: float = 0.95
    health_min_runs: int = 5
    total_runs: int = 0
    valid_runs: int = 0
    invalid_runs: int = 0
    recent_issues: list[str] = field(default_factory=list)
    recent_runs: list[dict[str, Any]] = field(default_factory=list)

    def record(self, validation: dict[str, Any]) -> None:
        self.total_runs += 1
        valid = validation.get("valid") is True
        if valid:
            self.valid_runs += 1
        else:
            self.invalid_runs += 1

        issues = [
            issue
            for issue in validation.get("issues") or []
            if isinstance(issue, str) and issue
        ]
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

    def _valid_rate(self) -> float:
        return 0.0 if self.total_runs == 0 else self.valid_runs / self.total_runs

    def health_status(self) -> str:
        if self.total_runs < self.health_min_runs:
            return "insufficient_data"
        if self._valid_rate() >= self.health_valid_rate_threshold:
            return "healthy"
        return "degraded"

    def summary(self) -> dict[str, Any]:
        return {
            "total_runs": self.total_runs,
            "valid_runs": self.valid_runs,
            "invalid_runs": self.invalid_runs,
            "valid_rate": round(self._valid_rate(), 4),
            "recent_issues": list(self.recent_issues),
            "recent_runs": [dict(snapshot) for snapshot in self.recent_runs],
            "health_status": self.health_status(),
            "health_threshold": {
                "minimum_runs": self.health_min_runs,
                "minimum_valid_rate": self.health_valid_rate_threshold,
            },
            "real_broker_dispatch_enabled": False,
        }
