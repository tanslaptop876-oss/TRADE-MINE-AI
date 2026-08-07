from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.services.decision import DecisionEngine
from app.services.risk import RiskEngine
from app.services.indicators import add_indicators

app = FastAPI(title="TradeMind AI", version="0.1.0")

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
    risk_per_trade: float = Field(default=0.01, gt=0, lt=0.1)

@app.get("/health")
def health():
    return {"status": "ok", "service": "trademind-ai", "version": "0.1.0"}

@app.post("/v1/signal")
def signal(req: SignalRequest):
    df = add_indicators([c.model_dump() for c in req.candles])
    decision = DecisionEngine().evaluate(df)
    risk = RiskEngine(req.risk_per_trade).size_position(
        capital=req.capital, entry=decision.entry, stop=decision.stop_loss
    )
    return {"decision": decision.model_dump(), "risk": risk}
