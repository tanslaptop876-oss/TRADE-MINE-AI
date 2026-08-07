def indian_equity_symbol(symbol: str, exchange: str = "NSE") -> str:
    """Convert a plain Indian equity ticker to a Yahoo Finance symbol."""
    clean = symbol.strip().upper()
    if not clean:
        raise ValueError("symbol is required")

    exchange = exchange.strip().upper()
    suffixes = {"NSE": ".NS", "BSE": ".BO"}
    if exchange not in suffixes:
        raise ValueError("exchange must be NSE or BSE")

    if clean.endswith((".NS", ".BO")):
        return clean
    return f"{clean}{suffixes[exchange]}"
