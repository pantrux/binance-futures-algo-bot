from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.schemas.dashboard_command_center import (
    DashboardCommandCenterOrder,
    DashboardCommandCenterPosition,
    DashboardCommandCenterResponse,
    DashboardCommandCenterRiskEvent,
    DashboardCommandCenterShadowRun,
    DashboardCommandCenterSummary,
    DashboardCommandCenterTradePlan,
)
from apps.api.app.services.shadow_run_reporting_service import ShadowRunReportingService


class DashboardCommandCenterService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self) -> DashboardCommandCenterResponse:
        summary = DashboardCommandCenterSummary(
            trade_plans_total=self.db.scalar(select(func.count()).select_from(TradePlan)) or 0,
            approved_trade_plans=self.db.scalar(
                select(func.count()).select_from(TradePlan).where(TradePlan.status == "approved")
            )
            or 0,
            paper_executed_trade_plans=self.db.scalar(
                select(func.count()).select_from(TradePlan).where(TradePlan.status == "paper_executed")
            )
            or 0,
            testnet_executed_trade_plans=self.db.scalar(
                select(func.count()).select_from(TradePlan).where(TradePlan.status == "testnet_executed")
            )
            or 0,
            open_positions=self.db.scalar(
                select(func.count()).select_from(Position).where(Position.status == "open")
            )
            or 0,
            risk_events_total=self.db.scalar(select(func.count()).select_from(RiskEvent)) or 0,
        )

        shadow_run_summary = ShadowRunReportingService(self.db).build_summary(window_days=30)
        shadow_run = DashboardCommandCenterShadowRun(
            shadow_run_duration_days=shadow_run_summary.shadow_run_duration_days,
            paper_executed_trade_plans=shadow_run_summary.paper_executed_trade_plans,
            testnet_executed_trade_plans=shadow_run_summary.testnet_executed_trade_plans,
            compared_pairs=shadow_run_summary.compared_pairs,
            unmatched_paper=shadow_run_summary.unmatched_paper,
            unmatched_testnet=shadow_run_summary.unmatched_testnet,
            testnet_orders_total=shadow_run_summary.testnet_orders_total,
            testnet_orders_filled=shadow_run_summary.testnet_orders_filled,
            testnet_fill_rate_pct=shadow_run_summary.testnet_fill_rate_pct,
            avg_testnet_slippage_bps=shadow_run_summary.avg_testnet_slippage_bps,
            critical_risk_events_7d=shadow_run_summary.critical_risk_events_7d,
            warning_risk_events_7d=shadow_run_summary.warning_risk_events_7d,
        )

        recent_trade_plans = [
            DashboardCommandCenterTradePlan(
                id=plan.id,
                symbol=plan.symbol,
                side=plan.side,
                market_regime=plan.market_regime,
                aggregate_score=plan.aggregate_score,
                applied_risk_pct=plan.applied_risk_pct,
                max_position_notional=plan.max_position_notional,
                status=plan.status,
                created_at=plan.created_at,
            )
            for plan in self.db.query(TradePlan).order_by(desc(TradePlan.created_at)).limit(12).all()
        ]

        recent_orders = [
            DashboardCommandCenterOrder(
                id=order.id,
                trade_plan_id=order.trade_plan_id,
                symbol=order.symbol,
                side=order.side,
                venue=order.venue,
                status=order.status,
                price=order.price,
                quantity=order.quantity,
                executed_quantity=order.executed_quantity,
                created_at=order.created_at,
            )
            for order in self.db.query(Order).order_by(desc(Order.created_at)).limit(12).all()
        ]

        open_positions = [
            DashboardCommandCenterPosition(
                id=position.id,
                trade_plan_id=position.trade_plan_id,
                symbol=position.symbol,
                side=position.side,
                quantity=position.quantity,
                entry_price=position.entry_price,
                mark_price=position.mark_price,
                unrealized_pnl=position.unrealized_pnl,
                leverage=position.leverage,
                status=position.status,
                opened_at=position.opened_at,
            )
            for position in self.db.query(Position)
            .filter(Position.status == "open")
            .order_by(desc(Position.opened_at))
            .limit(12)
            .all()
        ]

        recent_risk_events = [
            DashboardCommandCenterRiskEvent(
                id=event.id,
                trade_plan_id=event.trade_plan_id,
                event_type=event.event_type,
                severity=event.severity,
                message=event.message,
                created_at=event.created_at,
            )
            for event in self.db.query(RiskEvent).order_by(desc(RiskEvent.created_at)).limit(12).all()
        ]

        return DashboardCommandCenterResponse(
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            shadow_run=shadow_run,
            recent_trade_plans=recent_trade_plans,
            recent_orders=recent_orders,
            open_positions=open_positions,
            recent_risk_events=recent_risk_events,
        )
