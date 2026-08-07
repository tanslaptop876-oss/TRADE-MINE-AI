import pytest

from app.services.broker_adapters import BrokerCredentials
from app.services.broker_gateway import BrokerOrder
from app.services.upstox_readonly import build_upstox_read_only_adapter


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


def complete_upstox_credentials():
    return BrokerCredentials(
        "upstox",
        {
            "client_id": "client",
            "client_secret": "secret",
            "redirect_uri": "https://example.com/callback",
            "access_token": "token-123",
        },
    )


def test_upstox_quote_uses_bearer_auth_and_instrument_key():
    calls = []

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return FakeResponse({"status": "success", "data": {"NSE_EQ|INE002A01018": {"last_price": 2500}}})

    adapter = build_upstox_read_only_adapter(complete_upstox_credentials(), request)
    payload = adapter.quote("NSE_EQ|INE002A01018")

    assert payload["status"] == "success"
    method, url, kwargs = calls[0]
    assert method == "GET"
    assert url.endswith("/v2/market-quote/quotes")
    assert kwargs["headers"]["Authorization"] == "Bearer token-123"
    assert kwargs["params"] == {"instrument_key": "NSE_EQ|INE002A01018"}
    assert kwargs["timeout"] == 10


def test_upstox_funds_is_read_only_and_live_order_stays_blocked():
    def request(method, url, **kwargs):
        return FakeResponse({"status": "success", "data": {"equity": {"available_margin": 100000}}})

    adapter = build_upstox_read_only_adapter(complete_upstox_credentials(), request)
    assert adapter.funds()["data"]["equity"]["available_margin"] == 100000

    with pytest.raises(PermissionError):
        adapter.place_order(BrokerOrder("RELIANCE", "BUY", 1, price=100.0))


def test_upstox_http_errors_propagate_to_smoke_test_layer():
    def request(method, url, **kwargs):
        return FakeResponse({"status": "error"}, status_code=401)

    adapter = build_upstox_read_only_adapter(complete_upstox_credentials(), request)
    with pytest.raises(RuntimeError, match="http 401"):
        adapter.funds()
