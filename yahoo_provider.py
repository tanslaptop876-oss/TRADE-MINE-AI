INDIAN_SYMBOLS = {
    "NIFTY50": {"exchange": "NSE", "segment": "INDEX"},
    "BANKNIFTY": {"exchange": "NSE", "segment": "INDEX"},
    "FINNIFTY": {"exchange": "NSE", "segment": "INDEX"},
}

def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()
