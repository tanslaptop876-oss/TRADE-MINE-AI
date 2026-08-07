from pydantic import BaseModel, Field
import pandas as pd


class Decision(BaseModel):
    action: str
    confidence: float = Field(ge=0, le=100)
    entry: float
    stop_loss: float
    target: float
    risk_reward: float
    evidence: list[str]
    invalidation: str


class DecisionEngine:
    """Transparent deterministic baseline for trading decision support."""

    def evaluate(self, df: pd.DataFrame) -> Decision:
        if len(df) < 55:
            raise ValueError("At least 55 candles are required.")

        row = df.iloc[-1]
        required = ["close", "atr14", "ema20", "ema50", "macd", "macd_signal", "rsi14"]
        if any(col not in df.columns for col in required):
            raise ValueError("Required indicators are missing.")

        price = float(row["close"])
        atr = float(row["atr14"])
        rsi = float(row["rsi14"])
        if pd.isna(atr) or atr <= 0 or price <= 0:
            raise ValueError("Insufficient price/ATR data.")
        if pd.isna(rsi):
            raise ValueError("Insufficient RSI data.")

        score = 0.0
        evidence: list[str] = []

        ema_spread = (float(row["ema20"]) - float(row["ema50"])) / price
        if ema_spread > 0:
            score += 1.0
            evidence.append("EMA20 is above EMA50")
            if ema_spread >= 0.01:
                score += 0.5
                evidence.append("Bullish EMA separation is meaningful")
        else:
            score -= 1.0
            evidence.append("EMA20 is below EMA50")
            if ema_spread <= -0.01:
                score -= 0.5
                evidence.append("Bearish EMA separation is meaningful")

        macd_hist = float(row["macd"] - row["macd_signal"])
        if macd_hist > 0:
            score += 1.0
            evidence.append("MACD momentum is positive")
        elif macd_hist < 0:
            score -= 1.0
            evidence.append("MACD momentum is negative")

        if 50 <= rsi <= 70:
            score += 1.0
            evidence.append(f"RSI supports bullish momentum ({rsi:.1f})")
        elif 30 <= rsi < 50:
            score -= 1.0
            evidence.append(f"RSI shows weak momentum ({rsi:.1f})")
        elif rsi > 75:
            score -= 0.5
            evidence.append(f"RSI is overbought ({rsi:.1f})")
        elif rsi < 25:
            score += 0.5
            evidence.append(f"RSI is oversold ({rsi:.1f})")

        vol_ma = row.get("volume_ma20")
        if vol_ma is not None and not pd.isna(vol_ma) and vol_ma > 0:
            ratio = float(row["volume"] / vol_ma)
            if ratio >= 1.2:
                score += 0.5 if score > 0 else (-0.5 if score < 0 else 0)
                evidence.append(f"Volume confirms momentum ({ratio:.2f}x average)")

        if score >= 2.0:
            action = "BUY"
            stop = price - 1.5 * atr
            target = price + 3.0 * atr
        elif score <= -2.0:
            action = "SELL"
            stop = price + 1.5 * atr
            target = price - 3.0 * atr
        else:
            action = "HOLD"
            stop = price
            target = price

        confidence = 50.0 if action == "HOLD" else min(95.0, 55.0 + abs(score) * 8.0)
        rr = 0.0 if action == "HOLD" else abs(target - price) / max(abs(price - stop), 1e-9)

        return Decision(
            action=action,
            confidence=round(confidence, 1),
            entry=round(price, 4),
            stop_loss=round(stop, 4),
            target=round(target, 4),
            risk_reward=round(rr, 2),
            evidence=evidence,
            invalidation=(
                "No active trade while signal is HOLD."
                if action == "HOLD"
                else "Invalid if stop-loss is hit or trend structure reverses."
            ),
        )
