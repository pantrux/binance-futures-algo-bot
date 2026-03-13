import time

from sqlalchemy.orm import Session

from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.services.binance_client import BinanceFuturesClient


class BinanceTestnetTradingService:
    def __init__(
        self,
        db: Session,
        binance_client: BinanceFuturesClient | None = None,
        *,
        execution_enabled: bool = False,
    ) -> None:
        self.db = db
        self.binance_client = binance_client or BinanceFuturesClient()
        self.execution_enabled = execution_enabled

    @staticmethod
    def _to_float(value: object, *, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    def _log_risk_event(self, *, trade_plan_id: int, event_type: str, severity: str, message: str) -> None:
        self.db.add(
            RiskEvent(
                trade_plan_id=trade_plan_id,
                event_type=event_type,
                severity=severity,
                message=message,
            )
        )

    async def execute_trade_plan(self, trade_plan_id: int) -> dict:
        trade_plan = self.db.get(TradePlan, trade_plan_id)
        if not trade_plan:
            raise ValueError("Trade plan no encontrado")

        if not self.execution_enabled:
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_disabled",
                severity="warning",
                message="Ejecución testnet deshabilitada por configuración",
            )
            self.db.commit()
            return {"executed": False, "reason": "testnet_execution_disabled"}

        if trade_plan.status != "approved":
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_blocked_not_approved",
                severity="warning",
                message=f"Intento de ejecución testnet bloqueado para trade plan con estado {trade_plan.status}",
            )
            self.db.commit()
            return {"executed": False, "reason": "trade_plan_not_approved"}

        stop_distance = abs(trade_plan.entry_price - trade_plan.stop_loss)
        quantity = 0.0 if stop_distance == 0 else round((trade_plan.capital_usdt * (trade_plan.applied_risk_pct / 100)) / stop_distance, 6)
        if quantity <= 0:
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_invalid_quantity",
                severity="critical",
                message="Cantidad inválida calculada para ejecución testnet",
            )
            self.db.commit()
            return {"executed": False, "reason": "invalid_quantity"}

        if trade_plan.side not in {"long", "short"}:
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_invalid_side",
                severity="critical",
                message=f"Valor de side inválido: {trade_plan.side!r}",
            )
            self.db.commit()
            return {"executed": False, "reason": "invalid_side"}

        side = "BUY" if trade_plan.side == "long" else "SELL"
        client_order_id = f"tp-{trade_plan.id}-{int(time.time() * 1000)}"

        try:
            exchange_order = await self.binance_client.place_market_order(
                symbol=trade_plan.symbol,
                side=side,
                quantity=quantity,
                client_order_id=client_order_id,
            )
        except Exception as exc:  # noqa: BLE001
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_error",
                severity="critical",
                message=f"Error en envío testnet: {exc}",
            )
            self.db.commit()
            return {"executed": False, "reason": "testnet_api_error"}

        exchange_price = self._to_float(exchange_order.get("avgPrice"), fallback=0.0)
        if exchange_price <= 0:
            exchange_price = trade_plan.entry_price

        executed_qty = self._to_float(exchange_order.get("executedQty"), fallback=quantity)
        if executed_qty <= 0:
            executed_qty = quantity
        order_status = str(exchange_order.get("status") or "FILLED").lower()
        external_order_id = str(exchange_order.get("orderId") or exchange_order.get("clientOrderId") or client_order_id)

        order = Order(
            trade_plan_id=trade_plan.id,
            venue="binance_futures_testnet",
            external_order_id=external_order_id,
            symbol=trade_plan.symbol,
            side=trade_plan.side,
            order_type="market",
            status=order_status,
            price=exchange_price,
            quantity=quantity,
            executed_quantity=executed_qty,
            is_testnet=True,
        )
        position = Position(
            trade_plan_id=trade_plan.id,
            symbol=trade_plan.symbol,
            side=trade_plan.side,
            quantity=executed_qty,
            entry_price=exchange_price,
            mark_price=exchange_price,
            unrealized_pnl=0,
            leverage=1,
            status="open",
            is_testnet=True,
        )

        trade_plan.status = "testnet_executed"
        self._log_risk_event(
            trade_plan_id=trade_plan.id,
            event_type="testnet_execution_submitted",
            severity="info",
            message=f"Orden testnet enviada: external_order_id={external_order_id}",
        )

        self.db.add_all([order, position, trade_plan])
        self.db.commit()
        self.db.refresh(order)
        self.db.refresh(position)

        return {
            "executed": True,
            "order_id": order.id,
            "position_id": position.id,
            "external_order_id": external_order_id,
            "reason": None,
        }
