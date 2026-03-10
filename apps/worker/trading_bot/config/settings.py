from dataclasses import dataclass


@dataclass
class WorkerSettings:
    symbols: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    timeframes: tuple[str, ...] = ("5m", "15m", "1h")
    paper_trading: bool = True
    max_account_risk_pct: float = 5.0
