from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from apps.api.app.core.settings import settings
from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.schemas.dashboard_command_center import (
    DashboardCommandCenterOperationSnapshot,
    DashboardCommandCenterOrder,
    DashboardCommandCenterPosition,
    DashboardCommandCenterReconciliationDrift,
    DashboardCommandCenterResponse,
    DashboardCommandCenterRiskEvent,
    DashboardCommandCenterShadowRun,
    DashboardCommandCenterSummary,
    DashboardCommandCenterTimelineEntry,
    DashboardCommandCenterTradePlan,
)
from apps.api.app.services.execution_state_machine_service import ExecutionStateMachineService
from apps.api.app.services.shadow_run_reporting_service import ShadowRunReportingService


class DashboardCommandCenterService:
    PLAN_ORDER_HISTORY_LIMIT = 50
    PLAN_POSITION_HISTORY_LIMIT = 50
    PLAN_RISK_EVENT_HISTORY_LIMIT = 100

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _trade_plan_tone(status: str) -> str:
        return "ok" if status in {"approved", "paper_executed", "testnet_executed"} else "neutral"

    @staticmethod
    def _order_tone(status: str) -> str:
        if status in {"filled", "partially_filled"}:
            return "ok"
        if status in {"rejected", "expired", "canceled", "cancelled"}:
            return "danger"
        return "warn"

    @staticmethod
    def _position_tone(status: str) -> str:
        return "ok" if status == "open" else "neutral"

    @staticmethod
    def _risk_tone(severity: str) -> str:
        if severity == "critical":
            return "danger"
        if severity == "warning":
            return "warn"
        return "neutral"

    @staticmethod
    def _reconciliation_tone(severity: str) -> str:
        if severity == "critical":
            return "danger"
        if severity == "warning":
            return "warn"
        return "neutral"

    @staticmethod
    def _timeline_anchor(*timestamps: datetime | None) -> datetime:
        candidates = [timestamp for timestamp in timestamps if timestamp is not None]
        if not candidates:
            return datetime.now(timezone.utc)
        return max(candidates)

    @staticmethod
    def _serialize_order(order: Order) -> DashboardCommandCenterOrder:
        return DashboardCommandCenterOrder(
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

    @staticmethod
    def _serialize_position(position: Position) -> DashboardCommandCenterPosition:
        return DashboardCommandCenterPosition(
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

    @staticmethod
    def _serialize_risk_event(event: RiskEvent) -> DashboardCommandCenterRiskEvent:
        return DashboardCommandCenterRiskEvent(
            id=event.id,
            trade_plan_id=event.trade_plan_id,
            event_type=event.event_type,
            severity=event.severity,
            message=event.message,
            context=event.context_json or {},
            created_at=event.created_at,
        )

    def build(self) -> DashboardCommandCenterResponse:
        cutover = settings.operational_cutover_at

        trade_plans_base = select(func.count()).select_from(TradePlan)
        approved_trade_plans_query = select(func.count()).select_from(TradePlan).where(TradePlan.status == "approved")
        paper_executed_query = select(func.count()).select_from(TradePlan).where(TradePlan.status == "paper_executed")
        testnet_executed_query = select(func.count()).select_from(TradePlan).where(TradePlan.status == "testnet_executed")
        open_positions_query = select(func.count()).select_from(Position).where(Position.status == "open")
        risk_events_query = select(func.count()).select_from(RiskEvent)

        if cutover is not None:
            trade_plans_base = trade_plans_base.where(TradePlan.created_at >= cutover)
            approved_trade_plans_query = approved_trade_plans_query.where(TradePlan.created_at >= cutover)
            paper_executed_query = paper_executed_query.where(TradePlan.created_at >= cutover)
            testnet_executed_query = testnet_executed_query.where(TradePlan.created_at >= cutover)
            open_positions_query = open_positions_query.where(Position.opened_at >= cutover)
            risk_events_query = risk_events_query.where(RiskEvent.created_at >= cutover)

        summary = DashboardCommandCenterSummary(
            trade_plans_total=self.db.scalar(trade_plans_base) or 0,
            approved_trade_plans=self.db.scalar(approved_trade_plans_query) or 0,
            paper_executed_trade_plans=self.db.scalar(paper_executed_query) or 0,
            testnet_executed_trade_plans=self.db.scalar(testnet_executed_query) or 0,
            open_positions=self.db.scalar(open_positions_query) or 0,
            risk_events_total=self.db.scalar(risk_events_query) or 0,
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

        recent_trade_plans_query = self.db.query(TradePlan)
        if cutover is not None:
            recent_trade_plans_query = recent_trade_plans_query.filter(TradePlan.created_at >= cutover)
        recent_trade_plan_rows = recent_trade_plans_query.order_by(desc(TradePlan.created_at)).limit(12).all()
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

        recent_orders_query = self.db.query(Order)
        if cutover is not None:
            recent_orders_query = recent_orders_query.filter(Order.created_at >= cutover)
        recent_orders = [
            self._serialize_order(order)
            for order in recent_orders_query.order_by(desc(Order.created_at)).limit(12).all()
        ]

        open_positions_query = self.db.query(Position).filter(Position.status == "open")
        if cutover is not None:
            open_positions_query = open_positions_query.filter(Position.opened_at >= cutover)
        open_positions = [
            self._serialize_position(position)
            for position in open_positions_query.order_by(desc(Position.opened_at)).limit(12).all()
        ]

        recent_risk_events_query = self.db.query(RiskEvent)
        if cutover is not None:
            recent_risk_events_query = recent_risk_events_query.filter(RiskEvent.created_at >= cutover)
        recent_risk_events_rows = recent_risk_events_query.order_by(desc(RiskEvent.created_at)).limit(12).all()
        recent_risk_events = [self._serialize_risk_event(event) for event in recent_risk_events_rows]

        operation_snapshots: list[DashboardCommandCenterOperationSnapshot] = []
        timeline: list[DashboardCommandCenterTimelineEntry] = []
        execution_state_machine = ExecutionStateMachineService(self.db)

        for plan in recent_trade_plan_rows:
            plan_orders_query = self.db.query(Order).filter(Order.trade_plan_id == plan.id)
            plan_positions_query = self.db.query(Position).filter(Position.trade_plan_id == plan.id)
            plan_risk_events_query = self.db.query(RiskEvent).filter(RiskEvent.trade_plan_id == plan.id)
            if cutover is not None:
                plan_orders_query = plan_orders_query.filter(Order.created_at >= cutover)
                plan_positions_query = plan_positions_query.filter(Position.opened_at >= cutover)
                plan_risk_events_query = plan_risk_events_query.filter(RiskEvent.created_at >= cutover)

            plan_orders = (
                plan_orders_query.order_by(desc(Order.created_at), desc(Order.id))
                .limit(self.PLAN_ORDER_HISTORY_LIMIT)
                .all()
            )
            plan_positions = (
                plan_positions_query.order_by(desc(Position.opened_at), desc(Position.id))
                .limit(self.PLAN_POSITION_HISTORY_LIMIT)
                .all()
            )
            plan_risk_events = (
                plan_risk_events_query.order_by(desc(RiskEvent.created_at), desc(RiskEvent.id))
                .limit(self.PLAN_RISK_EVENT_HISTORY_LIMIT)
                .all()
            )

            latest_order = plan_orders[0] if plan_orders else None
            latest_position = plan_positions[0] if plan_positions else None
            latest_risk = plan_risk_events[0] if plan_risk_events else None
            risk_event_count = (
                self.db.query(func.count(RiskEvent.id))
                .filter(RiskEvent.trade_plan_id == plan.id)
                .scalar()
                or 0
            )

            reconciliation = execution_state_machine.reconcile_loaded_trade_plan(
                plan,
                list(reversed(plan_orders)),
                list(reversed(plan_positions)),
            )
            primary_drift = reconciliation.drift_events[0] if reconciliation.drift_events else None

            plan_timeline: list[DashboardCommandCenterTimelineEntry] = [
                DashboardCommandCenterTimelineEntry(
                    trade_plan_id=plan.id,
                    symbol=plan.symbol,
                    entity_kind="trade_plan",
                    event_kind=plan.status,
                    tone=self._trade_plan_tone(plan.status),
                    title=f"Trade plan #{plan.id} · {plan.symbol}",
                    detail=f"{plan.side} · score {plan.aggregate_score:.2f} · regime {plan.market_regime}",
                    occurred_at=plan.created_at,
                )
            ]

            for order in plan_orders:
                plan_timeline.append(
                    DashboardCommandCenterTimelineEntry(
                        trade_plan_id=plan.id,
                        symbol=plan.symbol,
                        entity_kind="order",
                        event_kind=order.status,
                        tone=self._order_tone(order.status),
                        title=f"Orden #{order.id} · {order.venue}",
                        detail=f"status {order.status} · px {order.price:.2f} · exec {order.executed_quantity:.3f}/{order.quantity:.3f}",
                        occurred_at=order.created_at,
                    )
                )

            for position in plan_positions:
                plan_timeline.append(
                    DashboardCommandCenterTimelineEntry(
                        trade_plan_id=plan.id,
                        symbol=plan.symbol,
                        entity_kind="position",
                        event_kind=position.status,
                        tone=self._position_tone(position.status),
                        title=f"Posición #{position.id} · {position.symbol}",
                        detail=f"{position.side} · qty {position.quantity:.3f} · pnl {position.unrealized_pnl:.2f}",
                        occurred_at=position.opened_at,
                    )
                )

            for event in plan_risk_events:
                plan_timeline.append(
                    DashboardCommandCenterTimelineEntry(
                        trade_plan_id=plan.id,
                        symbol=plan.symbol,
                        entity_kind="risk_event",
                        event_kind=event.event_type,
                        tone=self._risk_tone(event.severity),
                        title=f"Riesgo · {event.event_type}",
                        detail=event.message,
                        occurred_at=event.created_at,
                    )
                )

            if primary_drift:
                plan_timeline.append(
                    DashboardCommandCenterTimelineEntry(
                        trade_plan_id=plan.id,
                        symbol=plan.symbol,
                        entity_kind="reconciliation",
                        event_kind=primary_drift.event_type,
                        tone=self._reconciliation_tone(primary_drift.severity),
                        title=f"Reconcile · {primary_drift.event_type}",
                        detail=primary_drift.message,
                        occurred_at=self._timeline_anchor(
                            latest_order.created_at if latest_order else None,
                            latest_position.opened_at if latest_position else None,
                            latest_risk.created_at if latest_risk else None,
                            plan.created_at,
                        ),
                    )
                )

            plan_timeline.sort(key=lambda item: item.occurred_at, reverse=True)
            timeline.extend(plan_timeline)

            operation_snapshots.append(
                DashboardCommandCenterOperationSnapshot(
                    trade_plan_id=plan.id,
                    symbol=plan.symbol,
                    side=plan.side,
                    status=plan.status,
                    timeframe=plan.timeframe,
                    market_regime=plan.market_regime,
                    technical_score=plan.technical_score,
                    fundamental_score=plan.fundamental_score,
                    sentiment_score=plan.sentiment_score,
                    confidence_score=plan.confidence_score,
                    aggregate_score=plan.aggregate_score,
                    thesis=plan.thesis,
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
                    reconciliation_order_count=reconciliation.order_count,
                    reconciliation_open_position_count=reconciliation.open_position_count,
                    reconciliation_filled_order_count=reconciliation.filled_order_count,
                    reconciliation_drift_events=[
                        DashboardCommandCenterReconciliationDrift(
                            event_type=event.event_type,
                            severity=event.severity,
                            message=event.message,
                        )
                        for event in reconciliation.drift_events
                    ],
                    reconciliation_recommended_actions=reconciliation.recommended_actions,
                    risk_event_count=risk_event_count,
                    latest_risk_severity=latest_risk.severity if latest_risk else None,
                    latest_risk_event_type=latest_risk.event_type if latest_risk else None,
                    latest_risk_message=latest_risk.message if latest_risk else None,
                    latest_risk_context=latest_risk.context_json if latest_risk and latest_risk.context_json else {},
                    order_history=[self._serialize_order(order) for order in plan_orders],
                    position_history=[self._serialize_position(position) for position in plan_positions],
                    risk_event_history=[self._serialize_risk_event(event) for event in plan_risk_events],
                    timeline_history=plan_timeline[:20],
                    created_at=plan.created_at,
                )
            )

        timeline.sort(key=lambda item: item.occurred_at, reverse=True)

        return DashboardCommandCenterResponse(
            generated_at=datetime.now(timezone.utc),
            operational_cutover_at=cutover,
            summary=summary,
            shadow_run=shadow_run,
            operation_snapshots=operation_snapshots,
            timeline=timeline[:20],
            recent_trade_plans=recent_trade_plans,
            recent_orders=recent_orders,
            open_positions=open_positions,
            recent_risk_events=recent_risk_events,
        )
