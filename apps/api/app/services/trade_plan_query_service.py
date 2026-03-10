from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.db.models import TradePlan
from apps.api.app.schemas.trade_plan_read import TradePlanRead


class TradePlanQueryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_trade_plans(self, limit: int = 20) -> list[TradePlanRead]:
        rows = self.db.scalars(select(TradePlan).order_by(TradePlan.created_at.desc()).limit(limit)).all()
        return [
            TradePlanRead(
                id=row.id,
                symbol=row.symbol,
                side=row.side,
                timeframe=row.timeframe,
                market_regime=row.market_regime,
                aggregate_score=row.aggregate_score,
                applied_risk_pct=row.applied_risk_pct,
                max_position_notional=row.max_position_notional,
                status=row.status,
                outline_url=row.outline_url,
                created_at=row.created_at,
            )
            for row in rows
        ]
