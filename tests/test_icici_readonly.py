import pytest

from app.services.broker_adapters import BrokerCredentials
from app.services.broker_gateway import BrokerOrder
from app.services.icici_readonly import build_icici_read_only_adapter


def complete_icici_credentials():
    return BrokerCredentials(
        "icici",
        {
            "app_key": "app",
            "client_secret": "secret",
            "user_id": "user",
            "api_session": "session",
        },
    )


class FakeIciciSdk:
    def __init__(self):
        self.quote_symbols = []

    def get_quotes(self, *, stock_code):
        self.quote_symbols.append(stock_code)
        return {"Success": [{"stock_code": stock_code, "ltp": 2500.0}]}

    def get_funds(self):
        return {"Success": {"available_margin": 100000.0}}


def test_icici_read_only_adapter_routes_sdk_quote_and_funds():
    sdk = FakeIciciSdk()
    adapter = build_icici_read_only_adapter(complete_icici_credentials(), sdk)

    assert adapter.quote("RELIANCE")["Success"][0]["ltp"] == 2500.0
    assert sdk.quote_symbols == ["RELIANCE"]
    assert adapter.funds()["Success"]["available_margin"] == 100000.0


def test_icici_live_order_stays_blocked():
    adapter = build_icici_read_only_adapter(complete_icici_credentials(), FakeIciciSdk())
    with pytest.raises(PermissionError):
        adapter.place_order(BrokerOrder("RELIANCE", "BUY", 1, price=100.0))


def test_icici_adapter_rejects_incomplete_credentials():
    with pytest.raises(ValueError):
        build_icici_read_only_adapter(
            BrokerCredentials("icici", {"app_key": "app"}),
            FakeIciciSdk(),
        )
