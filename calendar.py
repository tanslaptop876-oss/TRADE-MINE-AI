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
    # Transparent baseline. ML/LLM layers can be added later without removing
    # deterministic evidence and risk controls.
    def evaluate(self, df: pd.DataFrame) -> Decision:
        if len(df) < 55:
            raise ValueError("At least 55 candles are required.")

        row = df.iloc[-1]
        price = float(row["close"])
        atr = float(row["atr14"])
        if pd.isna(atr) or atr <= 0:
            raise ValueError("Insufficient ATR data.")

        score = 0
        evidence = []

        if row["ema20"] > row["ema50"]:
            score += 1
            evidence.append("EMA20 is above EMA50")
        else:
            score -= 1
            evidence.append("EMA20 is below EMA50")

        if row["macd"] > row["macd_signal"]:
            score += 1
            evidence.append("MACD is above signal")
        else:
            score -= 1
            evidence.append("MACD is below signal")

        rsi = float(row["rsi14"])
        if 50 <= rsi <= 70:
            score += 1
            evidence.append(f"RSI supports bullish momentum ({rsi:.1f})")
        elif 30 <= rsi < 50:
            score -= 1
            evidence.append(f"RSI is weak ({rsi:.1f})")

        vol_ma = row["volume_ma20"]
        if not pd.isna(vol_ma) and row["volume"] > vol_ma:
            score += 1
            evidence.append("Volume is above its 20-period average")

        if score >= 2:
            action = "BUY"
            stop = price - 1.5 * atr
            target = price + 3.0 * atr
        elif score <= -2:
            action = "SELL"
            stop = price + 1.5 * atr
            target = price - 3.0 * atr
        else:
            action = "HOLD"
            stop = price
            target = price

        confidence = min(95.0, 50.0 + abs(score) * 10.0)
        rr = abs(target - price) / max(abs(price - stop), 1e-9)

        return Decision(
            action=action,
            confidence=confidence,
            entry=price,
            stop_loss=stop,
            target=target,
            risk_reward=rr,
            evidence=evidence,
            invalidation="Invalid if stop-loss is hit or trend structure reverses."
        )
