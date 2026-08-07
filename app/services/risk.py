class RiskEngine:
    def __init__(self, risk_per_trade: float = 0.01):
        if not 0 < risk_per_trade <= 0.05:
            raise ValueError("risk_per_trade must be between 0 and 0.05")
        self.risk_per_trade = risk_per_trade

    def size_position(self, capital: float, entry: float, stop: float):
        if capital <= 0:
            raise ValueError("capital must be positive")
        if entry <= 0:
            raise ValueError("entry must be positive")

        risk_amount = capital * self.risk_per_trade
        per_share_risk = abs(entry - stop)
        if per_share_risk <= 0:
            return {
                "risk_amount": round(risk_amount, 2),
                "per_share_risk": 0.0,
                "quantity": 0,
                "notional": 0.0,
                "reason": "Invalid stop distance",
            }

        risk_limited_qty = int(risk_amount // per_share_risk)
        capital_limited_qty = int(capital // entry)
        quantity = max(0, min(risk_limited_qty, capital_limited_qty))

        return {
            "risk_amount": round(risk_amount, 2),
            "per_share_risk": round(per_share_risk, 4),
            "quantity": quantity,
            "notional": round(quantity * entry, 2),
            "max_affordable_quantity": capital_limited_qty,
        }
