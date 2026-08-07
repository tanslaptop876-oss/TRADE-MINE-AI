from __future__ import annotations

from typing import Any, Mapping, Protocol

from app.services.broker_adapters import BrokerCredentials
from app.services.read_only_broker import ReadOnlyBrokerAdapter, build_read_only_adapter


class IciciReadSdk(Protocol):
    def get_quotes(self, *, stock_code: str) -> Mapping[str, Any]: ...

    def get_funds(self) -> Mapping[str, Any]: ...

    def get_portfolio_positions(self) -> Mapping[str, Any] | list[Mapping[str, Any]]: ...


class IciciReadOnlyClient:
    def __init__(self, sdk: IciciReadSdk):
        self.sdk = sdk

    def quote(self, *, symbol: str) -> Mapping[str, Any]:
        return self.sdk.get_quotes(stock_code=symbol)

    def funds(self) -> Mapping[str, Any]:
        return self.sdk.get_funds()

    def positions(self) -> list[dict[str, Any]]:
        payload = self.sdk.get_portfolio_positions()
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        if isinstance(payload, Mapping):
            data = payload.get("data", [])
            if isinstance(data, list):
                return [dict(item) for item in data]
        return []


def build_icici_read_only_adapter(
    credentials: BrokerCredentials,
    sdk: IciciReadSdk,
) -> ReadOnlyBrokerAdapter:
    if credentials.broker != "icici":
        raise ValueError("icici credentials required")
    if not credentials.configured:
        raise ValueError(f"icici credentials are incomplete: {credentials.missing_fields()}")

    client = IciciReadOnlyClient(sdk)
    return build_read_only_adapter(
        name="icici",
        credentials=credentials,
        quote_call=client.quote,
        funds_call=client.funds,
        positions_call=client.positions,
    )
