import pytest

from app.services.indicators import add_indicators


def make_rows(step=0.2, count=70):
    rows = []
    for i in range(count):
        p = 100 + i * step
        rows.append(
            {
                "timestamp": f"2026-01-{(i % 28) + 1:02d}",
                "open": p,
                "high": p + 1,
                "low": p - 1,
                "close": p,
                "volume": 1000 + i * 5,
            }
        )
    return rows


def test_indicators_include_v04_metrics():
    df = add_indicators(make_rows())
    for column in [
        "ema20",
        "ema50",
        "ema_spread_pct",
        "rsi14",
        "macd_hist",
        "atr14",
        "atr_pct",
        "volume_ratio",
    ]:
        assert column in df.columns
    assert df.iloc[-1]["rsi14"] == 100.0


def test_flat_market_rsi_is_neutral():
    df = add_indicators(make_rows(step=0))
    assert df.iloc[-1]["rsi14"] == 50.0


def test_missing_ohlc_field_is_rejected():
    rows = make_rows()
    for row in rows:
        row.pop("high")
    with pytest.raises(ValueError, match="Missing required candle fields"):
        add_indicators(rows)
