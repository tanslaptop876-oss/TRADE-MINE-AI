from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_ALERT_JOURNAL_PATH = Path("data/paper_alert_journal.json")


class PaperAlertJournal:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @classmethod
    def from_environment(cls) -> "PaperAlertJournal":
        configured = os.getenv("PAPER_ALERT_JOURNAL_PATH")
        return cls(configured or DEFAULT_ALERT_JOURNAL_PATH)

    def load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {
            code: state
            for code, state in payload.items()
            if isinstance(code, str) and isinstance(state, dict)
        }

    def save(self, states: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            temporary_path.write_text(
                json.dumps(states, separators=(",", ":"), sort_keys=True),
                encoding="utf-8",
            )
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


class PaperAlertManager:
    def __init__(
        self,
        journal: PaperAlertJournal | None = None,
        *,
        cooldown_runs: int = 5,
    ) -> None:
        if cooldown_runs < 0:
            raise ValueError("cooldown_runs cannot be negative")
        self.journal = journal
        self.cooldown_runs = cooldown_runs
        self.outbound_delivery_enabled = False
        self._states = {} if journal is None else journal.load()

    def current(
        self,
        alerts: list[dict[str, str]],
        *,
        current_run: int,
    ) -> list[dict[str, str]]:
        visible: list[dict[str, str]] = []
        seen: set[str] = set()
        for alert in alerts:
            code = alert.get("code")
            if not isinstance(code, str) or not code or code in seen:
                continue
            seen.add(code)
            state = self._states.get(code, {})
            resolved_run = state.get("resolved_run")
            if (
                isinstance(resolved_run, int)
                and current_run - resolved_run < self.cooldown_runs
            ):
                continue
            decorated = dict(alert)
            decorated["status"] = (
                "acknowledged"
                if state.get("status") == "acknowledged"
                else "active"
            )
            visible.append(decorated)
        return visible

    def acknowledge(self, code: str, *, current_run: int) -> None:
        self._states[code] = {
            "status": "acknowledged",
            "updated_run": current_run,
        }
        self._persist()

    def resolve(self, code: str, *, current_run: int) -> None:
        self._states[code] = {
            "status": "resolved",
            "resolved_run": current_run,
            "updated_run": current_run,
        }
        self._persist()

    def _persist(self) -> None:
        if self.journal is not None:
            self.journal.save(self._states)
