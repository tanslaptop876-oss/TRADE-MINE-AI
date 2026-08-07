from datetime import datetime, timezone

import pytest

from app.services.market_data import MarketDataRequest, MarketDataService, normalize_candles


class FakeProvider:
    def __init__(self, rows):
        self.rows = rows
        self.last_request = None

    def fetch(self, request):
        self.last_request = request
        return self.rows


def _row(timestamp="2026-01-01T09:15:00+05:30", **overrides):
    row = {
        "timestamp": timestamp,
        "open": 100,
        "high": 105,
        "low": 98,
        "close": 103,
        "volume": 1000,
    }
    row.update(overrides)
    return row


def test_normalizes_sorts_and_deduplicates_candles():
    rows = [
        _row("2026-01-02T09:15:00+05:30", close=104),
        _row("2026-01-01T09:15:00+05:30"),
        _row("2026-01-02T09:15:00+05:30", close=102),
    ]
    df = normalize_candles(rows)
    assert len(df) == 2
    assert df["timestamp"].is_monotonic_increasing
    assert df.iloc[-1]["close"] == 102


def test_rejects_invalid_ohlc_relationship():
    with pytest.raises(ValueError, match="high"):
        normalize_candles([_row(high=99)])


def test_rejects_negative_volume():
    with pytest.raises(ValueError, match="volume"):
        normalize_candles([_row(volume=-1)])


def test_request_rejects_bad_date_range():
    with pytest.raises(ValueError, match="start"):
        MarketDataRequest(
            symbol="NIFTY50",
            start=datetime(2026, 2, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_service_uses_provider_and_returns_normalized_frame():
    provider = FakeProvider([_row()])
    service = MarketDataService(provider)
    request = MarketDataRequest(symbol="RELIANCE", interval="5m")
    df = service.get_candles(request)
    assert provider.last_request == request
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert len(df) == 1
