from fastapi import APIRouter, HTTPException
from app.data.csv_provider import CSVMarketDataProvider
from app.services.pro_backtest import run_ema_backtest_v2

router = APIRouter(prefix="/v1/backtest", tags=["backtest"])

@router.post("/csv")
def backtest_csv(path: str, initial_capital: float = 100000,
                 risk_per_trade: float = 0.01, fee_rate: float = 0.0005,
                 slippage_rate: float = 0.0002):
    try:
        df = CSVMarketDataProvider().load_csv(path)
        result = run_ema_backtest_v2(
            df.to_dict("records"),
            initial_capital=initial_capital,
            risk_per_trade=risk_per_trade,
            fee_rate=fee_rate,
            slippage_rate=slippage_rate,
        )
        return {"config": result.config, "metrics": result.metrics,
                "trades": result.trades, "equity_curve": result.equity_curve}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
