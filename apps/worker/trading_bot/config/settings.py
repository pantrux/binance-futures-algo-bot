import json

from pydantic import ValidationInfo, field_validator
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
    signal_strategy: str = "hybrid"
    signal_strategy_symbols: tuple[str, ...] = ()
    runtime_mode: str = "oneshot"
    poll_interval_seconds: float = 30.0
    max_cycles: int = 0
    strict_symbol_failures: bool = False
    testnet_execution_enabled: bool = False
    testnet_global_kill_switch: bool = False
    testnet_kill_switch_symbols: tuple[str, ...] = ()
    testnet_fallback_to_paper: bool = True

    @field_validator("symbols", "timeframes", "testnet_kill_switch_symbols", "signal_strategy_symbols", mode="before")
    @classmethod
    def parse_tuple_env(cls, value: object, info: ValidationInfo):
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                if info.field_name == "signal_strategy_symbols":
                    return ()
                raise ValueError("lista de símbolos/timeframes no puede estar vacía")
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, (list, tuple)):
                    if not all(isinstance(item, str) for item in parsed):
                        raise ValueError("todos los elementos de la lista deben ser strings")
                    result = tuple(item.strip() for item in parsed if item.strip())
                    if not result:
                        raise ValueError("lista de símbolos/timeframes no puede estar vacía")
                    return result
                raise ValueError(f"se esperaba una lista JSON, se recibió {type(parsed).__name__}")
            except json.JSONDecodeError:
                if raw.startswith("[") or raw.startswith("{"):
                    raise ValueError(
                        "valor con apariencia de JSON inválido; usa JSON válido o CSV sin corchetes"
                    )
            result = tuple(item.strip() for item in raw.split(",") if item.strip())
            if not result:
                raise ValueError("lista de símbolos/timeframes no puede estar vacía")
            return result
        return value

    @field_validator("runtime_mode")
    @classmethod
    def validate_runtime_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"oneshot", "loop"}:
            raise ValueError("runtime_mode debe ser 'oneshot' o 'loop'")
        return normalized

    @field_validator("signal_strategy")
    @classmethod
    def validate_signal_strategy(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"hybrid", "ema_rsi_baseline"}:
            raise ValueError("signal_strategy debe ser 'hybrid' o 'ema_rsi_baseline'")
        return normalized

    @field_validator("poll_interval_seconds")
    @classmethod
    def validate_poll_interval_seconds(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("poll_interval_seconds debe ser > 0")
        return value

    @field_validator("max_cycles")
    @classmethod
    def validate_max_cycles(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_cycles debe ser >= 0")
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
