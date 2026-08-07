# TradeMind AI

Modular AI-powered trading decision-support platform for Indian markets.

## MVP / v0.3 foundation
- Market-data abstraction
- Technical indicators: EMA, RSI, MACD, ATR
- Transparent decision engine with confidence/evidence
- Risk-based position sizing
- Backtesting baseline with fee/slippage
- FastAPI backend
- Streamlit dashboard
- Unit tests + GitHub Actions

## Architecture
Market Data -> Technical Engine -> Decision Engine -> Risk Engine -> Backtest/Paper Trade -> API/Dashboard

## Quick start
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

Dashboard:
```bash
streamlit run dashboard/app.py
```

The included CSV provider lets you test without broker credentials. For live Indian-market data, implement a provider for your chosen broker/data vendor. Never commit API keys.

This is a decision-support system, not a guarantee of returns. Validate with out-of-sample data and paper trading before risking capital.
