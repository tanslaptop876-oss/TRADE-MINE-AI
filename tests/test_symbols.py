import pytest

from app.services.symbols import indian_equity_symbol


def test_nse_symbol_mapping():
    assert indian_equity_symbol("reliance") == "RELIANCE.NS"
    assert indian_equity_symbol("TCS.NS") == "TCS.NS"


def test_bse_symbol_mapping():
    assert indian_equity_symbol("500325", "BSE") == "500325.BO"


def test_invalid_exchange():
    with pytest.raises(ValueError, match="NSE or BSE"):
        indian_equity_symbol("RELIANCE", "MCX")


def test_empty_symbol():
    with pytest.raises(ValueError, match="symbol is required"):
        indian_equity_symbol("   ")
