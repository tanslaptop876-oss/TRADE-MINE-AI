from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_HISTORY_PATH = Path("data/paper_validation_history.jsonl")


class PaperValidationHistory:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @classmethod
    def from_environment(cls) -> "PaperValidationHistory":
        configured_path = os.getenv("PAPER_VALIDATION_HISTORY_PATH")
        return cls(configured_path or DEFAULT_HISTORY_PATH)

    def append(self, snapshot: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as history_file:
            history_file.write(json.dumps(snapshot, separators=(",", ":"), sort_keys=True))
            history_file.write("\n")

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
                    snapshots.append(snapshot)
        return snapshots

    def recent(self, limit: int) -> list[dict[str, Any]]:
        return self.load()[-limit:]
