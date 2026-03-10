from sqlalchemy.orm import Session

from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan


class PaperTradingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute_trade_plan(self, trade_plan_id: int) -> dict:
        trade_plan = self.db.get(TradePlan, trade_plan_id)
        if not trade_plan:
            raise ValueError("Trade plan no encontrado")
        if trade_plan.status != "approved":
            risk_event = RiskEvent(
                trade_plan_id=trade_plan.id,
                event_type="paper_execution_blocked",
                severity="warning",
                message=f"Intento de ejecución bloqueado para trade plan con estado {trade_plan.status}",
            )
            self.db.add(risk_event)
            self.db.commit()
            return {"executed": False, "reason": "trade_plan_not_approved"}

        stop_distance = abs(trade_plan.entry_price - trade_plan.stop_loss)
        quantity = 0 if stop_distance == 0 else round((trade_plan.capital_usdt * (trade_plan.applied_risk_pct / 100)) / stop_distance, 6)

        order = Order(
            trade_plan_id=trade_plan.id,
            external_order_id=f"paper-{trade_plan.id}",
            symbol=trade_plan.symbol,
            side=trade_plan.side,
            order_type="market",
            status="filled",
            price=trade_plan.entry_price,
            quantity=quantity,
            executed_quantity=quantity,
            is_testnet=True,
        )
        position = Position(
            trade_plan_id=trade_plan.id,
            symbol=trade_plan.symbol,
            side=trade_plan.side,
            quantity=quantity,
            entry_price=trade_plan.entry_price,
            mark_price=trade_plan.entry_price,
            unrealized_pnl=0,
            leverage=1,
            status="open",
            is_testnet=True,
        )
        trade_plan.status = "paper_executed"
        self.db.add_all([order, position, trade_plan])
        self.db.commit()
        self.db.refresh(order)
        self.db.refresh(position)
        return {"executed": True, "order_id": order.id, "position_id": position.id}
