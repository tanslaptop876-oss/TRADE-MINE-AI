from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.audit_log import AuditLog
from app.services.broker_gateway import BrokerAdapter, BrokerOrder
from app.services.live_risk_guard import LiveRiskGuard


@dataclass
class ControlledLiveGateway:
    adapter: BrokerAdapter
    risk_guard: LiveRiskGuard
    audit_log: AuditLog

    def place_order(self, *, order_key: str, order: BrokerOrder, reference_price: float) -> dict[str, Any]:
        self.audit_log.record(
            "live_order_attempted",
            broker=self.adapter.name,
            order_key=order_key,
            symbol=order.symbol,
            side=order.side.upper(),
            quantity=order.quantity,
            reference_price=reference_price,
        )

        try:
            self.risk_guard.validate_order(
                order_key=order_key,
                quantity=order.quantity,
                price=reference_price,
            )
        except Exception as exc:
            self.audit_log.record(
                "live_order_blocked",
                broker=self.adapter.name,
                order_key=order_key,
                reason=str(exc),
                error_type=type(exc).__name__,
            )
            raise

        try:
            result = self.adapter.place_order(order)
        except Exception as exc:
            self.audit_log.record(
                "live_order_failed",
                broker=self.adapter.name,
                order_key=order_key,
                reason=str(exc),
                error_type=type(exc).__name__,
            )
            raise

        self.risk_guard.mark_order_accepted(order_key)
        self.audit_log.record(
            "live_order_sent",
            broker=self.adapter.name,
            order_key=order_key,
            result=result,
        )
        return result
