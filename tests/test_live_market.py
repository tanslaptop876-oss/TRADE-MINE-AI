from datetime import datetime, timedelta, timezone

import pytest

from app.services.instruments import upstox_instrument_key
from app.services.live_market import LiveQuote, can_submit_live_signal, normalize_upstox_ltpc


def test_upstox_instrument_mapping():
    assert upstox_instrument_key("reliance") == "NSE_EQ|INE002A01018"
    assert upstox_instrument_key("TCS") == "NSE_EQ|INE467B01029"


def test_normalize_upstox_ltpc():
    payload = {
        "feeds": {
            "NSE_EQ|INE002A01018": {
                "ltpc": {"ltp": 1425.5, "ltt": 1786109400000, "cp": 1410.0}
            }
        }
    }
    quote = normalize_upstox_ltpc(payload, "NSE_EQ|INE002A01018")
    assert quote.ltp == 1425.5
    assert quote.close == 1410.0
    assert quote.timestamp.tzinfo is not None


def test_live_gate_accepts_fresh_open_market_quote():
    now = datetime.now(timezone.utc)
    quote = LiveQuote("NSE_EQ|INE002A01018", 1425.5, now)
    assert can_submit_live_signal(market_status="NORMAL_OPEN", quote=quote, max_age_seconds=10)


def test_live_gate_rejects_closed_market():
    now = datetime.now(timezone.utc)
    quote = LiveQuote("NSE_EQ|INE002A01018", 1425.5, now)
    assert not can_submit_live_signal(market_status="CLOSED", quote=quote)


def test_live_gate_rejects_stale_quote():
    quote = LiveQuote(
        "NSE_EQ|INE002A01018",
        1425.5,
        datetime.now(timezone.utc) - timedelta(seconds=30),
    )
    with pytest.raises(ValueError, match="stale"):
        can_submit_live_signal(market_status="NORMAL_OPEN", quote=quote, max_age_seconds=10)
