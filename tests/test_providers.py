from datetime import datetime, timezone

import pandas as pd

from app.services.market_data import MarketDataRequest, MarketDataService
from app.services.providers import YFinanceProvider


def test_yfinance_provider_maps_downloaded_frame(monkeypatch):
    index = pd.DatetimeIndex([pd.Timestamp("2026-08-03", tz="UTC")], name="Date")
    downloaded = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [105.0],
            "Low": [99.0],
            "Close": [104.0],
            "Volume": [10000],
        },
        index=index,
    )

    import yfinance as yf

    monkeypatch.setattr(yf, "download", lambda **kwargs: downloaded)
    service = MarketDataService(YFinanceProvider())
    result = service.get_candles(
        MarketDataRequest(
            symbol="RELIANCE.NS",
            interval="1d",
            start=datetime(2026, 8, 1, tzinfo=timezone.utc),
            end=datetime(2026, 8, 5, tzinfo=timezone.utc),
        )
    )

    assert len(result) == 1
    assert result.iloc[0]["close"] == 104.0
    assert result.iloc[0]["volume"] == 10000


def test_yfinance_provider_handles_empty_download(monkeypatch):
    import yfinance as yf

    monkeypatch.setattr(yf, "download", lambda **kwargs: pd.DataFrame())
    rows = list(YFinanceProvider().fetch(MarketDataRequest(symbol="TCS.NS")))
    assert rows == []
