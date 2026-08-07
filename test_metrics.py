# TradeMind AI v0.3 — Indian Market Data Layer

## Goal
Create a provider-agnostic data layer that can consume Indian-market historical data without coupling the strategy engine to one vendor.

## Included
- Indian instrument master for initial development symbols.
- Yahoo Finance development adapter using NSE notation such as `RELIANCE.NS`.
- Local CSV caching.
- OHLCV validation.
- Data-quality reporting.
- Market-data API endpoints.
- Lightweight weekday calendar fallback.

## Important
The Yahoo adapter is for development/research. It is not a guarantee of exchange-grade real-time data, corporate-action completeness, or execution-grade timestamps.

Before live/paper deployment, replace or supplement it with a licensed broker/exchange data feed and a proper Indian exchange holiday/calendar service.

## API examples
GET `/v1/market-data/instruments`

GET `/v1/market-data/history/RELIANCE?start=2025-01-01&end=2026-01-01&interval=1d`

## Next milestone
v0.4:
- realistic Indian transaction-cost model
- walk-forward backtesting
- portfolio-level risk
- paper-trading ledger
- broker adapter interface
