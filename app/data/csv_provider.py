import pandas as pd

class CSVMarketDataProvider:
    def load(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path)
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df.sort_values("timestamp").dropna().reset_index(drop=True)
