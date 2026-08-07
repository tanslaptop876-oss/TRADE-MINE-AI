from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.services.assets import default_india_registry
from app.services.decision import DecisionEngine
from app.services.indicators import add_indicators
from app.services.paper_trading import PaperAccount, PaperBroker
from app.services.pipeline import TradingPipeline
from app.services.risk import RiskEngine

app = FastAPI(title="TradeMind AI", version="1.0.0")


class Candle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0


class SignalRequest(BaseModel):
    candles: list[Candle]
    capital: float = Field(default=100000, gt=0)
    risk_per_trade: float = Field(default=0.01, gt=0, le=0.05)


class PaperRunRequest(BaseModel):
    symbol: str
    candles: list[Candle]
    starting_cash: float = Field(default=100000, gt=0)
    risk_per_trade: float = Field(default=0.01, gt=0, le=0.05)


@app.get("/health")
def health():
    return {"status": "ok", "service": "trademind-ai", "version": "1.0.0"}


@app.post("/v1/signal")
def signal(req: SignalRequest):
    df = add_indicators([c.model_dump() for c in req.candles])
    decision = DecisionEngine().evaluate(df)
    risk = RiskEngine(req.risk_per_trade).size_position(
        capital=req.capital, entry=decision.entry, stop=decision.stop_loss
    )
    return {"decision": decision.model_dump(), "risk": risk}


@app.post("/v1/paper/run")
def paper_run(req: PaperRunRequest):
    registry = default_india_registry()
    account = PaperAccount(starting_cash=req.starting_cash)
    broker = PaperBroker(account, registry)
    pipeline = TradingPipeline(
        broker=broker,
        registry=registry,
        risk_per_trade=req.risk_per_trade,
    )
    result = pipeline.run(
        symbol=req.symbol,
        candles=[c.model_dump() for c in req.candles],
    )
    result["account"] = {
        "cash": round(account.cash, 2),
        "positions": dict(account.positions),
        "trade_count": len(account.trades),
    }
    return result
