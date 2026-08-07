from dataclasses import dataclass
from enum import Enum


class AssetClass(str, Enum):
    EQUITY = "equity"
    COMMODITY = "commodity"
    CURRENCY = "currency"


@dataclass(frozen=True)
class AssetSpec:
    symbol: str
    asset_class: AssetClass
    exchange: str
    currency: str = "INR"
    lot_size: int = 1
    tick_size: float = 0.05

    def __post_init__(self):
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if self.lot_size <= 0:
            raise ValueError("lot_size must be positive")
        if self.tick_size <= 0:
            raise ValueError("tick_size must be positive")


class AssetRegistry:
    def __init__(self):
        self._assets: dict[str, AssetSpec] = {}

    def register(self, asset: AssetSpec) -> None:
        self._assets[asset.symbol.upper()] = asset

    def get(self, symbol: str) -> AssetSpec:
        key = symbol.upper()
        if key not in self._assets:
            raise KeyError(f"Unknown asset: {symbol}")
        return self._assets[key]

    def list(self, asset_class: AssetClass | None = None) -> list[AssetSpec]:
        assets = list(self._assets.values())
        if asset_class is not None:
            assets = [asset for asset in assets if asset.asset_class == asset_class]
        return sorted(assets, key=lambda asset: asset.symbol)


def default_india_registry() -> AssetRegistry:
    registry = AssetRegistry()
    for asset in [
        AssetSpec("RELIANCE", AssetClass.EQUITY, "NSE", lot_size=1, tick_size=0.05),
        AssetSpec("TCS", AssetClass.EQUITY, "NSE", lot_size=1, tick_size=0.05),
        AssetSpec("NATURALGAS", AssetClass.COMMODITY, "MCX", lot_size=1250, tick_size=0.10),
        AssetSpec("CRUDEOIL", AssetClass.COMMODITY, "MCX", lot_size=100, tick_size=1.0),
        AssetSpec("USDINR", AssetClass.CURRENCY, "NSE", lot_size=1000, tick_size=0.0025),
    ]:
        registry.register(asset)
    return registry
