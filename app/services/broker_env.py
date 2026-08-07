from __future__ import annotations

import os
from typing import Mapping

from app.services.broker_adapters import BROKER_REQUIRED_CREDENTIALS


def _env_key(broker: str, field: str) -> str:
    return f"TRADEMIND_{broker.upper()}_{field.upper()}"


def load_broker_credentials(env: Mapping[str, str] | None = None) -> dict[str, dict[str, str]]:
    source = env or os.environ
    loaded: dict[str, dict[str, str]] = {}
    for broker, fields in BROKER_REQUIRED_CREDENTIALS.items():
        values = {
            field: source.get(_env_key(broker, field), "").strip()
            for field in fields
        }
        if any(values.values()):
            loaded[broker] = values
    return loaded
