from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class BrokerMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


@dataclass(frozen=True)
class BrokerOrder:
    symbol: str
    side: str
    quantity: int
    order_type: str = "MARKET"
    price: float | None = None

    def __post_init__(self):
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if self.side.upper() not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


class BrokerAdapter(ABC):
    name: str

    @abstractmethod
    def connection_status(self) -> dict[str, Any]: ...

    @abstractmethod
    def quote(self, symbol: str) -> dict[str, Any]: ...

    @abstractmethod
    def positions(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def funds(self) -> dict[str, Any]: ...

    @abstractmethod
    def place_order(self, order: BrokerOrder) -> dict[str, Any]: ...


class BrokerGateway:
    def __init__(self, mode: BrokerMode = BrokerMode.PAPER):
        self.mode = mode
        self._adapters: dict[str, BrokerAdapter] = {}

    def register(self, adapter: BrokerAdapter) -> None:
        key = adapter.name.strip().lower()
        if not key:
            raise ValueError("broker adapter name is required")
        self._adapters[key] = adapter

    def brokers(self) -> list[str]:
        return sorted(self._adapters)

    def get(self, name: str) -> BrokerAdapter:
        key = name.strip().lower()
        if key not in self._adapters:
            raise KeyError(f"broker not registered: {name}")
        return self._adapters[key]

    def place_order(self, broker: str, order: BrokerOrder, *, live_confirmed: bool = False) -> dict[str, Any]:
        if self.mode is BrokerMode.LIVE and not live_confirmed:
            raise PermissionError("live order blocked: explicit confirmation required")
        return self.get(broker).place_order(order)
