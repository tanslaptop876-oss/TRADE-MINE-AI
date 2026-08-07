from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ShadowOrderIntent:
    order_key: str
    broker: str
    symbol: str
    side: str
    quantity: float
    price: float

    @property
    def notional(self) -> float:
        return self.quantity * self.price


@dataclass
class ShadowExecutionRecorder:
    intents: list[ShadowOrderIntent] = field(default_factory=list)

    def record(self, intent: ShadowOrderIntent) -> dict[str, Any]:
        if intent.quantity <= 0 or intent.price <= 0:
            raise ValueError("quantity and price must be positive")
        if intent.side.upper() not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        self.intents.append(intent)
        return {
            "mode": "shadow",
            "executed": False,
            "broker_order_sent": False,
            "order_key": intent.order_key,
            "broker": intent.broker,
            "symbol": intent.symbol,
            "side": intent.side.upper(),
            "quantity": intent.quantity,
            "price": intent.price,
            "notional": intent.notional,
        }
