from sqlalchemy.orm import Session

from apps.api.app.db.models import Order, Position, TradePlan
from apps.api.app.schemas.execution_reconciliation import ExecutionDriftEvent, ReconciliationReport


class ExecutionStateMachineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def reconcile_trade_plan(self, trade_plan_id: int) -> ReconciliationReport:
        trade_plan = self.db.get(TradePlan, trade_plan_id)
        if not trade_plan:
            raise ValueError("Trade plan no encontrado")

        orders = (
            self.db.query(Order)
            .filter(Order.trade_plan_id == trade_plan_id)
            .order_by(Order.created_at.asc())
            .all()
        )
        positions = (
            self.db.query(Position)
            .filter(Position.trade_plan_id == trade_plan_id)
            .order_by(Position.id.asc())
            .all()
        )

        open_positions = [position for position in positions if position.status == "open"]
        closed_positions = [position for position in positions if position.status == "closed"]
        filled_orders = [order for order in orders if order.status in {"filled", "partially_filled"}]

        drift_events: list[ExecutionDriftEvent] = []
        recommended_actions: list[str] = []

        if trade_plan.status in {"testnet_executed", "executed", "paper_executed"}:
            if not filled_orders:
                drift_events.append(
                    ExecutionDriftEvent(
                        event_type="missing_filled_order",
                        severity="critical",
                        message="Trade plan ejecutado sin órdenes fill registradas",
                    )
                )
                recommended_actions.append("replay_execution_audit")

            if not positions:
                drift_events.append(
                    ExecutionDriftEvent(
                        event_type="missing_position_association",
                        severity="critical",
                        message="Trade plan ejecutado sin posición asociada registrada",
                    )
                )
                recommended_actions.append("rebuild_position_state")
            elif not open_positions and closed_positions:
                drift_events.append(
                    ExecutionDriftEvent(
                        event_type="position_closed_but_plan_still_executed",
                        severity="warning",
                        message="La posición fue cerrada pero el trade plan sigue en estado ejecutado",
                    )
                )
                recommended_actions.append("sync_trade_plan_terminal_status")

        if len(open_positions) > 1:
            drift_events.append(
                ExecutionDriftEvent(
                    event_type="multiple_open_positions",
                    severity="warning",
                    message="Hay múltiples posiciones abiertas para un mismo trade plan",
                )
            )
            recommended_actions.append("consolidate_positions")

        if any(order.status == "rejected" for order in orders) and trade_plan.status in {"testnet_executed", "executed", "paper_executed"}:
            drift_events.append(
                ExecutionDriftEvent(
                    event_type="executed_with_rejected_orders",
                    severity="warning",
                    message="Trade plan marcado ejecutado con órdenes rechazadas en el historial",
                )
            )
            recommended_actions.append("review_order_rejections")

        healthy = len(drift_events) == 0
        if healthy:
            recommended_actions.append("none")

        return ReconciliationReport(
            trade_plan_id=trade_plan.id,
            trade_plan_status=trade_plan.status,
            healthy=healthy,
            order_count=len(orders),
            open_position_count=len(open_positions),
            filled_order_count=len(filled_orders),
            drift_events=drift_events,
            recommended_actions=recommended_actions,
        )
