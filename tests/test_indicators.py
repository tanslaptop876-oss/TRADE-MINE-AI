from app.services.indicators import add_indicators

def test_indicators():
    rows = []
    for i in range(70):
        p = 100 + i * 0.2
        rows.append({
            "timestamp": f"2026-01-{(i % 28) + 1:02d}",
            "open": p, "high": p + 1, "low": p - 1,
            "close": p, "volume": 1000
        })
    df = add_indicators(rows)
    assert "ema20" in df.columns
    assert "rsi14" in df.columns
    assert "atr14" in df.columns
