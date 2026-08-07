import pandas as pd
from app.services.metrics import performance_metrics

def test_metrics_basic():
    equity = pd.Series([100, 105, 102, 110])
    trades = [{"pnl": 5}, {"pnl": -2}, {"pnl": 8}]
    m = performance_metrics(equity, trades)
    assert m["trades"] == 3
    assert m["win_rate_pct"] == 66.67
    assert m["profit_factor"] == 6.5
