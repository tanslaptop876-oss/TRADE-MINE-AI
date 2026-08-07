from __future__ import annotations

from typing import Any

from app.services.broker_gateway import BrokerAdapter


def _check(fn, *args, **kwargs) -> dict[str, Any]:
    try:
        value = fn(*args, **kwargs)
        return {"ok": True, "data": value}
    except Exception as exc:  # boundary reports broker failures without crashing API
        return {"ok": False, "error": str(exc), "error_type": type(exc).__name__}


def run_broker_smoke_test(adapter: BrokerAdapter, *, symbol: str) -> dict[str, Any]:
    checks = {
        "quote": _check(adapter.quote, symbol),
        "funds": _check(adapter.funds),
        "positions": _check(adapter.positions),
    }
    return {
        "broker": adapter.name,
        "connected": all(item["ok"] for item in checks.values()),
        "checks": checks,
    }
