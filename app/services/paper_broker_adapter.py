from __future__ import annotations

from typing import Any

from app.services.assets import AssetRegistry
from app.services.broker_gateway import BrokerAdapter, BrokerOrder
from app.services.paper_trading import PaperAccount, PaperBroker, PaperOrder, Side


class PaperBrokerAdapter(BrokerAdapter):
    name = "paper"

    def __init__(self, account: PaperAccount, registry: AssetRegistry):
        self.account = account
        self.broker = PaperBroker(account, registry)

    def connection_status(self) -> dict[str, Any]:
        return {"broker": self.name, "connected": True, "mode": "paper"}

    def quote(self, symbol: str) -> dict[str, Any]:
        raise NotImplementedError("paper adapter requires an external market-data provider for quotes")

    def positions(self) -> list[dict[str, Any]]:
        return [
            {"symbol": symbol, "quantity": quantity}
            for symbol, quantity in sorted(self.account.positions.items())
        ]

    def funds(self) -> dict[str, Any]:
        return {"cash": round(self.account.cash, 2), "starting_cash": round(self.account.starting_cash, 2)}

    def place_order(self, order: BrokerOrder) -> dict[str, Any]:
        return self.broker.execute(
            PaperOrder(
                symbol=order.symbol,
                side=Side(order.side.upper()),
                quantity=order.quantity,
                price=float(order.price) if order.price is not None else 0.0,
            )
        )
