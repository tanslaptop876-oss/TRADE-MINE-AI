from dataclasses import dataclass, field
from enum import Enum

from app.services.assets import AssetRegistry


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class PaperOrder:
    symbol: str
    side: Side
    quantity: int
    price: float

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")


@dataclass
class PaperAccount:
    starting_cash: float = 100000.0
    cash: float = field(init=False)
    positions: dict[str, int] = field(default_factory=dict)
    trades: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if self.starting_cash <= 0:
            raise ValueError("starting_cash must be positive")
        self.cash = float(self.starting_cash)


class PaperBroker:
    def __init__(self, account: PaperAccount, registry: AssetRegistry):
        self.account = account
        self.registry = registry

    def execute(self, order: PaperOrder) -> dict:
        asset = self.registry.get(order.symbol)
        if order.quantity % asset.lot_size != 0:
            raise ValueError(f"quantity must be a multiple of lot_size={asset.lot_size}")

        symbol = asset.symbol.upper()
        value = order.quantity * order.price
        current_qty = self.account.positions.get(symbol, 0)

        if order.side == Side.BUY:
            if value > self.account.cash:
                raise ValueError("insufficient paper cash")
            self.account.cash -= value
            self.account.positions[symbol] = current_qty + order.quantity
        else:
            if order.quantity > current_qty:
                raise ValueError("paper account cannot sell more than current position")
            self.account.cash += value
            remaining = current_qty - order.quantity
            if remaining:
                self.account.positions[symbol] = remaining
            else:
                self.account.positions.pop(symbol, None)

        trade = {
            "symbol": symbol,
            "asset_class": asset.asset_class.value,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": order.price,
            "value": round(value, 2),
            "cash_after": round(self.account.cash, 2),
        }
        self.account.trades.append(trade)
        return trade

    def equity(self, prices: dict[str, float]) -> float:
        position_value = 0.0
        for symbol, quantity in self.account.positions.items():
            if symbol not in prices:
                raise ValueError(f"missing mark price for {symbol}")
            position_value += quantity * prices[symbol]
        return round(self.account.cash + position_value, 2)
