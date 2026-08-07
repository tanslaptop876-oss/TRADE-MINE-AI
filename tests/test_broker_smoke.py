from app.services.broker_gateway import BrokerAdapter, BrokerOrder
from app.services.broker_smoke import run_broker_smoke_test


class HealthyAdapter(BrokerAdapter):
    name = "healthy"

    def connection_status(self):
        return {"broker": self.name, "connected": True}

    def quote(self, symbol: str):
        return {"symbol": symbol, "ltp": 100.0}

    def positions(self):
        return [{"symbol": "RELIANCE", "quantity": 1}]

    def funds(self):
        return {"available": 50000.0}

    def place_order(self, order: BrokerOrder):
        raise PermissionError("disabled")


class BrokenFundsAdapter(HealthyAdapter):
    name = "broken"

    def funds(self):
        raise RuntimeError("funds unavailable")


def test_smoke_test_reports_all_checks_when_healthy():
    result = run_broker_smoke_test(HealthyAdapter(), symbol="RELIANCE")
    assert result["connected"] is True
    assert result["checks"]["quote"]["ok"] is True
    assert result["checks"]["funds"]["ok"] is True
    assert result["checks"]["positions"]["ok"] is True


def test_smoke_test_isolates_individual_failures():
    result = run_broker_smoke_test(BrokenFundsAdapter(), symbol="RELIANCE")
    assert result["connected"] is False
    assert result["checks"]["quote"]["ok"] is True
    assert result["checks"]["positions"]["ok"] is True
    assert result["checks"]["funds"]["ok"] is False
    assert result["checks"]["funds"]["error_type"] == "RuntimeError"
