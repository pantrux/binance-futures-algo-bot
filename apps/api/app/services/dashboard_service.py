from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.app.db.models import Position, RiskEvent, TradePlan
from apps.api.app.schemas.dashboard import DashboardSummary


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self) -> DashboardSummary:
        trade_plans_total = self.db.scalar(select(func.count()).select_from(TradePlan)) or 0
        approved_trade_plans = self.db.scalar(select(func.count()).select_from(TradePlan).where(TradePlan.status == 'approved')) or 0
        paper_executed_trade_plans = self.db.scalar(select(func.count()).select_from(TradePlan).where(TradePlan.status == 'paper_executed')) or 0
        open_positions = self.db.scalar(select(func.count()).select_from(Position).where(Position.status == 'open')) or 0
        risk_events_total = self.db.scalar(select(func.count()).select_from(RiskEvent)) or 0
        return DashboardSummary(
            trade_plans_total=trade_plans_total,
            approved_trade_plans=approved_trade_plans,
            paper_executed_trade_plans=paper_executed_trade_plans,
            open_positions=open_positions,
            risk_events_total=risk_events_total,
        )
