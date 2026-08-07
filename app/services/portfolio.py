from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class TradeRecord:
    symbol: str
    side: str
    quantity: int
    price: float
    realized_pnl: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PortfolioPosition:
    symbol: str
    quantity: int = 0
    average_price: float = 0.0
    realized_pnl: float = 0.0

    def buy(self, quantity: int, price: float) -> None:
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        new_quantity = self.quantity + quantity
        self.average_price = (
            (self.quantity * self.average_price) + (quantity * price)
        ) / new_quantity
        self.quantity = new_quantity

    def sell(self, quantity: int, price: float) -> float:
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        if quantity > self.quantity:
            raise ValueError("cannot sell more than the open position")
        pnl = (price - self.average_price) * quantity
        self.quantity -= quantity
        self.realized_pnl += pnl
        if self.quantity == 0:
            self.average_price = 0.0
        return pnl

    def unrealized_pnl(self, mark_price: float) -> float:
        if mark_price <= 0:
            raise ValueError("mark_price must be positive")
        return (mark_price - self.average_price) * self.quantity


class Portfolio:
    def __init__(self, starting_cash: float, max_position_pct: float = 0.25):
        if starting_cash <= 0:
            raise ValueError("starting_cash must be positive")
        if not 0 < max_position_pct <= 1:
            raise ValueError("max_position_pct must be between 0 and 1")
        self.starting_cash = float(starting_cash)
        self.cash = float(starting_cash)
        self.max_position_pct = max_position_pct
        self.positions: dict[str, PortfolioPosition] = {}
        self.journal: list[TradeRecord] = []

    def _position(self, symbol: str) -> PortfolioPosition:
        key = symbol.upper()
        return self.positions.setdefault(key, PortfolioPosition(key))

    def buy(self, symbol: str, quantity: int, price: float) -> TradeRecord:
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        cost = quantity * price
        if cost > self.cash:
            raise ValueError("insufficient cash")
        max_position_value = self.starting_cash * self.max_position_pct
        position = self._position(symbol)
        if (position.quantity * position.average_price) + cost > max_position_value:
            raise ValueError("position risk limit exceeded")
        position.buy(quantity, price)
        self.cash -= cost
        record = TradeRecord(symbol.upper(), "BUY", quantity, price)
        self.journal.append(record)
        return record

    def sell(self, symbol: str, quantity: int, price: float) -> TradeRecord:
        position = self._position(symbol)
        pnl = position.sell(quantity, price)
        self.cash += quantity * price
        record = TradeRecord(symbol.upper(), "SELL", quantity, price, pnl)
        self.journal.append(record)
        return record

    def realized_pnl(self) -> float:
        return sum(position.realized_pnl for position in self.positions.values())

    def unrealized_pnl(self, marks: dict[str, float]) -> float:
        total = 0.0
        for symbol, position in self.positions.items():
            if position.quantity and symbol in marks:
                total += position.unrealized_pnl(marks[symbol])
        return total

    def equity(self, marks: dict[str, float]) -> float:
        market_value = sum(
            position.quantity * marks.get(symbol, position.average_price)
            for symbol, position in self.positions.items()
        )
        return self.cash + market_value

    def summary(self, marks: dict[str, float]) -> dict:
        return {
            "starting_cash": round(self.starting_cash, 2),
            "cash": round(self.cash, 2),
            "equity": round(self.equity(marks), 2),
            "realized_pnl": round(self.realized_pnl(), 2),
            "unrealized_pnl": round(self.unrealized_pnl(marks), 2),
            "open_positions": sum(1 for p in self.positions.values() if p.quantity > 0),
            "trades": len(self.journal),
        }
