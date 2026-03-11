import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    symbols: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    timeframes: tuple[str, ...] = ("5m", "15m", "1h")
    paper_trading: bool = True
    max_account_risk_pct: float = 5.0
    api_base_url: str = "http://127.0.0.1:8000"
    seed_capital_usdt: float = 1000.0
    default_signal_timeframe: str = "15m"
    signal_snapshot_limit: int = 200
    strict_symbol_failures: bool = False

    @field_validator("symbols", "timeframes", mode="before")
    @classmethod
    def parse_tuple_env(cls, value: object):
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise ValueError("lista de símbolos/timeframes no puede estar vacía")
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, (list, tuple)):
                    return tuple(str(item).strip() for item in parsed if str(item).strip())
            except json.JSONDecodeError:
                pass
            return tuple(item.strip() for item in raw.split(",") if item.strip())
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
