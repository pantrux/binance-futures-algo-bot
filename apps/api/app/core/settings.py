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
    paper_trading: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
