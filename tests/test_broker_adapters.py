import pytest

from app.services.broker_adapters import BrokerCredentials, ConfiguredBrokerAdapter
from app.services.broker_env import load_broker_credentials
from app.services.broker_gateway import BrokerOrder


def test_icici_credentials_report_missing_fields():
    creds = BrokerCredentials("icici", {"app_key": "key"})
    assert creds.configured is False
    assert creds.missing_fields() == ["client_secret", "user_id", "api_session"]


def test_upstox_credentials_are_configured_when_complete():
    creds = BrokerCredentials(
        "upstox",
        {
            "client_id": "client",
            "client_secret": "secret",
            "redirect_uri": "https://example.com/callback",
            "access_token": "token",
        },
    )
    assert creds.configured is True
    assert creds.missing_fields() == []


def test_environment_loader_uses_namespaced_keys_only():
    loaded = load_broker_credentials(
        {
            "TRADEMIND_ZERODHA_API_KEY": "key",
            "TRADEMIND_ZERODHA_API_SECRET": "secret",
            "TRADEMIND_ZERODHA_ACCESS_TOKEN": "token",
            "API_KEY": "must-not-be-used",
        }
    )
    assert loaded["zerodha"]["api_key"] == "key"
    assert "icici" not in loaded


def test_real_adapter_never_enables_live_orders_by_configuration_alone():
    creds = BrokerCredentials(
        "upstox",
        {
            "client_id": "client",
            "client_secret": "secret",
            "redirect_uri": "https://example.com/callback",
            "access_token": "token",
        },
    )
    adapter = ConfiguredBrokerAdapter("upstox", credentials=creds, transport_connected=True)
    assert adapter.connection_status()["live_orders_enabled"] is False
    with pytest.raises(PermissionError):
        adapter.place_order(BrokerOrder("RELIANCE", "BUY", 1, price=100.0))
