from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services.assets import default_india_registry
from app.services.broker_gateway import BrokerGateway, BrokerMode
from app.services.broker_smoke import run_broker_smoke_test
from app.services.decision import DecisionEngine
from app.services.indicators import add_indicators
from app.services.live_risk_guard import LiveRiskGuard, TradingMode
from app.services.paper_broker_adapter import PaperBrokerAdapter
from app.services.paper_trading import PaperAccount, PaperBroker
from app.services.paper_validation import validate_paper_result
from app.services.paper_validation_metrics import PaperValidationMetrics
from app.services.pipeline import TradingPipeline
from app.services.risk import RiskEngine
from app.services.shadow_execution import ShadowExecutionRecorder, ShadowOrderIntent

APP_VERSION = "1.7.0"
app = FastAPI(title="TradeMind AI", version=APP_VERSION)

registry = default_india_registry()
gateway_account = PaperAccount(starting_cash=100000)
broker_gateway = BrokerGateway(mode=BrokerMode.PAPER)
broker_gateway.register(PaperBrokerAdapter(gateway_account, registry))
live_risk_guard = LiveRiskGuard()
shadow_recorder = ShadowExecutionRecorder()
paper_validation_metrics = PaperValidationMetrics()


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


class ShadowOrderRequest(BaseModel):
    order_key: str = Field(min_length=1)
    broker: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: str
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)


@app.get("/health")
def health():
    return {"status": "ok", "service": "trademind-ai", "version": APP_VERSION}


@app.get("/v1/readiness")
def readiness():
    result = dict(live_risk_guard.readiness())
    result.update(
        {
            "service_version": APP_VERSION,
            "broker_gateway_mode": broker_gateway.mode.value,
            "shadow_intent_count": len(shadow_recorder.intents),
            "paper_validation_total_runs": paper_validation_metrics.total_runs,
            "real_broker_dispatch_enabled": False,
        }
    )
    return result


@app.get("/v1/paper/metrics")
def paper_metrics():
    return paper_validation_metrics.summary()


@app.get("/v1/shadow/summary")
def shadow_summary():
    intents = shadow_recorder.intents
    return {
        "mode": "shadow",
        "intent_count": len(intents),
        "broker_order_sent": False,
        "executed": False,
        "latest": None
        if not intents
        else {
            "order_key": intents[-1].order_key,
            "broker": intents[-1].broker,
            "symbol": intents[-1].symbol,
            "side": intents[-1].side.upper(),
            "quantity": intents[-1].quantity,
            "price": intents[-1].price,
            "notional": intents[-1].notional,
        },
    }


@app.post("/v1/shadow/order")
def shadow_order(req: ShadowOrderRequest):
    if live_risk_guard.mode is not TradingMode.SHADOW:
        raise HTTPException(status_code=409, detail="shadow mode is not enabled")
    try:
        return shadow_recorder.record(ShadowOrderIntent(**req.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/brokers")
def broker_status():
    return {
        "mode": broker_gateway.mode.value,
        "brokers": [
            broker_gateway.get(name).connection_status()
            for name in broker_gateway.brokers()
        ],
    }


@app.get("/v1/brokers/{broker}/smoke")
def broker_smoke(broker: str, symbol: str):
    try:
        adapter = broker_gateway.get(broker)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"broker not registered: {broker}") from exc
    return run_broker_smoke_test(adapter, symbol=symbol)


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
    account_snapshot = {
        "cash": round(account.cash, 2),
        "positions": dict(account.positions),
        "trade_count": len(account.trades),
    }
    result["account"] = account_snapshot
    validation = validate_paper_result(result, account_snapshot).as_dict()
    result["validation"] = validation
    paper_validation_metrics.record(validation)
    return result
