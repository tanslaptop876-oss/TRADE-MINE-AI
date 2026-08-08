from __future__ import annotations

from collections import Counter
from typing import Any


def filter_validation_runs(
    runs: list[dict[str, Any]],
    *,
    outcome: str = "all",
    symbol: str = "all",
    service_version: str = "all",
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for run in runs:
        if outcome == "valid" and run.get("valid") is not True:
            continue
        if outcome == "invalid" and run.get("valid") is True:
            continue
        if symbol != "all" and run.get("symbol") != symbol:
            continue
        if service_version != "all" and run.get("service_version") != service_version:
            continue
        filtered.append(run)
    return filtered


def issue_frequency(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(
        issue
        for run in runs
        for issue in run.get("issues") or []
        if isinstance(issue, str) and issue
    )
    return [
        {"issue": issue, "count": count}
        for issue, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def filter_options(
    runs: list[dict[str, Any]],
    key: str,
) -> list[str]:
    return ["all", *sorted({
        value
        for run in runs
        if isinstance((value := run.get(key)), str) and value
    })]
