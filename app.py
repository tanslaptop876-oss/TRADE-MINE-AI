from abc import ABC, abstractmethod
import pandas as pd

class MarketDataProvider(ABC):
    @abstractmethod
    def history(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Return normalized OHLCV data for a symbol."""
        raise NotImplementedError

    @staticmethod
    def validate(df: pd.DataFrame) -> pd.DataFrame:
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        out = df.copy()
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
        numeric = ["open", "high", "low", "close", "volume"]
        for c in numeric:
            out[c] = pd.to_numeric(out[c], errors="coerce")
        out = out.dropna(subset=["timestamp"] + numeric)
        out = out[(out["high"] >= out[["open","close","low"]].max(axis=1))]
        out = out[(out["low"] <= out[["open","close","high"]].min(axis=1))]
        out = out.sort_values("timestamp").drop_duplicates("timestamp")
        return out.reset_index(drop=True)
