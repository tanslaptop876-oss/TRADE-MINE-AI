from fastapi.testclient import TestClient

from app.main import app


def test_readiness_defaults_to_safe_locked_state():
    response = TestClient(app).get("/v1/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "paper"
    assert payload["kill_switch"] is True
    assert payload["live_execution_allowed"] is False


def test_shadow_order_records_intent_without_sending_broker_order():
    response = TestClient(app).post(
        "/v1/shadow/order",
        json={
            "order_key": "shadow-1",
            "broker": "upstox",
            "symbol": "RELIANCE",
            "side": "BUY",
            "quantity": 2,
            "price": 2500,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "shadow"
    assert payload["executed"] is False
    assert payload["broker_order_sent"] is False
    assert payload["notional"] == 5000


def test_shadow_order_rejects_invalid_side():
    response = TestClient(app).post(
        "/v1/shadow/order",
        json={
            "order_key": "shadow-bad",
            "broker": "upstox",
            "symbol": "RELIANCE",
            "side": "HOLD",
            "quantity": 1,
            "price": 100,
        },
    )
    assert response.status_code == 400
    assert "side must be BUY or SELL" in response.json()["detail"]
