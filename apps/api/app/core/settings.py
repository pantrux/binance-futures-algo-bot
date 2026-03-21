from datetime import datetime, timezone

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Binance Futures Algo Bot API"
    environment: str = "development"
    outline_api_url: str = "http://192.168.0.8:3005/api"
    outline_api_token: str = ""
    default_capital_usdt: float = 1000.0
    max_account_risk_pct: float = 5.0
    risk_per_trade_pct: float = 1.0
    postgres_dsn: str = "postgresql+psycopg://tradingbot:change-me@localhost:5432/tradingbot"
    redis_url: str = "redis://localhost:6379/0"
    binance_futures_base_url: str = "https://testnet.binancefuture.com"
    binance_api_key: SecretStr = SecretStr("")
    binance_api_secret: SecretStr = SecretStr("")
    paper_trading: bool = True
    testnet_execution_enabled: bool = False
    metrics_api_key: SecretStr = SecretStr("")
    operational_cutover_at: datetime | None = None

    @field_validator("operational_cutover_at")
    @classmethod
    def normalize_operational_cutover_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("operational_cutover_at debe incluir timezone explícito")
        return value.astimezone(timezone.utc)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
