from app.main import (
    APP_VERSION,
    ShadowOrderRequest,
    health,
    live_risk_guard,
    readiness,
    shadow_order,
    shadow_recorder,
    shadow_summary,
)
from app.services.live_risk_guard import TradingMode


def setup_function():
    shadow_recorder.intents.clear()
    live_risk_guard.mode = TradingMode.PAPER
    live_risk_guard.kill_switch = True
    live_risk_guard.live_confirmed = False
    live_risk_guard.daily_pnl = 0.0


def test_health_reports_v17_version():
    assert APP_VERSION == "1.7.0"
    assert health()["version"] == "1.7.0"


def test_readiness_reports_execution_hard_lock():
    result = readiness()

    assert result["service_version"] == "1.7.0"
    assert result["broker_gateway_mode"] == "paper"
    assert result["shadow_intent_count"] == 0
    assert result["real_broker_dispatch_enabled"] is False


def test_shadow_summary_is_safe_when_empty():
    result = shadow_summary()

    assert result == {
        "mode": "shadow",
        "intent_count": 0,
        "broker_order_sent": False,
        "executed": False,
        "latest": None,
    }


def test_shadow_summary_tracks_latest_intent_without_dispatch():
    live_risk_guard.mode = TradingMode.SHADOW

    order_result = shadow_order(
        ShadowOrderRequest(
            order_key="shadow-1",
            broker="upstox",
            symbol="RELIANCE",
            side="BUY",
            quantity=2,
            price=100.0,
        )
    )
    summary = shadow_summary()
    ready = readiness()

    assert order_result["executed"] is False
    assert order_result["broker_order_sent"] is False
    assert summary["intent_count"] == 1
    assert summary["executed"] is False
    assert summary["broker_order_sent"] is False
    assert summary["latest"]["order_key"] == "shadow-1"
    assert summary["latest"]["notional"] == 200.0
    assert ready["shadow_intent_count"] == 1
    assert ready["real_broker_dispatch_enabled"] is False
