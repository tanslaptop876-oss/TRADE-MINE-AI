from app.services.paper_trading import PaperBroker, PaperOrder, Side


def execute_decision_signal(
    broker: PaperBroker,
    *,
    symbol: str,
    action: str,
    quantity: int,
    price: float,
) -> dict:
    normalized = action.upper()
    if normalized == "HOLD":
        return {
            "status": "skipped",
            "reason": "hold_signal",
            "symbol": symbol.upper(),
        }
    if normalized not in {"BUY", "SELL"}:
        raise ValueError(f"unsupported decision action: {action}")

    return broker.execute(
        PaperOrder(
            symbol=symbol,
            side=Side(normalized),
            quantity=quantity,
            price=price,
        )
    )
