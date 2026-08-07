from __future__ import annotations

from typing import Any, Callable, Mapping

from app.services.broker_adapters import BrokerCredentials
from app.services.read_only_broker import ReadOnlyBrokerAdapter, build_read_only_adapter


HttpGet = Callable[..., Any]


class UpstoxReadOnlyClient:
    quote_url = "https://api.upstox.com/v2/market-quote/quotes"
    funds_url = "https://api.upstox.com/v2/user/get-funds-and-margin"

    def __init__(self, *, access_token: str, request: HttpGet):
        self.access_token = access_token
        self.request = request

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

    def quote(self, *, symbol: str) -> Mapping[str, Any]:
        response = self.request(
            "GET",
            self.quote_url,
            headers=self.headers,
            params={"instrument_key": symbol},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def funds(self) -> Mapping[str, Any]:
        response = self.request(
            "GET",
            self.funds_url,
            headers=self.headers,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


def build_upstox_read_only_adapter(
    credentials: BrokerCredentials,
    request: HttpGet,
) -> ReadOnlyBrokerAdapter:
    if credentials.broker != "upstox":
        raise ValueError("upstox credentials required")
    if not credentials.configured:
        raise ValueError(f"upstox credentials are incomplete: {credentials.missing_fields()}")

    client = UpstoxReadOnlyClient(
        access_token=credentials.values["access_token"],
        request=request,
    )
    return build_read_only_adapter(
        name="upstox",
        credentials=credentials,
        quote_call=client.quote,
        funds_call=client.funds,
    )
