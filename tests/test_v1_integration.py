from fastapi.testclient import TestClient

from app.main import app
from app.services.assets import default_india_registry
from app.services.paper_trading import PaperAccount, PaperBroker
from app.services.pipeline import TradingPipeline


def bullish_candles(count=80):
    rows = []
    for i in range(count):
        close = 100 + i * 0.8
        rows.append(
            {
                "timestamp": f"2026-01-{(i % 28) + 1:02d}T00:00:00Z",
                "open": close - 0.3,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1000 + i * 20,
            }
        )
    return rows


def test_pipeline_returns_dashboard_ready_shape():
    registry = default_india_registry()
    account = PaperAccount(starting_cash=100000)
    pipeline = TradingPipeline(
        broker=PaperBroker(account, registry),
        registry=registry,
        risk_per_trade=0.01,
    )

    result = pipeline.run(symbol="RELIANCE", candles=bullish_candles())

    assert result["symbol"] == "RELIANCE"
    assert result["asset_class"] == "equity"
    assert set(result) == {"symbol", "asset_class", "decision", "risk", "execution"}
    assert result["decision"]["action"] in {"BUY", "SELL", "HOLD"}


def test_paper_api_is_end_to_end_and_returns_account_state():
    client = TestClient(app)
    response = client.post(
        "/v1/paper/run",
        json={
            "symbol": "RELIANCE",
            "candles": bullish_candles(),
            "starting_cash": 100000,
            "risk_per_trade": 0.01,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "RELIANCE"
    assert "decision" in payload
    assert "execution" in payload
    assert payload["account"]["cash"] >= 0
    assert isinstance(payload["account"]["positions"], dict)
    assert payload["account"]["trade_count"] >= 0


def test_health_reports_v1():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "1.0.0"
