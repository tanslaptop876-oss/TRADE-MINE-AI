import math
import pytest

from app.services.backtest import run_ema_backtest


def _trend_rows(n=120):
    rows = []
    for i in range(n):
        # Uptrend followed by a reversal to force at least one completed trade.
        price = 100 + i * 0.5 if i < 80 else 140 - (i - 80) * 0.8
        rows.append({
            "timestamp": f"2026-01-{(i % 28) + 1:02d}",
            "open": price,
            "high": price + 1,
            "low": price - 1,
            "close": price,
            "volume": 1000 + i,
        })
    return rows


def test_backtest_returns_extended_metrics():
    result = run_ema_backtest(_trend_rows())
    assert result.final_capital >= 0
    assert result.trades >= 1
    assert result.wins + result.losses <= result.trades
    assert result.max_drawdown_pct >= 0
    assert result.gross_profit >= 0
    assert result.gross_loss >= 0
    assert result.profit_factor >= 0 or math.isinf(result.profit_factor)
    assert isinstance(result.expectancy, float)
    assert isinstance(result.risk_adjusted_return, float)


def test_backtest_rejects_invalid_risk():
    with pytest.raises(ValueError, match="risk_per_trade"):
        run_ema_backtest(_trend_rows(), risk_per_trade=0.10)


def test_backtest_rejects_invalid_capital():
    with pytest.raises(ValueError, match="initial_capital"):
        run_ema_backtest(_trend_rows(), initial_capital=0)


def test_backtest_never_uses_more_cash_than_available():
    result = run_ema_backtest(_trend_rows(), initial_capital=1000, risk_per_trade=0.05)
    assert result.final_capital >= 0
