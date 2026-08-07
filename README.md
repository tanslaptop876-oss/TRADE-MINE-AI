# TradeMind AI

AI-powered trading decision-support platform focused on Indian markets.

## Project goals

- Market data ingestion and validation
- Technical and fundamental analysis
- AI-assisted BUY / HOLD / SELL decision support
- Risk management and position sizing
- Backtesting and performance metrics
- Paper trading and portfolio management
- Web dashboard for analysis and monitoring

## Repository structure

```text
app/
  services/       # market data, indicators, decisions, risk, backtesting
  __init__.py

dashboard/        # dashboard application
sample_data/      # small datasets for development/tests
tests/            # automated tests
.github/workflows/ # CI
requirements.txt
```

## Development setup

Python 3.12+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Status

The project is currently in the cleanup/foundation stage. Changes are developed on feature branches and merged through pull requests before reaching `main`.

## Disclaimer

TradeMind AI is a software project for research, analysis, backtesting, and decision support. It does not guarantee investment returns and should not be treated as financial advice.
