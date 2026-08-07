from dataclasses import dataclass

from app.services.assets import AssetRegistry
from app.services.decision import DecisionEngine
from app.services.indicators import add_indicators
from app.services.paper_trading import PaperBroker
from app.services.paper_signal import execute_decision_signal
from app.services.risk import RiskEngine


@dataclass
class TradingPipeline:
    broker: PaperBroker
    registry: AssetRegistry
    risk_per_trade: float = 0.01

    def run(self, *, symbol: str, candles: list[dict]) -> dict:
        asset = self.registry.get(symbol)
        df = add_indicators(candles)
        decision = DecisionEngine().evaluate(df)

        result = {
            "symbol": asset.symbol,
            "asset_class": asset.asset_class.value,
            "decision": decision.model_dump(),
            "risk": None,
            "execution": None,
        }

        if decision.action == "HOLD":
            result["execution"] = execute_decision_signal(
                self.broker,
                symbol=asset.symbol,
                action="HOLD",
                quantity=asset.lot_size,
                price=decision.entry,
            )
            return result

        risk = RiskEngine(self.risk_per_trade).size_position(
            capital=self.broker.account.cash,
            entry=decision.entry,
            stop=decision.stop_loss,
        )
        result["risk"] = risk

        quantity = int(risk["quantity"])
        quantity = (quantity // asset.lot_size) * asset.lot_size
        if quantity <= 0:
            result["execution"] = {
                "status": "skipped",
                "reason": "quantity_below_lot_size",
                "symbol": asset.symbol,
            }
            return result

        if decision.action == "SELL" and self.broker.account.positions.get(asset.symbol, 0) < quantity:
            result["execution"] = {
                "status": "skipped",
                "reason": "no_long_position_to_sell",
                "symbol": asset.symbol,
            }
            return result

        result["execution"] = execute_decision_signal(
            self.broker,
            symbol=asset.symbol,
            action=decision.action,
            quantity=quantity,
            price=decision.entry,
        )
        return result
