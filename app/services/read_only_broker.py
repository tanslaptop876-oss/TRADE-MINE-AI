from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from app.services.broker_adapters import BrokerCredentials, ConfiguredBrokerAdapter
from app.services.broker_gateway import BrokerOrder


ReadCall = Callable[..., Mapping[str, Any]]
PositionsCall = Callable[..., Sequence[Mapping[str, Any]]]


@dataclass
class ReadOnlyBrokerAdapter(ConfiguredBrokerAdapter):
    quote_call: ReadCall | None = None
    funds_call: ReadCall | None = None
    positions_call: PositionsCall | None = None

    def quote(self, symbol: str) -> dict[str, Any]:
        if not self.transport_connected or self.quote_call is None:
            raise self._not_connected()
        return dict(self.quote_call(symbol=symbol))

    def funds(self) -> dict[str, Any]:
        if not self.transport_connected or self.funds_call is None:
            raise self._not_connected()
        return dict(self.funds_call())

    def positions(self) -> list[dict[str, Any]]:
        if not self.transport_connected or self.positions_call is None:
            raise self._not_connected()
        return [dict(position) for position in self.positions_call()]

    def place_order(self, order: BrokerOrder) -> dict[str, Any]:
        raise PermissionError(f"{self.name} live orders are not enabled")


def build_read_only_adapter(
    *,
    name: str,
    credentials: BrokerCredentials,
    quote_call: ReadCall,
    funds_call: ReadCall,
    positions_call: PositionsCall | None = None,
) -> ReadOnlyBrokerAdapter:
    if not credentials.configured:
        raise ValueError(f"{name} credentials are incomplete: {credentials.missing_fields()}")
    return ReadOnlyBrokerAdapter(
        name=name,
        credentials=credentials,
        transport_connected=True,
        quote_call=quote_call,
        funds_call=funds_call,
        positions_call=positions_call,
    )
