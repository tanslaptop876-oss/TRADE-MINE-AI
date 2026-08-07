import pytest

from app.services.risk import RiskEngine


def test_position_size():
    result = RiskEngine(0.01).size_position(100000, 100, 95)
    assert result["risk_amount"] == 1000
    assert result["quantity"] == 200
    assert result["notional"] == 20000


def test_position_size_never_exceeds_available_capital():
    result = RiskEngine(0.01).size_position(10000, 1000, 999)
    assert result["quantity"] == 10
    assert result["notional"] <= 10000


def test_zero_stop_distance_returns_zero_quantity():
    result = RiskEngine(0.01).size_position(100000, 100, 100)
    assert result["quantity"] == 0
    assert result["notional"] == 0


def test_invalid_risk_fraction_rejected():
    with pytest.raises(ValueError):
        RiskEngine(0.10)


def test_invalid_capital_rejected():
    with pytest.raises(ValueError):
        RiskEngine().size_position(0, 100, 95)
