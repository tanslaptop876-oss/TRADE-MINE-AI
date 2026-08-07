import numpy as np
import pandas as pd

def performance_metrics(equity: pd.Series, trades: list[dict], periods_per_year: int = 252):
    equity = pd.Series(equity, dtype=float).dropna()
    if equity.empty:
        return {}

    returns = equity.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    years = max(len(equity) / periods_per_year, 1 / periods_per_year)
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1

    vol = returns.std(ddof=1)
    sharpe = (returns.mean() / vol) * np.sqrt(periods_per_year) if vol > 0 else 0.0

    downside = returns[returns < 0].std(ddof=1)
    sortino = (returns.mean() / downside) * np.sqrt(periods_per_year) if downside and downside > 0 else 0.0

    peak = equity.cummax()
    dd = equity / peak - 1
    max_dd = abs(dd.min())

    wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
    losses = sum(1 for t in trades if t.get("pnl", 0) < 0)
    gross_profit = sum(t["pnl"] for t in trades if t.get("pnl", 0) > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t.get("pnl", 0) < 0))
    profit_factor = gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else 0)

    return {
        "total_return_pct": round(total_return * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "sharpe": round(float(sharpe), 3),
        "sortino": round(float(sortino), 3),
        "trades": len(trades),
        "win_rate_pct": round((wins / len(trades)) * 100, 2) if trades else 0,
        "losses": losses,
        "profit_factor": round(float(profit_factor), 3) if np.isfinite(profit_factor) else "inf",
    }
