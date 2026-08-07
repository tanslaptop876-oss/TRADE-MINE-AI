from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.broker_gateway import BrokerAdapter, BrokerOrder


@dataclass
class ConfiguredBrokerAdapter(BrokerAdapter):
    name: str
    credentials_configured: bool = False

    def connection_status(self) -> dict[str, Any]:
        return {
            "broker": self.name,
            "configured": self.credentials_configured,
            "connected": False,
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
        raise self._not_connected()


def default_broker_adapters() -> list[ConfiguredBrokerAdapter]:
    return [
        ConfiguredBrokerAdapter("icici"),
        ConfiguredBrokerAdapter("zerodha"),
        ConfiguredBrokerAdapter("upstox"),
        ConfiguredBrokerAdapter("angelone"),
        ConfiguredBrokerAdapter("motilal_oswal"),
        ConfiguredBrokerAdapter("dhan"),
        ConfiguredBrokerAdapter("fyers"),
    ]
