from app.services.risk import RiskEngine

def test_position_size():
    result = RiskEngine(0.01).size_position(100000, 100, 95)
    assert result["risk_amount"] == 1000
    assert result["quantity"] == 200
