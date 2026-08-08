import pytest

from app.services.audit_log import AuditLog
from app.services.broker_gateway import BrokerAdapter, BrokerOrder
from app.services.controlled_live_gateway import ControlledLiveGateway
from app.services.live_risk_guard import LiveRiskGuard, TradingMode


class RecordingAdapter(BrokerAdapter):
    name = "recording"

    def __init__(self, fail=False):
        self.fail = fail
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
        if self.fail:
            raise RuntimeError("broker rejected order")
        self.orders.append(order)
        return {"status": "accepted", "order_id": "OID-1"}


def open_guard():
    return LiveRiskGuard(mode=TradingMode.LIVE, kill_switch=False, live_confirmed=True)


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


def test_successful_order_is_sent_once_and_audited():
    adapter = RecordingAdapter()
    audit = AuditLog()
    gateway = ControlledLiveGateway(adapter, open_guard(), audit)

    result = gateway.place_order(
        order_key="ok-1",
        order=BrokerOrder("RELIANCE", "BUY", 1),
        reference_price=100.0,
    )

    assert result["status"] == "accepted"
    assert len(adapter.orders) == 1
    assert [event["event_type"] for event in audit.recent()] == [
        "live_order_attempted",
        "live_order_sent",
    ]


def test_duplicate_order_is_blocked_before_second_broker_call():
    adapter = RecordingAdapter()
    audit = AuditLog()
    gateway = ControlledLiveGateway(adapter, open_guard(), audit)
    order = BrokerOrder("RELIANCE", "BUY", 1)

    gateway.place_order(order_key="dup-1", order=order, reference_price=100.0)
    with pytest.raises(PermissionError, match="duplicate order blocked"):
        gateway.place_order(order_key="dup-1", order=order, reference_price=100.0)

    assert len(adapter.orders) == 1
    assert audit.recent()[-1]["event_type"] == "live_order_blocked"


def test_broker_failure_is_audited_and_not_marked_accepted():
    adapter = RecordingAdapter(fail=True)
    audit = AuditLog()
    guard = open_guard()
    gateway = ControlledLiveGateway(adapter, guard, audit)

    with pytest.raises(RuntimeError, match="broker rejected order"):
        gateway.place_order(
            order_key="fail-1",
            order=BrokerOrder("RELIANCE", "BUY", 1),
            reference_price=100.0,
        )

    assert audit.recent()[-1]["event_type"] == "live_order_failed"

    adapter.fail = False
    gateway.place_order(
        order_key="fail-1",
        order=BrokerOrder("RELIANCE", "BUY", 1),
        reference_price=100.0,
    )
    assert len(adapter.orders) == 1
