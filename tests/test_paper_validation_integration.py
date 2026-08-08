from app.main import PaperRunRequest, paper_run
from app.services.pipeline import TradingPipeline


def test_paper_run_attaches_validation_report(monkeypatch):
    def fake_run(self, *, symbol, candles):
        return {
            "symbol": symbol,
            "asset_class": "equity",
            "decision": {"action": "HOLD"},
            "risk": None,
            "execution": {"status": "hold"},
        }

    monkeypatch.setattr(TradingPipeline, "run", fake_run)

    result = paper_run(
        PaperRunRequest(
            symbol="RELIANCE",
            candles=[],
            starting_cash=100000,
            risk_per_trade=0.01,
        )
    )

    assert result["account"] == {
        "cash": 100000,
        "positions": {},
        "trade_count": 0,
    }
    assert result["validation"]["valid"] is True
    assert result["validation"]["issues"] == []
    assert result["validation"]["checks"]["decision_present"] is True
    assert result["validation"]["checks"]["execution_present"] is True


def test_paper_run_validation_flags_inconsistent_trade(monkeypatch):
    def fake_run(self, *, symbol, candles):
        return {
            "symbol": symbol,
            "asset_class": "equity",
            "decision": {"action": "BUY"},
            "risk": None,
            "execution": {"status": "accepted"},
        }

    monkeypatch.setattr(TradingPipeline, "run", fake_run)

    result = paper_run(
        PaperRunRequest(
            symbol="RELIANCE",
            candles=[],
            starting_cash=100000,
            risk_per_trade=0.01,
        )
    )

    assert result["validation"]["valid"] is False
    assert "non-HOLD decision missing risk result" in result["validation"]["issues"]
