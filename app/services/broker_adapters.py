from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from app.services.broker_gateway import BrokerAdapter, BrokerOrder


BROKER_REQUIRED_CREDENTIALS: dict[str, tuple[str, ...]] = {
    # ICICI Direct Trade API (normal ICICI Direct account): API session is
    # obtained via interactive login, then exchanged for SessionToken.
    "icici": ("app_key", "client_secret", "user_id", "api_session"),
    "zerodha": ("api_key", "api_secret", "access_token"),
    # Upstox OAuth2 access token flow.
    "upstox": ("client_id", "client_secret", "redirect_uri", "access_token"),
    "angelone": ("api_key", "client_code", "access_token"),
    "motilal_oswal": ("api_key", "client_code", "access_token"),
    "dhan": ("client_id", "access_token"),
    "fyers": ("client_id", "access_token"),
}


@dataclass(frozen=True)
class BrokerCredentials:
    broker: str
    values: Mapping[str, str] = field(default_factory=dict)

    @property
    def required_fields(self) -> tuple[str, ...]:
        return BROKER_REQUIRED_CREDENTIALS.get(self.broker, ())

    def missing_fields(self) -> list[str]:
        return [name for name in self.required_fields if not self.values.get(name, "").strip()]

    @property
    def configured(self) -> bool:
        return bool(self.required_fields) and not self.missing_fields()


@dataclass
class ConfiguredBrokerAdapter(BrokerAdapter):
    name: str
    credentials: BrokerCredentials | None = None
    transport_connected: bool = False

    def connection_status(self) -> dict[str, Any]:
        credentials = self.credentials or BrokerCredentials(self.name)
        return {
            "broker": self.name,
            "configured": credentials.configured,
            "missing_credentials": credentials.missing_fields(),
            "connected": self.transport_connected,
            "live_orders_enabled": False,
        }

    def _not_connected(self) -> RuntimeError:
        return RuntimeError(f"{self.name} API transport is not connected")

    def quote(self, symbol: str) -> dict[str, Any]:
        raise self._not_connected()

    def positions(self) -> list[dict[str, Any]]:
        raise self._not_connected()

    def funds(self) -> dict[str, Any]:
        raise self._not_connected()

    def place_order(self, order: BrokerOrder) -> dict[str, Any]:
        raise PermissionError(f"{self.name} live orders are not enabled")


def default_broker_adapters(
    credentials: Mapping[str, Mapping[str, str]] | None = None,
) -> list[ConfiguredBrokerAdapter]:
    credentials = credentials or {}
    return [
        ConfiguredBrokerAdapter(
            name,
            BrokerCredentials(name, credentials.get(name, {})),
        )
        for name in BROKER_REQUIRED_CREDENTIALS
    ]
