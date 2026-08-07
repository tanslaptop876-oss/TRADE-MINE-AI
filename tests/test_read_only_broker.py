import pytest

from app.services.broker_adapters import BrokerCredentials
from app.services.broker_gateway import BrokerOrder
from app.services.read_only_broker import build_read_only_adapter


def complete_upstox_credentials():
    return BrokerCredentials(
        "upstox",
        {
            "client_id": "client",
            "client_secret": "secret",
            "redirect_uri": "https://example.com/callback",
            "access_token": "token",
        },
    )


def test_read_only_adapter_routes_quote_and_funds():
    adapter = build_read_only_adapter(
        name="upstox",
        credentials=complete_upstox_credentials(),
        quote_call=lambda **kwargs: {"symbol": kwargs["symbol"], "ltp": 100.5},
        funds_call=lambda **kwargs: {"available": 25000.0},
    )

    assert adapter.quote("NSE_EQ|RELIANCE") == {"symbol": "NSE_EQ|RELIANCE", "ltp": 100.5}
    assert adapter.funds() == {"available": 25000.0}


def test_read_only_adapter_keeps_live_orders_locked():
    adapter = build_read_only_adapter(
        name="upstox",
        credentials=complete_upstox_credentials(),
        quote_call=lambda **kwargs: {},
        funds_call=lambda **kwargs: {},
    )

    with pytest.raises(PermissionError):
        adapter.place_order(BrokerOrder("RELIANCE", "BUY", 1, price=100.0))


def test_read_only_adapter_rejects_incomplete_credentials():
    with pytest.raises(ValueError):
        build_read_only_adapter(
            name="upstox",
            credentials=BrokerCredentials("upstox", {"client_id": "client"}),
            quote_call=lambda **kwargs: {},
            funds_call=lambda **kwargs: {},
        )
