from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PaperValidationReport:
    valid: bool
    checks: dict[str, bool]
    issues: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "checks": dict(self.checks),
            "issues": list(self.issues),
        }


def validate_paper_result(result: dict[str, Any], account: dict[str, Any]) -> PaperValidationReport:
    issues: list[str] = []
    checks: dict[str, bool] = {}

    checks["decision_present"] = isinstance(result.get("decision"), dict)
    if not checks["decision_present"]:
        issues.append("decision missing")

    checks["execution_present"] = isinstance(result.get("execution"), dict)
    if not checks["execution_present"]:
        issues.append("execution missing")

    cash = account.get("cash")
    checks["cash_non_negative"] = isinstance(cash, (int, float)) and cash >= 0
    if not checks["cash_non_negative"]:
        issues.append("cash is negative or invalid")

    trade_count = account.get("trade_count")
    checks["trade_count_valid"] = isinstance(trade_count, int) and trade_count >= 0
    if not checks["trade_count_valid"]:
        issues.append("trade_count is invalid")

    execution = result.get("execution") or {}
    status = execution.get("status")
    checks["execution_status_known"] = status in {"filled", "skipped", "hold", "accepted"}
    if not checks["execution_status_known"]:
        issues.append(f"unknown execution status: {status}")

    risk = result.get("risk")
    decision = result.get("decision") or {}
    action = decision.get("action")
    checks["risk_consistent"] = action == "HOLD" or isinstance(risk, dict)
    if not checks["risk_consistent"]:
        issues.append("non-HOLD decision missing risk result")

    return PaperValidationReport(valid=all(checks.values()), checks=checks, issues=issues)
