from app import main


class FakePipeline:
    def __init__(self, *, broker, registry, risk_per_trade):
        self.broker = broker

    def run(self, *, symbol: str, candles: list[dict]):
        return {
            "symbol": symbol,
            "asset_class": "equity",
            "decision": {"action": "HOLD"},
            "risk": None,
            "execution": {"status": "hold"},
        }


def test_paper_run_attaches_validation_report(monkeypatch):
    monkeypatch.setattr(main, "TradingPipeline", FakePipeline)

    req = main.PaperRunRequest(
        symbol="RELIANCE",
        candles=[
            main.Candle(
                timestamp="2026-08-08T09:15:00+05:30",
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000,
            )
        ],
        starting_cash=100000,
        risk_per_trade=0.01,
    )

    result = main.paper_run(req)

    assert result["account"]["cash"] == 100000.0
    assert result["account"]["trade_count"] == 0
    assert result["validation"]["valid"] is True
    assert result["validation"]["issues"] == []
