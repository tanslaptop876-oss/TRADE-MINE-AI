import pytest

from app.services.assets import default_india_registry
from app.services.broker_gateway import BrokerGateway, BrokerMode, BrokerOrder
from app.services.paper_broker_adapter import PaperBrokerAdapter
from app.services.paper_trading import PaperAccount


def make_gateway(mode=BrokerMode.PAPER):
    account = PaperAccount(starting_cash=100000)
    gateway = BrokerGateway(mode=mode)
    gateway.register(PaperBrokerAdapter(account, default_india_registry()))
    return gateway, account


def test_gateway_registers_and_reports_paper_adapter():
    gateway, _ = make_gateway()
    assert gateway.brokers() == ["paper"]
    assert gateway.get("paper").connection_status()["connected"] is True


def test_paper_order_executes_through_common_gateway():
    gateway, account = make_gateway()
    result = gateway.place_order(
        "paper",
        BrokerOrder(symbol="RELIANCE", side="BUY", quantity=2, price=2500),
    )
    assert result["status"] == "filled"
    assert account.positions["RELIANCE"] == 2
    assert account.cash == 95000


def test_paper_order_requires_execution_price():
    gateway, _ = make_gateway()
    with pytest.raises(ValueError, match="explicit execution price"):
        gateway.place_order("paper", BrokerOrder(symbol="RELIANCE", side="BUY", quantity=1))


def test_live_gateway_requires_explicit_confirmation():
    gateway, _ = make_gateway(BrokerMode.LIVE)
    order = BrokerOrder(symbol="RELIANCE", side="BUY", quantity=1, price=2500)
    with pytest.raises(PermissionError, match="explicit confirmation"):
        gateway.place_order("paper", order)


def test_live_gateway_can_only_continue_after_confirmation():
    gateway, account = make_gateway(BrokerMode.LIVE)
    result = gateway.place_order(
        "paper",
        BrokerOrder(symbol="RELIANCE", side="BUY", quantity=1, price=2500),
        live_confirmed=True,
    )
    assert result["status"] == "filled"
    assert account.positions["RELIANCE"] == 1


def test_unknown_broker_is_rejected():
    gateway, _ = make_gateway()
    with pytest.raises(KeyError, match="broker not registered"):
        gateway.get("unknown")
