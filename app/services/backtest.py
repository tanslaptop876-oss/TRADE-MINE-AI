from dataclasses import dataclass
import pandas as pd
from app.services.indicators import add_indicators

@dataclass
class BacktestResult:
    initial_capital: float
    final_capital: float
    total_return_pct: float
    trades: int
    win_rate_pct: float
    max_drawdown_pct: float

def run_ema_backtest(rows, initial_capital=100000, risk_per_trade=0.01,
                     fee_rate=0.0005, slippage_rate=0.0002):
    df = add_indicators(rows).dropna().reset_index(drop=True)
    capital = float(initial_capital)
    equity = []
    position = 0
    entry = 0.0
    wins = 0
    trades = 0

    for _, r in df.iterrows():
        price = float(r["close"])

        if position == 0 and r["ema20"] > r["ema50"]:
            risk_amount = capital * risk_per_trade
            stop_distance = max(float(r["atr14"]) * 1.5, price * 0.005)
            position = max(0, int(risk_amount / stop_distance))
            if position:
                entry = price * (1 + slippage_rate)
                capital -= position * entry * fee_rate

        elif position > 0 and r["ema20"] <= r["ema50"]:
            exit_price = price * (1 - slippage_rate)
            pnl = position * (exit_price - entry)
            capital += position * exit_price
            capital -= position * exit_price * fee_rate
            trades += 1
            wins += int(pnl > 0)
            position = 0
            entry = 0.0

        equity.append(capital + (position * price if position else 0))

    if position:
        price = float(df.iloc[-1]["close"])
        exit_price = price * (1 - slippage_rate)
        pnl = position * (exit_price - entry)
        capital += position * exit_price
        capital -= position * exit_price * fee_rate
        trades += 1
        wins += int(pnl > 0)

    eq = pd.Series(equity + [capital])
    peak = eq.cummax()
    dd = (eq - peak) / peak
    max_dd = abs(float(dd.min()) * 100) if len(eq) else 0

    return BacktestResult(
        initial_capital=initial_capital,
        final_capital=round(capital, 2),
        total_return_pct=round((capital / initial_capital - 1) * 100, 2),
        trades=trades,
        win_rate_pct=round((wins / trades) * 100, 2) if trades else 0,
        max_drawdown_pct=round(max_dd, 2)
    )
