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

## Paper-validation observability

Read-only endpoints expose paper-validation health without enabling broker dispatch:

- `GET /v1/paper/metrics` — aggregate health, thresholds, and recent snapshots
- `GET /v1/paper/history?limit=20` — bounded restart-safe validation history
- `GET /v1/observability/dashboard` — dashboard-ready metrics, alerts, and safety state

History defaults to `data/paper_validation_history.jsonl`. Set
`PAPER_VALIDATION_HISTORY_PATH` to use another local path. Retention defaults to
10,000 valid records and can be configured with
`PAPER_VALIDATION_HISTORY_MAX_RECORDS`. Compaction uses an atomic file replace,
and malformed JSONL records are skipped during recovery. Generated history files
are ignored by Git.

Internal alert lifecycle endpoints support acknowledgement and resolution without
sending outbound notifications:

- `GET /v1/observability/alerts`
- `POST /v1/observability/alerts/{code}/acknowledge`
- `POST /v1/observability/alerts/{code}/resolve`

Alert state defaults to `data/paper_alert_journal.json` and can be configured
with `PAPER_ALERT_JOURNAL_PATH`. Resolved alerts use a run-based cooldown;
outbound delivery remains disabled.

Structured alert lifecycle audit events are available from
`GET /v1/observability/audit`. Audit storage defaults to
`data/observability_audit.jsonl` and can be configured with
`OBSERVABILITY_AUDIT_PATH`. Token, password, secret, authorization, API-key,
and broker-token fields are recursively redacted before persistence.

See [the v1.8 plan](docs/V1_8_PLAN.md) for the next observability milestones.
Real broker dispatch remains disabled.

## Status

The project is currently in the cleanup/foundation stage. Changes are developed on feature branches and merged through pull requests before reaching `main`.

## Disclaimer

TradeMind AI is a software project for research, analysis, backtesting, and decision support. It does not guarantee investment returns and should not be treated as financial advice.
