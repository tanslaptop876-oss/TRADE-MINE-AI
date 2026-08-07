class RiskEngine:
    def __init__(self, risk_per_trade: float = 0.01):
        self.risk_per_trade = risk_per_trade

    def size_position(self, capital: float, entry: float, stop: float):
        risk_amount = capital * self.risk_per_trade
        per_share_risk = abs(entry - stop)
        if per_share_risk <= 0:
            return {
                "risk_amount": risk_amount,
                "quantity": 0,
                "notional": 0,
                "reason": "Invalid stop distance"
            }
        quantity = int(risk_amount // per_share_risk)
        return {
            "risk_amount": round(risk_amount, 2),
            "per_share_risk": round(per_share_risk, 4),
            "quantity": quantity,
            "notional": round(quantity * entry, 2)
        }
