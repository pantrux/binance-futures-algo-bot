from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.schemas.dashboard_command_center import (
    DashboardCommandCenterOperationSnapshot,
    DashboardCommandCenterOrder,
    DashboardCommandCenterPosition,
    DashboardCommandCenterResponse,
    DashboardCommandCenterRiskEvent,
    DashboardCommandCenterShadowRun,
    DashboardCommandCenterSummary,
    DashboardCommandCenterTradePlan,
)
from apps.api.app.services.execution_state_machine_service import ExecutionStateMachineService
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

        recent_trade_plan_rows = self.db.query(TradePlan).order_by(desc(TradePlan.created_at)).limit(12).all()
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
            for plan in recent_trade_plan_rows
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

        recent_risk_events_rows = self.db.query(RiskEvent).order_by(desc(RiskEvent.created_at)).limit(12).all()
        recent_risk_events = [
            DashboardCommandCenterRiskEvent(
                id=event.id,
                trade_plan_id=event.trade_plan_id,
                event_type=event.event_type,
                severity=event.severity,
                message=event.message,
                created_at=event.created_at,
            )
            for event in recent_risk_events_rows
        ]

        operation_snapshots: list[DashboardCommandCenterOperationSnapshot] = []
        execution_state_machine = ExecutionStateMachineService(self.db)
        for plan in recent_trade_plan_rows:
            plan_orders = (
                self.db.query(Order)
                .filter(Order.trade_plan_id == plan.id)
                .order_by(desc(Order.created_at), desc(Order.id))
                .all()
            )
            plan_positions = (
                self.db.query(Position)
                .filter(Position.trade_plan_id == plan.id)
                .order_by(desc(Position.opened_at), desc(Position.id))
                .all()
            )
            latest_risk = (
                self.db.query(RiskEvent)
                .filter(RiskEvent.trade_plan_id == plan.id)
                .order_by(desc(RiskEvent.created_at), desc(RiskEvent.id))
                .first()
            )
            risk_event_count = (
                self.db.scalar(select(func.count()).select_from(RiskEvent).where(RiskEvent.trade_plan_id == plan.id))
                or 0
            )
            latest_order = plan_orders[0] if plan_orders else None
            latest_position = plan_positions[0] if plan_positions else None
            reconciliation = execution_state_machine.reconcile_loaded_trade_plan(
                plan,
                list(reversed(plan_orders)),
                list(reversed(plan_positions)),
            )
            primary_drift = reconciliation.drift_events[0] if reconciliation.drift_events else None

            operation_snapshots.append(
                DashboardCommandCenterOperationSnapshot(
                    trade_plan_id=plan.id,
                    symbol=plan.symbol,
                    side=plan.side,
                    status=plan.status,
                    market_regime=plan.market_regime,
                    aggregate_score=plan.aggregate_score,
                    entry_price=plan.entry_price,
                    stop_loss=plan.stop_loss,
                    take_profit=plan.take_profit,
                    applied_risk_pct=plan.applied_risk_pct,
                    max_position_notional=plan.max_position_notional,
                    latest_order_id=latest_order.id if latest_order else None,
                    latest_order_status=latest_order.status if latest_order else None,
                    latest_order_venue=latest_order.venue if latest_order else None,
                    latest_order_price=latest_order.price if latest_order else None,
                    latest_order_executed_quantity=latest_order.executed_quantity if latest_order else None,
                    latest_position_id=latest_position.id if latest_position else None,
                    latest_position_status=latest_position.status if latest_position else None,
                    latest_position_quantity=latest_position.quantity if latest_position else None,
                    latest_position_entry_price=latest_position.entry_price if latest_position else None,
                    latest_position_mark_price=latest_position.mark_price if latest_position else None,
                    latest_position_unrealized_pnl=latest_position.unrealized_pnl if latest_position else None,
                    reconciliation_healthy=reconciliation.healthy,
                    reconciliation_primary_severity=primary_drift.severity if primary_drift else None,
                    reconciliation_primary_event=primary_drift.event_type if primary_drift else None,
                    reconciliation_primary_message=primary_drift.message if primary_drift else None,
                    risk_event_count=risk_event_count,
                    latest_risk_severity=latest_risk.severity if latest_risk else None,
                    latest_risk_event_type=latest_risk.event_type if latest_risk else None,
                    latest_risk_message=latest_risk.message if latest_risk else None,
                    created_at=plan.created_at,
                )
            )

        return DashboardCommandCenterResponse(
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            shadow_run=shadow_run,
            operation_snapshots=operation_snapshots,
            recent_trade_plans=recent_trade_plans,
            recent_orders=recent_orders,
            open_positions=open_positions,
            recent_risk_events=recent_risk_events,
        )
