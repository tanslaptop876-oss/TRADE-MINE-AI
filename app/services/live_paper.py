from app.services.live_market import LiveQuote, can_submit_live_signal
from app.services.paper_signal import execute_decision_signal
from app.services.paper_trading import PaperBroker


def execute_live_quote_on_paper(
    broker: PaperBroker,
    *,
    symbol: str,
    action: str,
    quantity: int,
    quote: LiveQuote,
    market_status: str,
    max_age_seconds: float = 10.0,
) -> dict:
    """Validate a real-time quote, then route the signal to paper execution only."""
    if not can_submit_live_signal(
        market_status=market_status,
        quote=quote,
        max_age_seconds=max_age_seconds,
    ):
        return {
            "status": "skipped",
            "reason": "market_not_open",
            "symbol": symbol.upper(),
        }

    return execute_decision_signal(
        broker,
        symbol=symbol,
        action=action,
        quantity=quantity,
        price=quote.ltp,
    )
