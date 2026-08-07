UPSTOX_NSE_INSTRUMENTS = {
    "RELIANCE": "NSE_EQ|INE002A01018",
    "TCS": "NSE_EQ|INE467B01029",
}


def upstox_instrument_key(symbol: str) -> str:
    key = symbol.strip().upper()
    if key not in UPSTOX_NSE_INSTRUMENTS:
        raise KeyError(f"No Upstox instrument mapping for {symbol}")
    return UPSTOX_NSE_INSTRUMENTS[key]
