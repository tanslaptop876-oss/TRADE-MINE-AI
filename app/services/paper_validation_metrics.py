from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PaperValidationMetrics:
    total_runs: int = 0
    valid_runs: int = 0
    invalid_runs: int = 0
    recent_issues: list[str] = field(default_factory=list)

    def record(self, validation: dict[str, Any]) -> None:
        self.total_runs += 1
        if validation.get("valid") is True:
            self.valid_runs += 1
        else:
            self.invalid_runs += 1

        for issue in validation.get("issues") or []:
            if isinstance(issue, str) and issue:
                self.recent_issues.append(issue)
        self.recent_issues = self.recent_issues[-20:]

    def summary(self) -> dict[str, Any]:
        valid_rate = 0.0 if self.total_runs == 0 else self.valid_runs / self.total_runs
        return {
            "total_runs": self.total_runs,
            "valid_runs": self.valid_runs,
            "invalid_runs": self.invalid_runs,
            "valid_rate": round(valid_rate, 4),
            "recent_issues": list(self.recent_issues),
            "real_broker_dispatch_enabled": False,
        }
