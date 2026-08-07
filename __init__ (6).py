import pandas as pd

def quality_report(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"rows": 0, "valid": False, "issues": ["empty dataset"]}

    issues = []
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"rows": len(df), "valid": False, "issues": [f"missing columns: {missing}"]}

    if df[required].isna().any().any():
        issues.append("null values present")

    if (df["high"] < df[["open", "close", "low"]].max(axis=1)).any():
        issues.append("invalid high prices")

    if (df["low"] > df[["open", "close", "high"]].min(axis=1)).any():
        issues.append("invalid low prices")

    duplicate_timestamps = df["timestamp"].duplicated().sum()
    if duplicate_timestamps:
        issues.append(f"{duplicate_timestamps} duplicate timestamps")

    return {
        "rows": len(df),
        "valid": len(issues) == 0,
        "issues": issues,
        "start": str(df["timestamp"].min()),
        "end": str(df["timestamp"].max()),
    }
