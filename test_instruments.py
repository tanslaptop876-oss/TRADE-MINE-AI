from pathlib import Path
import pandas as pd

from app.data.provider import MarketDataProvider
from app.data.instruments import get_instrument

class YahooFinanceProvider(MarketDataProvider):
    """
    Development-only market-data adapter.
    It keeps TradeMind's data layer provider-agnostic so a licensed
    NSE/BSE/broker feed can replace it later without changing the engine.
    """

    def __init__(self, cache_dir: str = "data_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def history(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError(
                "yfinance is not installed. Install requirements.txt or use CSVMarketDataProvider."
            ) from exc

        instrument = get_instrument(symbol)
        df = yf.download(
            instrument.provider_symbol,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=False,
            progress=False,
            group_by="column",
        )

        if df.empty:
            raise ValueError(f"No market data returned for {symbol}")

        # yfinance may return MultiIndex columns depending on version.
        if hasattr(df.columns, "levels"):
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

        df = df.reset_index()
        rename = {
            "Date": "timestamp",
            "Datetime": "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        df = df.rename(columns=rename)
        keep = ["timestamp", "open", "high", "low", "close", "volume"]
        df = df[keep]
        df = self.validate(df)
        df["symbol"] = instrument.symbol
        df["exchange"] = instrument.exchange
        df["segment"] = instrument.segment
        return df

    def history_cached(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        safe = f"{symbol}_{start}_{end}_{interval}".replace("/", "-").replace(":", "-")
        path = self.cache_dir / f"{safe}.csv"
        if path.exists():
            return pd.read_csv(path, parse_dates=["timestamp"])
        df = self.history(symbol, start, end, interval)
        df.to_csv(path, index=False)
        return df
