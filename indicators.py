from dataclasses import dataclass, asdict
import pandas as pd
from app.services.indicators import add_indicators
from app.services.metrics import performance_metrics

@dataclass
class BacktestResult:
    config: dict
    metrics: dict
    trades: list[dict]
    equity_curve: list[dict]

def run_ema_backtest_v2(rows, initial_capital=100000, risk_per_trade=0.01,
                        fee_rate=0.0005, slippage_rate=0.0002):
    """
    Long-only baseline strategy:
      Entry: EMA20 > EMA50
      Exit: EMA20 <= EMA50
    Assumptions are explicit and configurable.
    """
    df = add_indicators(rows).dropna().reset_index(drop=True)
    capital = float(initial_capital)
    cash = capital
    position = 0
    entry_price = 0.0
    entry_time = None
    trades = []
    equity_curve = []

    for _, r in df.iterrows():
        price = float(r["close"])
        ts = str(r["timestamp"])

        if position == 0 and r["ema20"] > r["ema50"]:
            risk_amount = cash * risk_per_trade
            stop_distance = max(float(r["atr14"]) * 1.5, price * 0.005)
            qty = int(risk_amount / stop_distance)
            if qty > 0:
                entry_price = price * (1 + slippage_rate)
                entry_cost = qty * entry_price
                fee = entry_cost * fee_rate
                if entry_cost + fee <= cash:
                    cash -= entry_cost + fee
                    position = qty
                    entry_time = ts

        elif position > 0 and r["ema20"] <= r["ema50"]:
            exit_price = price * (1 - slippage_rate)
            proceeds = position * exit_price
            fee = proceeds * fee_rate
            pnl = proceeds - fee - (position * entry_price)
            cash += proceeds - fee
            trades.append({
                "entry_time": entry_time,
                "exit_time": ts,
                "entry": round(entry_price, 4),
                "exit": round(exit_price, 4),
                "quantity": position,
                "pnl": round(pnl, 2),
            })
            position = 0
            entry_price = 0.0
            entry_time = None

        equity = cash + (position * price if position else 0)
        equity_curve.append({"timestamp": ts, "equity": equity})

    if position > 0:
        price = float(df.iloc[-1]["close"])
        exit_price = price * (1 - slippage_rate)
        proceeds = position * exit_price
        fee = proceeds * fee_rate
        pnl = proceeds - fee - (position * entry_price)
        cash += proceeds - fee
        trades.append({
            "entry_time": entry_time,
            "exit_time": str(df.iloc[-1]["timestamp"]),
            "entry": round(entry_price, 4),
            "exit": round(exit_price, 4),
            "quantity": position,
            "pnl": round(pnl, 2),
        })
        equity_curve.append({"timestamp": str(df.iloc[-1]["timestamp"]), "equity": cash})

    eq = pd.Series([x["equity"] for x in equity_curve])
    metrics = performance_metrics(eq, trades)

    return BacktestResult(
        config={
            "initial_capital": initial_capital,
            "risk_per_trade": risk_per_trade,
            "fee_rate": fee_rate,
            "slippage_rate": slippage_rate,
        },
        metrics=metrics,
        trades=trades,
        equity_curve=equity_curve,
    )

def walk_forward_slices(df: pd.DataFrame, train_ratio: float = 0.7):
    if not 0.5 < train_ratio < 0.95:
        raise ValueError("train_ratio must be between 0.5 and 0.95")
    cut = int(len(df) * train_ratio)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()
