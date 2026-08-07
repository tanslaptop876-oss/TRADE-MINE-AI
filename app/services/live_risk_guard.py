from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TradingMode(str, Enum):
    PAPER = "paper"
    SHADOW = "shadow"
    LIVE = "live"


@dataclass(frozen=True)
class LiveRiskLimits:
    max_order_notional: float = 5000.0
    max_daily_loss: float = 1000.0


@dataclass
class LiveRiskGuard:
    limits: LiveRiskLimits = field(default_factory=LiveRiskLimits)
    mode: TradingMode = TradingMode.PAPER
    kill_switch: bool = True
    live_confirmed: bool = False
    daily_pnl: float = 0.0
    _seen_order_keys: set[str] = field(default_factory=set)

    def readiness(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "kill_switch": self.kill_switch,
            "live_confirmed": self.live_confirmed,
            "daily_pnl": self.daily_pnl,
            "max_order_notional": self.limits.max_order_notional,
            "max_daily_loss": self.limits.max_daily_loss,
            "live_execution_allowed": self._live_gate_open(),
        }

    def _live_gate_open(self) -> bool:
        return (
            self.mode is TradingMode.LIVE
            and not self.kill_switch
            and self.live_confirmed
            and self.daily_pnl > -self.limits.max_daily_loss
        )

    def validate_order(
        self,
        *,
        order_key: str,
        quantity: float,
        price: float,
    ) -> None:
        if not self._live_gate_open():
            raise PermissionError("live execution gate is closed")
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        if quantity * price > self.limits.max_order_notional:
            raise PermissionError("max order notional exceeded")
        if order_key in self._seen_order_keys:
            raise PermissionError("duplicate order blocked")

    def mark_order_accepted(self, order_key: str) -> None:
        self._seen_order_keys.add(order_key)
