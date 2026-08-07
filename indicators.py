from fastapi import APIRouter, HTTPException
from app.data.instruments import INDIAN_INSTRUMENTS
from app.data.yahoo_provider import YahooFinanceProvider

router = APIRouter(prefix="/v1/market-data", tags=["market-data"])

@router.get("/instruments")
def instruments():
    return [
        {
            "symbol": x.symbol,
            "provider_symbol": x.provider_symbol,
            "exchange": x.exchange,
            "segment": x.segment,
            "name": x.name,
        }
        for x in INDIAN_INSTRUMENTS.values()
    ]

@router.get("/history/{symbol}")
def history(symbol: str, start: str, end: str, interval: str = "1d", cache: bool = True):
    try:
        provider = YahooFinanceProvider()
        df = (
            provider.history_cached(symbol, start, end, interval)
            if cache else provider.history(symbol, start, end, interval)
        )
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "rows": df.to_dict(orient="records"),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
