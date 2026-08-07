import pandas as pd
from app.data.provider import MarketDataProvider

def test_validation():
    df = pd.DataFrame([{
        "timestamp": "2026-01-01",
        "open": 100, "high": 102, "low": 99, "close": 101, "volume": 1000
    }])
    out = MarketDataProvider.validate(df)
    assert len(out) == 1
    assert str(out["timestamp"].dtype).startswith("datetime")
