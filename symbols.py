from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    default_capital: float = float(os.getenv("DEFAULT_CAPITAL", "100000"))
    max_risk_per_trade: float = float(os.getenv("MAX_RISK_PER_TRADE", "0.01"))
    max_portfolio_risk: float = float(os.getenv("MAX_PORTFOLIO_RISK", "0.05"))
    fee_rate: float = float(os.getenv("BACKTEST_FEE_RATE", "0.0005"))
    slippage_rate: float = float(os.getenv("BACKTEST_SLIPPAGE_RATE", "0.0002"))

settings = Settings()
