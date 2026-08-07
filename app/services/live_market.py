from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class LiveQuote:
    instrument_key: str
    ltp: float
    timestamp: datetime
    close: float | None = None

    def age_seconds(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        ts = self.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return max(0.0, (now - ts).total_seconds())

    def assert_fresh(self, max_age_seconds: float = 10.0, now: datetime | None = None) -> None:
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        if self.age_seconds(now) > max_age_seconds:
            raise ValueError("stale live market quote")


@dataclass(frozen=True)
class UpstoxV3Config:
    access_token: str

    def __post_init__(self):
        if not self.access_token.strip():
            raise ValueError("Upstox access token is required")

    @property
    def authorize_url(self) -> str:
        return "https://api.upstox.com/v3/feed/market-data-feed/authorize"

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }


def normalize_upstox_ltpc(payload: dict[str, Any], instrument_key: str) -> LiveQuote:
    feeds = payload.get("feeds") or {}
    feed = feeds.get(instrument_key) or {}
    ltpc = feed.get("ltpc") or feed.get("fullFeed", {}).get("marketFF", {}).get("ltpc") or {}

    if "ltp" not in ltpc or "ltt" not in ltpc:
        raise ValueError(f"missing LTPC data for {instrument_key}")

    ltp = float(ltpc["ltp"])
    if ltp <= 0:
        raise ValueError("live LTP must be positive")

    raw_ts = int(ltpc["ltt"])
    timestamp = datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc)
    close = float(ltpc["cp"]) if ltpc.get("cp") is not None else None

    return LiveQuote(
        instrument_key=instrument_key,
        ltp=ltp,
        timestamp=timestamp,
        close=close,
    )


def can_submit_live_signal(*, market_status: str, quote: LiveQuote, max_age_seconds: float = 10.0) -> bool:
    if market_status != "NORMAL_OPEN":
        return False
    quote.assert_fresh(max_age_seconds=max_age_seconds)
    return True
