from app.services.paper_validation import validate_paper_result


def test_valid_hold_result_passes():
    result = {
        "decision": {"action": "HOLD"},
        "risk": None,
        "execution": {"status": "hold"},
    }
    account = {"cash": 100000.0, "positions": {}, "trade_count": 0}

    report = validate_paper_result(result, account)

    assert report.valid is True
    assert report.issues == []


def test_missing_risk_for_trade_action_fails():
    result = {
        "decision": {"action": "BUY"},
        "risk": None,
        "execution": {"status": "accepted"},
    }
    account = {"cash": 95000.0, "positions": {"RELIANCE": 1}, "trade_count": 1}

    report = validate_paper_result(result, account)

    assert report.valid is False
    assert "non-HOLD decision missing risk result" in report.issues


def test_negative_cash_is_flagged():
    result = {
        "decision": {"action": "BUY"},
        "risk": {"quantity": 1},
        "execution": {"status": "filled"},
    }
    account = {"cash": -1.0, "positions": {"RELIANCE": 1}, "trade_count": 1}

    report = validate_paper_result(result, account)

    assert report.valid is False
    assert "cash is negative or invalid" in report.issues


def test_unknown_execution_status_is_flagged():
    result = {
        "decision": {"action": "HOLD"},
        "risk": None,
        "execution": {"status": "mystery"},
    }
    account = {"cash": 100000.0, "positions": {}, "trade_count": 0}

    report = validate_paper_result(result, account)

    assert report.valid is False
    assert "unknown execution status: mystery" in report.issues
