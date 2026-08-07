from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

import pandas as pd


REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


@dataclass(frozen=True)
class MarketDataRequest:
    symbol: str
    interval: str = "1d"
    start: datetime | None = None
    end: datetime | None = None

    def __post_init__(self):
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol is required")
        if not self.interval or not self.interval.strip():
            raise ValueError("interval is required")
        if self.start and self.end and self.start > self.end:
            raise ValueError("start must be before end")


class MarketDataProvider(Protocol):
    def fetch(self, request: MarketDataRequest) -> Iterable[dict]:
        ...


def normalize_candles(rows: Iterable[dict]) -> pd.DataFrame:
    df = pd.DataFrame(list(rows)).copy()
    if df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required market data fields: {missing}")

    df = df[REQUIRED_COLUMNS].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    if df["timestamp"].isna().any():
        raise ValueError("timestamp values must be valid datetimes")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise ValueError("OHLCV values must be numeric")
    if (df[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("OHLC values must be positive")
    if (df["volume"] < 0).any():
        raise ValueError("volume cannot be negative")
    if (df["high"] < df[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("high must be greater than or equal to open, close, and low")
    if (df["low"] > df[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("low must be less than or equal to open, close, and high")

    df = df.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    return df.reset_index(drop=True)


class MarketDataService:
    def __init__(self, provider: MarketDataProvider):
        self.provider = provider

    def get_candles(self, request: MarketDataRequest) -> pd.DataFrame:
        return normalize_candles(self.provider.fetch(request))
