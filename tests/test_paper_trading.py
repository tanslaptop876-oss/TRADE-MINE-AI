import pytest

from app.services.assets import AssetClass, default_india_registry
from app.services.paper_signal import execute_decision_signal
from app.services.paper_trading import PaperAccount, PaperBroker, PaperOrder, Side


def _broker(cash=100000.0):
    return PaperBroker(PaperAccount(starting_cash=cash), default_india_registry())


def test_registry_supports_multiple_asset_classes():
    registry = default_india_registry()
    assert registry.get("RELIANCE").asset_class == AssetClass.EQUITY
    assert registry.get("CRUDEOIL").asset_class == AssetClass.COMMODITY
    assert registry.get("USDINR").asset_class == AssetClass.CURRENCY


def test_paper_buy_and_sell_updates_cash_and_position():
    broker = _broker()
    buy = broker.execute(PaperOrder("RELIANCE", Side.BUY, 10, 1000.0))
    assert buy["cash_after"] == 90000.0
    assert broker.account.positions["RELIANCE"] == 10

    broker.execute(PaperOrder("RELIANCE", Side.SELL, 4, 1100.0))
    assert broker.account.positions["RELIANCE"] == 6
    assert broker.account.cash == 94400.0


def test_rejects_insufficient_cash_and_oversell():
    broker = _broker(cash=1000.0)
    with pytest.raises(ValueError, match="insufficient"):
        broker.execute(PaperOrder("RELIANCE", Side.BUY, 2, 600.0))
    with pytest.raises(ValueError, match="cannot sell"):
        broker.execute(PaperOrder("RELIANCE", Side.SELL, 1, 600.0))


def test_enforces_contract_lot_size():
    broker = _broker(cash=1000000.0)
    with pytest.raises(ValueError, match="lot_size"):
        broker.execute(PaperOrder("USDINR", Side.BUY, 1, 90.0))


def test_hold_signal_does_not_trade():
    broker = _broker()
    result = execute_decision_signal(
        broker, symbol="RELIANCE", action="HOLD", quantity=10, price=1000.0
    )
    assert result["status"] == "skipped"
    assert broker.account.trades == []


def test_buy_signal_executes_paper_order():
    broker = _broker()
    result = execute_decision_signal(
        broker, symbol="RELIANCE", action="BUY", quantity=5, price=1000.0
    )
    assert result["side"] == "BUY"
    assert broker.account.positions["RELIANCE"] == 5


def test_mark_to_market_equity():
    broker = _broker()
    broker.execute(PaperOrder("RELIANCE", Side.BUY, 10, 1000.0))
    assert broker.equity({"RELIANCE": 1100.0}) == 101000.0
