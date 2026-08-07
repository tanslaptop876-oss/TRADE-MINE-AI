from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.services.market_data import MarketDataRequest


@dataclass
class YFinanceProvider:
    """Historical/research market-data adapter backed by yfinance.

    This provider is intended for research, prototyping, and backtesting.
    It should not be treated as a broker-grade or execution-grade live feed.
    """

    auto_adjust: bool = False

    def fetch(self, request: MarketDataRequest) -> Iterable[dict]:
        import yfinance as yf

        kwargs = {
            "tickers": request.symbol,
            "interval": request.interval,
            "auto_adjust": self.auto_adjust,
            "progress": False,
            "threads": False,
        }
        if request.start is not None:
            kwargs["start"] = request.start
        if request.end is not None:
            kwargs["end"] = request.end

        frame = yf.download(**kwargs)
        if frame.empty:
            return []

        if getattr(frame.columns, "nlevels", 1) > 1:
            frame.columns = frame.columns.get_level_values(0)

        frame = frame.reset_index()
        timestamp_col = "Datetime" if "Datetime" in frame.columns else "Date"

        rows = []
        for _, row in frame.iterrows():
            rows.append(
                {
                    "timestamp": row[timestamp_col],
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row.get("Volume", 0),
                }
            )
        return rows
