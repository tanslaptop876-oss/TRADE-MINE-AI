from dataclasses import dataclass
import math
import pandas as pd

from app.services.indicators import add_indicators


@dataclass
class BacktestResult:
    initial_capital: float
    final_capital: float
    total_return_pct: float
    trades: int
    wins: int
    losses: int
    win_rate_pct: float
    max_drawdown_pct: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    expectancy: float
    risk_adjusted_return: float


def _risk_adjusted_return(equity: pd.Series) -> float:
    returns = equity.pct_change().dropna()
    if returns.empty or float(returns.std()) == 0:
        return 0.0
    return float((returns.mean() / returns.std()) * math.sqrt(252))


def run_ema_backtest(rows, initial_capital=100000, risk_per_trade=0.01,
                     fee_rate=0.0005, slippage_rate=0.0002):
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    if not 0 < risk_per_trade <= 0.05:
        raise ValueError("risk_per_trade must be between 0 and 0.05")
    if fee_rate < 0 or slippage_rate < 0:
        raise ValueError("fees and slippage cannot be negative")

    df = add_indicators(rows).dropna().reset_index(drop=True)
    capital = float(initial_capital)
    equity = []
    position = 0
    entry = 0.0
    trades = 0
    trade_pnls = []

    for _, r in df.iterrows():
        price = float(r["close"])

        if position == 0 and r["ema20"] > r["ema50"]:
            risk_amount = capital * risk_per_trade
            stop_distance = max(float(r["atr14"]) * 1.5, price * 0.005)
            risk_qty = int(risk_amount // stop_distance)
            affordable_qty = int(capital // (price * (1 + slippage_rate)))
            position = max(0, min(risk_qty, affordable_qty))
            if position:
                entry = price * (1 + slippage_rate)
                entry_cost = position * entry
                entry_fee = entry_cost * fee_rate
                capital -= entry_cost + entry_fee

        elif position > 0 and r["ema20"] <= r["ema50"]:
            exit_price = price * (1 - slippage_rate)
            exit_value = position * exit_price
            exit_fee = exit_value * fee_rate
            entry_value = position * entry
            entry_fee = entry_value * fee_rate
            pnl = exit_value - exit_fee - entry_value - entry_fee
            capital += exit_value - exit_fee
            trade_pnls.append(pnl)
            trades += 1
            position = 0
            entry = 0.0

        equity.append(capital + (position * price if position else 0))

    if position:
        price = float(df.iloc[-1]["close"])
        exit_price = price * (1 - slippage_rate)
        exit_value = position * exit_price
        exit_fee = exit_value * fee_rate
        entry_value = position * entry
        entry_fee = entry_value * fee_rate
        pnl = exit_value - exit_fee - entry_value - entry_fee
        capital += exit_value - exit_fee
        trade_pnls.append(pnl)
        trades += 1
        equity.append(capital)

    eq = pd.Series(equity if equity else [initial_capital], dtype=float)
    peak = eq.cummax()
    drawdown = (eq - peak) / peak.replace(0, pd.NA)
    max_dd = abs(float(drawdown.min()) * 100) if not drawdown.dropna().empty else 0.0

    wins = sum(p > 0 for p in trade_pnls)
    losses = sum(p < 0 for p in trade_pnls)
    gross_profit = sum(p for p in trade_pnls if p > 0)
    gross_loss = abs(sum(p for p in trade_pnls if p < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (math.inf if gross_profit > 0 else 0.0)
    expectancy = sum(trade_pnls) / trades if trades else 0.0

    return BacktestResult(
        initial_capital=round(float(initial_capital), 2),
        final_capital=round(capital, 2),
        total_return_pct=round((capital / initial_capital - 1) * 100, 2),
        trades=trades,
        wins=wins,
        losses=losses,
        win_rate_pct=round((wins / trades) * 100, 2) if trades else 0.0,
        max_drawdown_pct=round(max_dd, 2),
        gross_profit=round(gross_profit, 2),
        gross_loss=round(gross_loss, 2),
        profit_factor=round(profit_factor, 3) if math.isfinite(profit_factor) else math.inf,
        expectancy=round(expectancy, 2),
        risk_adjusted_return=round(_risk_adjusted_return(eq), 3),
    )
