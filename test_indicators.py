from app.data.instruments import get_instrument

def test_indian_instrument():
    x = get_instrument("reliance")
    assert x.provider_symbol == "RELIANCE.NS"
    assert x.exchange == "NSE"
