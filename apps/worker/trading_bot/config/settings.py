from dataclasses import dataclass


@dataclass
class WorkerSettings:
    symbols: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    timeframes: tuple[str, ...] = ("5m", "15m", "1h")
    paper_trading: bool = True
    max_account_risk_pct: float = 5.0
    api_base_url: str = "http://127.0.0.1:8000"
    seed_capital_usdt: float = 1000.0
