from pydantic import BaseModel, Field
from datetime import datetime

class OHLCV(BaseModel):
    timestamp: datetime
    symbol: str
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)

class BacktestConfig(BaseModel):
    initial_capital: float = Field(default=100000, gt=0)
    risk_per_trade: float = Field(default=0.01, gt=0, lt=0.1)
    fee_rate: float = Field(default=0.0005, ge=0)
    slippage_rate: float = Field(default=0.0002, ge=0)
    train_ratio: float = Field(default=0.7, gt=0.5, lt=0.95)
