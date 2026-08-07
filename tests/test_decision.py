import pandas as pd
import pytest

from app.services.decision import DecisionEngine


def _frame(**overrides):
    row = {
        "close": 100.0,
        "atr14": 2.0,
        "ema20": 105.0,
        "ema50": 100.0,
        "ema_spread_pct": 5.0,
        "macd": 1.0,
        "macd_signal": 0.5,
        "macd_hist": 0.5,
        "rsi14": 60.0,
        "volume": 1500.0,
        "volume_ma20": 1000.0,
        "volume_ratio": 1.5,
    }
    row.update(overrides)
    return pd.DataFrame([row] * 55)


def test_buy_signal():
    decision = DecisionEngine().evaluate(_frame())
    assert decision.action == "BUY"
    assert decision.stop_loss < decision.entry < decision.target
    assert decision.risk_reward >= 2.0
    assert decision.confidence > 50


def test_sell_signal():
    decision = DecisionEngine().evaluate(
        _frame(
            ema20=95.0,
            ema50=100.0,
            ema_spread_pct=-5.0,
            macd=-1.0,
            macd_signal=-0.2,
            macd_hist=-0.8,
            rsi14=40.0,
            volume=1600.0,
            volume_ratio=1.6,
        )
    )
    assert decision.action == "SELL"
    assert decision.target < decision.entry < decision.stop_loss
    assert decision.risk_reward >= 2.0


def test_hold_signal_has_no_trade_risk_reward():
    decision = DecisionEngine().evaluate(
        _frame(
            ema20=100.0,
            ema50=100.0,
            ema_spread_pct=0.0,
            macd=0.0,
            macd_signal=0.0,
            macd_hist=0.0,
            rsi14=50.0,
            volume=1000.0,
            volume_ratio=1.0,
        )
    )
    assert decision.action == "HOLD"
    assert decision.stop_loss == decision.entry
    assert decision.target == decision.entry
    assert decision.risk_reward == 0.0


def test_requires_enough_candles():
    with pytest.raises(ValueError, match="55 candles"):
        DecisionEngine().evaluate(_frame().iloc[:20])
