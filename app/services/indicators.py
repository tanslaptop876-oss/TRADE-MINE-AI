import numpy as np
import pandas as pd


def add_indicators(rows) -> pd.DataFrame:
    df = pd.DataFrame(rows).copy()
    if df.empty:
        return df

    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required candle fields: {sorted(missing)}")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[["open", "high", "low", "close"]].isna().any().any():
        raise ValueError("OHLC values must be numeric")

    close, high, low = df["close"], df["high"], df["low"]
    df["ema20"] = close.ewm(span=20, adjust=False).mean()
    df["ema50"] = close.ewm(span=50, adjust=False).mean()
    df["ema_spread_pct"] = ((df["ema20"] - df["ema50"]) / close.replace(0, np.nan)) * 100

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    avg_gain = gain
    avg_loss = loss
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    rsi = rsi.mask((avg_gain == 0) & (avg_loss > 0), 0.0)
    rsi = rsi.mask((avg_gain == 0) & (avg_loss == 0), 50.0)
    df["rsi14"] = rsi

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr14"] = tr.rolling(14).mean()
    df["atr_pct"] = (df["atr14"] / close.replace(0, np.nan)) * 100
    df["volume_ma20"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_ma20"].replace(0, np.nan)
    df["trend"] = np.where(df["ema20"] > df["ema50"], "bullish", "bearish")
    return df
