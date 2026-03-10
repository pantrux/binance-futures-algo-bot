from datetime import UTC, datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.db.base import Base


class TradePlan(Base):
    __tablename__ = "trade_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    timeframe: Mapped[str] = mapped_column(String(16), index=True)
    market_regime: Mapped[str] = mapped_column(String(32), index=True)
    technical_score: Mapped[float] = mapped_column(Float)
    fundamental_score: Mapped[float] = mapped_column(Float)
    sentiment_score: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float)
    aggregate_score: Mapped[float] = mapped_column(Float, index=True)
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    capital_usdt: Mapped[float] = mapped_column(Float)
    applied_risk_pct: Mapped[float] = mapped_column(Float)
    max_position_notional: Mapped[float] = mapped_column(Float)
    thesis: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    outline_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_testnet: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
