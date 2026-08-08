import pytest

from app.services.audit_log import AuditLog
from app.services.broker_gateway import BrokerAdapter, BrokerOrder
from app.services.controlled_live_gateway import ControlledLiveGateway
from app.services.live_risk_guard import LiveRiskGuard, LiveRiskLimits, TradingMode


class RecordingAdapter(BrokerAdapter):
    name = "recording"

    def __init__(self):
        self.orders = []

    def connection_status(self):
        return {"broker": self.name, "connected": True}

    def quote(self, symbol: str):
        return {"symbol": symbol, "ltp": 100.0}

    def positions(self):
        return []

    def funds(self):
        return {"available": 100000.0}

    def place_order(self, order: BrokerOrder):
        self.orders.append(order)
        return {"status": "accepted", "order_id": "OID-1"}


def open_guard(**kwargs):
    defaults = {
        "mode": TradingMode.LIVE,
        "kill_switch": False,
        "live_confirmed": True,
    }
    defaults.update(kwargs)
    return LiveRiskGuard(**defaults)


def test_blocked_order_never_reaches_broker_and_is_audited():
    adapter = RecordingAdapter()
    audit = AuditLog()
    gateway = ControlledLiveGateway(adapter, LiveRiskGuard(), audit)

    with pytest.raises(PermissionError, match="gate is closed"):
        gateway.place_order(
            order_key="blocked-1",
            order=BrokerOrder("RELIANCE", "BUY", 1),
            reference_price=100.0,
        )

    assert adapter.orders == []
    assert [event["event_type"] for event in audit.recent()] == [
        "live_order_attempted",
        "live_order_blocked",
    ]


def test_open_guard_only_approves_preflight_and_never_calls_broker():
    adapter = RecordingAdapter()
    audit = AuditLog()
    gateway = ControlledLiveGateway(adapter, open_guard(), audit)

    result = gateway.place_order(
        order_key="ok-1",
        order=BrokerOrder("RELIANCE", "BUY", 1),
        reference_price=100.0,
    )

    assert result == {
        "approved": True,
        "executed": False,
        "broker_order_sent": False,
        "mode": "live_preflight",
        "broker": "recording",
        "order_key": "ok-1",
    }
    assert adapter.orders == []
    assert [event["event_type"] for event in audit.recent()] == [
        "live_order_attempted",
        "live_order_preflight_approved",
    ]


def test_preflight_does_not_mark_duplicate_without_actual_submission():
    adapter = RecordingAdapter()
    audit = AuditLog()
    gateway = ControlledLiveGateway(adapter, open_guard(), audit)
    order = BrokerOrder("RELIANCE", "BUY", 1)

    first = gateway.place_order(order_key="dup-1", order=order, reference_price=100.0)
    second = gateway.place_order(order_key="dup-1", order=order, reference_price=100.0)

    assert first["approved"] is True
    assert second["approved"] is True
    assert adapter.orders == []


def test_over_notional_is_blocked_before_broker_call():
    adapter = RecordingAdapter()
    audit = AuditLog()
    guard = open_guard(limits=LiveRiskLimits(max_order_notional=50.0, max_daily_loss=1000.0))
    gateway = ControlledLiveGateway(adapter, guard, audit)

    with pytest.raises(PermissionError, match="max order notional exceeded"):
        gateway.place_order(
            order_key="big-1",
            order=BrokerOrder("RELIANCE", "BUY", 1),
            reference_price=100.0,
        )

    assert adapter.orders == []
    assert audit.recent()[-1]["event_type"] == "live_order_blocked"


def test_daily_loss_limit_blocks_preflight():
    adapter = RecordingAdapter()
    audit = AuditLog()
    guard = open_guard(daily_pnl=-1000.0)
    gateway = ControlledLiveGateway(adapter, guard, audit)

    with pytest.raises(PermissionError, match="gate is closed"):
        gateway.place_order(
            order_key="loss-1",
            order=BrokerOrder("RELIANCE", "BUY", 1),
            reference_price=100.0,
        )

    assert adapter.orders == []
