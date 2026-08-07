import pytest

from app.services.live_risk_guard import LiveRiskGuard, LiveRiskLimits, TradingMode


def open_live_guard(**kwargs):
    return LiveRiskGuard(
        limits=LiveRiskLimits(max_order_notional=5000.0, max_daily_loss=1000.0),
        mode=TradingMode.LIVE,
        kill_switch=False,
        live_confirmed=True,
        **kwargs,
    )


def test_default_state_keeps_live_execution_closed():
    guard = LiveRiskGuard()
    status = guard.readiness()
    assert status["mode"] == "paper"
    assert status["kill_switch"] is True
    assert status["live_execution_allowed"] is False
    with pytest.raises(PermissionError, match="gate is closed"):
        guard.validate_order(order_key="a", quantity=1, price=100)


def test_live_requires_kill_switch_off_and_explicit_confirmation():
    guard = LiveRiskGuard(mode=TradingMode.LIVE, kill_switch=False, live_confirmed=False)
    assert guard.readiness()["live_execution_allowed"] is False
    guard.live_confirmed = True
    assert guard.readiness()["live_execution_allowed"] is True


def test_max_order_notional_is_enforced():
    guard = open_live_guard()
    guard.validate_order(order_key="ok", quantity=5, price=1000)
    with pytest.raises(PermissionError, match="max order notional exceeded"):
        guard.validate_order(order_key="too-large", quantity=6, price=1000)


def test_daily_loss_limit_closes_live_gate():
    guard = open_live_guard(daily_pnl=-1000.0)
    assert guard.readiness()["live_execution_allowed"] is False
    with pytest.raises(PermissionError, match="gate is closed"):
        guard.validate_order(order_key="loss", quantity=1, price=100)


def test_duplicate_order_is_blocked_after_acceptance():
    guard = open_live_guard()
    guard.validate_order(order_key="same", quantity=1, price=100)
    guard.mark_order_accepted("same")
    with pytest.raises(PermissionError, match="duplicate order blocked"):
        guard.validate_order(order_key="same", quantity=1, price=100)


def test_invalid_quantity_or_price_is_rejected():
    guard = open_live_guard()
    with pytest.raises(ValueError, match="must be positive"):
        guard.validate_order(order_key="bad", quantity=0, price=100)
