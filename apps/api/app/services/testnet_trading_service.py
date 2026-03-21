import math
import time
from typing import Any

from sqlalchemy.orm import Session

from apps.api.app.db.models import Order, Position, RiskEvent, TradePlan
from apps.api.app.services.binance_client import BinanceFuturesClient


class BinanceTestnetTradingService:
    TERMINAL_ORDER_STATUSES = {"filled", "canceled", "expired", "rejected"}

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

    def _extract_fill_price(self, exchange_order: dict, *, fallback: float) -> float:
        avg_price = self._to_float(exchange_order.get("avgPrice"), fallback=0.0)
        if avg_price > 0:
            return avg_price

        status = str(exchange_order.get("status") or "").strip().lower()
        price = self._to_float(exchange_order.get("price"), fallback=0.0)
        if price > 0 and status in {"filled", "partially_filled"}:
            return price

        executed_qty = self._to_float(exchange_order.get("executedQty"), fallback=0.0)
        cum_quote = self._to_float(exchange_order.get("cumQuote"), fallback=0.0)
        if executed_qty > 0 and cum_quote > 0:
            return cum_quote / executed_qty

        return fallback

    def _resolve_exchange_order_ref(self, external_order_id: str | None) -> dict[str, int | str]:
        ref = str(external_order_id or "").strip()
        if not ref:
            raise ValueError("order external_order_id vacío para reconciliación")
        if ref.isdigit():
            return {"order_id": int(ref)}
        return {"client_order_id": ref}

    def _extract_fill_price_from_trades(self, trades: list[dict], *, fallback: float) -> float:
        total_qty = 0.0
        total_quote = 0.0
        for trade in trades:
            qty = self._to_float(trade.get("qty"), fallback=0.0)
            price = self._to_float(trade.get("price"), fallback=0.0)
            quote_qty = self._to_float(trade.get("quoteQty"), fallback=0.0)
            if qty <= 0:
                continue
            total_qty += qty
            total_quote += quote_qty if quote_qty > 0 else price * qty
        if total_qty > 0 and total_quote > 0:
            return total_quote / total_qty
        return fallback

    def _extract_executed_quantity_from_trades(self, trades: list[dict], *, fallback: float) -> float:
        total_qty = 0.0
        for trade in trades:
            total_qty += self._to_float(trade.get("qty"), fallback=0.0)
        return total_qty if total_qty > 0 else fallback

    def _prefer_refresh_value(self, key: str, original: object, refreshed: object) -> bool:
        """Decide si un campo refrescado debe sobreescribir el valor original.

        Regla general:
        - Nunca pisar con None/"".
        - Para valores numéricos: evitar degradar un valor positivo existente con 0.
        - Para strings no numéricos: ser conservador y evitar downgrades (especialmente en status).
        """
        if refreshed in (None, ""):
            return False
        if original in (None, ""):
            return True

        if key == "status":
            original_status = str(original or "").strip().lower()
            refreshed_status = str(refreshed or "").strip().lower()
            # Progreso típico de Binance (no exhaustivo pero suficiente para prevenir downgrades obvios)
            rank = {
                "pending_new": 0,
                "new": 0,
                "partially_filled": 1,
                # Estados terminales negativos: pueden ocurrir tras parcial fill, pero no deben pisar un FILLED.
                "canceled": 2,
                "expired": 2,
                "rejected": 2,
                "filled": 3,
            }
            original_known = original_status in rank
            refreshed_known = refreshed_status in rank
            if not original_known and not refreshed_known:
                return False
            unknown_rank = -1
            return rank.get(refreshed_status, unknown_rank) >= rank.get(original_status, unknown_rank)

        try:
            refreshed_value = float(refreshed)
            original_value = float(original)
        except (TypeError, ValueError):
            # Si no es numérico (e.g. strings varios), no pisar a menos que el original sea vacío.
            return False
        if refreshed_value <= 0 < original_value:
            return False
        return True

    async def _confirm_exchange_order(
        self,
        *,
        trade_plan_id: int | None,
        symbol: str,
        exchange_order: dict,
        client_order_id: str,
    ) -> dict:
        order_id = exchange_order.get("orderId")
        status = str(exchange_order.get("status") or "").strip().lower()
        avg_price = self._to_float(exchange_order.get("avgPrice"), fallback=0.0)
        executed_qty = self._to_float(exchange_order.get("executedQty"), fallback=0.0)
        terminal_no_fill = status in {"canceled", "expired", "rejected"} and executed_qty <= 0
        needs_refresh = not terminal_no_fill and (
            avg_price <= 0
            or executed_qty <= 0
            or status in {"new", "pending_new"}
        )
        get_order = getattr(self.binance_client, "get_order", None)
        if not needs_refresh or not callable(get_order):
            return exchange_order
        try:
            refreshed = await get_order(
                symbol=symbol,
                order_id=int(order_id) if order_id else None,
                client_order_id=client_order_id,
            )
        except Exception as exc:  # noqa: BLE001
            if trade_plan_id is not None:
                self._log_risk_event(
                    trade_plan_id=trade_plan_id,
                    event_type="testnet_order_refresh_failed",
                    severity="warning",
                    message=f"No fue posible refrescar la orden testnet: {exc}",
                    context={
                        "symbol": symbol,
                        "order_id": order_id,
                        "client_order_id": client_order_id,
                        "exception_type": type(exc).__name__,
                    },
                )
            return exchange_order
        if not isinstance(refreshed, dict) or not refreshed:
            return exchange_order
        merged = dict(exchange_order)
        for key, value in refreshed.items():
            if self._prefer_refresh_value(key, merged.get(key), value):
                merged[key] = value
        return merged

    @staticmethod
    def _normalize_order_status(raw_status: object, *, executed_qty: float, requested_qty: float) -> str:
        status = str(raw_status or "new").strip().lower()
        if executed_qty <= 0:
            return status
        if status in {"filled", "partially_filled"}:
            return status
        tolerance = max(1e-12, requested_qty * 1e-9)
        return "filled" if executed_qty >= max(0.0, requested_qty - tolerance) else "partially_filled"

    @staticmethod
    def _round_to_step(quantity: float, step_size: float) -> float:
        if step_size <= 0:
            return quantity
        rounded = math.floor(quantity / step_size) * step_size
        precision = max(0, min(12, int(round(-math.log10(step_size)))))
        return round(rounded, precision)

    @staticmethod
    def _derive_protection_prices(
        *,
        side: str,
        planned_entry: float,
        planned_stop_loss: float,
        planned_take_profit: float,
        exchange_price: float,
        mark_price: float,
    ) -> tuple[float, float]:
        reference_mark = mark_price if mark_price > 0 else exchange_price
        stop_distance = abs(planned_entry - planned_stop_loss)
        take_profit_distance = abs(planned_take_profit - planned_entry)
        safety_buffer = max(abs(reference_mark) * 0.001, 1e-8)

        if side == "long":
            stop_price = min(exchange_price, reference_mark) - max(stop_distance, safety_buffer)
            take_profit_price = max(exchange_price, reference_mark) + max(take_profit_distance, safety_buffer)
        else:
            stop_price = max(exchange_price, reference_mark) + max(stop_distance, safety_buffer)
            take_profit_price = min(exchange_price, reference_mark) - max(take_profit_distance, safety_buffer)

        return stop_price, take_profit_price

    @staticmethod
    def _round_price_to_tick(price: float, tick_size: float, *, mode: str) -> float:
        if tick_size <= 0:
            return price
        scaled = price / tick_size
        if mode == "down":
            rounded = math.floor(scaled) * tick_size
        elif mode == "up":
            rounded = math.ceil(scaled) * tick_size
        else:
            rounded = round(scaled) * tick_size
        precision = max(0, min(12, int(round(-math.log10(tick_size)))))
        return round(rounded, precision)

    def _log_risk_event(
        self,
        *,
        trade_plan_id: int,
        event_type: str,
        severity: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.db.add(
            RiskEvent(
                trade_plan_id=trade_plan_id,
                event_type=event_type,
                severity=severity,
                message=message,
                context_json=context or {},
            )
        )

    @staticmethod
    def _get_exit_side(position_side: str) -> str:
        return "SELL" if position_side == "long" else "BUY"

    def _resolve_local_exit_levels(self, *, trade_plan: TradePlan) -> tuple[float, float]:
        effective_event = (
            self.db.query(RiskEvent)
            .filter(RiskEvent.trade_plan_id == trade_plan.id, RiskEvent.event_type == "testnet_protection_orders_failed")
            .order_by(RiskEvent.created_at.desc(), RiskEvent.id.desc())
            .first()
        )
        if not effective_event:
            return trade_plan.stop_loss, trade_plan.take_profit

        context = effective_event.context_json or {}
        stop_loss = self._to_float(context.get("effective_stop_loss"), fallback=trade_plan.stop_loss)
        take_profit = self._to_float(context.get("effective_take_profit"), fallback=trade_plan.take_profit)
        return stop_loss, take_profit

    @staticmethod
    def _detect_local_exit_trigger(*, trade_plan: TradePlan, mark_price: float, stop_loss: float, take_profit: float) -> str | None:
        if mark_price <= 0:
            return None
        if trade_plan.side == "long":
            if mark_price <= stop_loss:
                return "stop_market"
            if mark_price >= take_profit:
                return "take_profit_market"
            return None
        if mark_price >= stop_loss:
            return "stop_market"
        if mark_price <= take_profit:
            return "take_profit_market"
        return None

    async def _place_protection_orders(
        self,
        *,
        trade_plan: TradePlan,
        exit_side: str,
        external_order_id: str,
        exchange_price: float,
        mark_price: float,
    ) -> tuple[Order | None, Order | None, str | None]:
        stop_client_order_id = f"sl-{trade_plan.id}-{int(time.time() * 1000)}"
        take_profit_client_order_id = f"tpx-{trade_plan.id}-{int(time.time() * 1000)}"
        stop_price, take_profit_price = self._derive_protection_prices(
            side=trade_plan.side,
            planned_entry=trade_plan.entry_price,
            planned_stop_loss=trade_plan.stop_loss,
            planned_take_profit=trade_plan.take_profit,
            exchange_price=exchange_price,
            mark_price=mark_price,
        )
        tick_size = 0.0
        get_symbol_tick_size = getattr(self.binance_client, "get_symbol_tick_size", None)
        if callable(get_symbol_tick_size):
            try:
                tick_size = await get_symbol_tick_size(trade_plan.symbol)
            except Exception:
                tick_size = 0.0

        if trade_plan.side == "long":
            stop_price = self._round_price_to_tick(stop_price, tick_size, mode="down")
            take_profit_price = self._round_price_to_tick(take_profit_price, tick_size, mode="up")
        else:
            stop_price = self._round_price_to_tick(stop_price, tick_size, mode="up")
            take_profit_price = self._round_price_to_tick(take_profit_price, tick_size, mode="down")

        try:
            stop_payload = await self.binance_client.place_stop_market_order(
                symbol=trade_plan.symbol,
                side=exit_side,
                stop_price=stop_price,
                client_order_id=stop_client_order_id,
            )
            take_profit_payload = await self.binance_client.place_take_profit_market_order(
                symbol=trade_plan.symbol,
                side=exit_side,
                stop_price=take_profit_price,
                client_order_id=take_profit_client_order_id,
            )
        except Exception as exc:  # noqa: BLE001
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_protection_orders_failed",
                severity="critical",
                message=f"No fue posible crear órdenes de protección testnet: {exc}",
                context={
                    "symbol": trade_plan.symbol,
                    "external_order_id": external_order_id,
                    "exception_type": type(exc).__name__,
                    "planned_stop_loss": trade_plan.stop_loss,
                    "planned_take_profit": trade_plan.take_profit,
                    "effective_stop_loss": stop_price,
                    "effective_take_profit": take_profit_price,
                    "exchange_price": exchange_price,
                    "mark_price": mark_price,
                },
            )
            return None, None, "protection_orders_failed"

        stop_order = Order(
            trade_plan_id=trade_plan.id,
            venue="binance_futures_testnet",
            external_order_id=str(stop_payload.get("orderId") or stop_payload.get("clientOrderId") or stop_client_order_id),
            symbol=trade_plan.symbol,
            side=trade_plan.side,
            order_type="stop_market",
            status=str(stop_payload.get("status") or "new").strip().lower(),
            price=stop_price,
            quantity=0.0,
            executed_quantity=0.0,
            is_testnet=True,
        )
        take_profit_order = Order(
            trade_plan_id=trade_plan.id,
            venue="binance_futures_testnet",
            external_order_id=str(
                take_profit_payload.get("orderId") or take_profit_payload.get("clientOrderId") or take_profit_client_order_id
            ),
            symbol=trade_plan.symbol,
            side=trade_plan.side,
            order_type="take_profit_market",
            status=str(take_profit_payload.get("status") or "new").strip().lower(),
            price=take_profit_price,
            quantity=0.0,
            executed_quantity=0.0,
            is_testnet=True,
        )
        self._log_risk_event(
            trade_plan_id=trade_plan.id,
            event_type="testnet_protection_orders_submitted",
            severity="info",
            message="Órdenes de protección testnet enviadas",
            context={
                "symbol": trade_plan.symbol,
                "external_order_id": external_order_id,
                "stop_order_id": stop_order.external_order_id,
                "take_profit_order_id": take_profit_order.external_order_id,
            },
        )
        return stop_order, take_profit_order, None

    async def sync_exit_orders(self, trade_plan_id: int) -> dict:
        if not self.execution_enabled:
            return {"synced": False, "reason": "testnet_execution_disabled"}

        trade_plan = self.db.get(TradePlan, trade_plan_id)
        if not trade_plan:
            raise ValueError("Trade plan no encontrado")
        if trade_plan.status == "testnet_closed":
            return {"synced": False, "reason": "trade_plan_already_closed"}

        position = (
            self.db.query(Position)
            .filter(Position.trade_plan_id == trade_plan_id)
            .filter(Position.status == "open")
            .filter(Position.is_testnet.is_(True))
            .order_by(Position.id.desc())
            .first()
        )
        if not position:
            return {"synced": False, "reason": "no_open_position"}

        protection_orders = (
            self.db.query(Order)
            .filter(Order.trade_plan_id == trade_plan_id)
            .filter(Order.order_type.in_(["stop_market", "take_profit_market"]))
            .filter(Order.is_testnet.is_(True))
            .order_by(Order.id.asc())
            .all()
        )
        if not protection_orders:
            get_position_risk = getattr(self.binance_client, "get_position_risk", None)
            if not callable(get_position_risk):
                return {"synced": False, "reason": "no_protection_orders"}
            try:
                position_risk = await get_position_risk(trade_plan.symbol)
            except Exception as exc:  # noqa: BLE001
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_local_exit_mark_price_unavailable",
                    severity="warning",
                    message=f"No fue posible evaluar salida local sin órdenes nativas: {exc}",
                    context={"symbol": trade_plan.symbol, "exception_type": type(exc).__name__},
                )
                self.db.commit()
                return {"synced": False, "reason": "local_exit_mark_price_unavailable"}

            mark_price = self._to_float((position_risk or {}).get("markPrice"), fallback=position.mark_price)
            if mark_price > 0:
                position.mark_price = mark_price
            effective_stop_loss, effective_take_profit = self._resolve_local_exit_levels(trade_plan=trade_plan)
            local_trigger = self._detect_local_exit_trigger(
                trade_plan=trade_plan,
                mark_price=position.mark_price,
                stop_loss=effective_stop_loss,
                take_profit=effective_take_profit,
            )
            if local_trigger is None:
                self.db.commit()
                return {"synced": True, "reason": "no_triggered_exit"}

            close_position_market = getattr(self.binance_client, "close_position_market", None)
            if not callable(close_position_market):
                return {"synced": False, "reason": "local_exit_close_unavailable"}

            client_order_id = f"lex-{trade_plan.id}-{int(time.time() * 1000)}"
            try:
                close_payload = await close_position_market(
                    symbol=trade_plan.symbol,
                    side=self._get_exit_side(position.side),
                    quantity=position.quantity,
                    client_order_id=client_order_id,
                )
            except Exception as exc:  # noqa: BLE001
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_local_exit_execution_failed",
                    severity="critical",
                    message=f"No fue posible ejecutar salida local sintética: {exc}",
                    context={
                        "symbol": trade_plan.symbol,
                        "triggered_order_type": local_trigger,
                        "mark_price": position.mark_price,
                        "effective_stop_loss": effective_stop_loss,
                        "effective_take_profit": effective_take_profit,
                        "exception_type": type(exc).__name__,
                    },
                )
                self.db.commit()
                return {"synced": False, "reason": "local_exit_execution_failed"}

            close_payload = await self._confirm_exchange_order(
                trade_plan_id=trade_plan.id,
                symbol=trade_plan.symbol,
                exchange_order=close_payload,
                client_order_id=client_order_id,
            )
            close_price = self._extract_fill_price(close_payload, fallback=position.mark_price)
            close_qty = self._to_float(close_payload.get("executedQty"), fallback=0.0)
            close_status = self._normalize_order_status(
                close_payload.get("status"),
                executed_qty=close_qty,
                requested_qty=position.quantity,
            )
            tolerance = max(1e-12, position.quantity * 1e-9)
            if close_status != "filled" and close_qty < max(0.0, position.quantity - tolerance):
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_local_exit_not_filled",
                    severity="critical",
                    message="La salida local sintética no quedó completamente ejecutada",
                    context={
                        "symbol": trade_plan.symbol,
                        "triggered_order_type": local_trigger,
                        "order_status": close_status,
                        "executed_quantity": close_qty,
                        "requested_quantity": position.quantity,
                        "effective_stop_loss": effective_stop_loss,
                        "effective_take_profit": effective_take_profit,
                    },
                )
                self.db.commit()
                return {"synced": False, "reason": "local_exit_not_filled"}
            position.status = "closed"
            position.mark_price = close_price
            position.unrealized_pnl = 0.0
            trade_plan.status = "testnet_closed"
            close_order = Order(
                trade_plan_id=trade_plan.id,
                venue="binance_futures_testnet",
                external_order_id=str(close_payload.get("orderId") or close_payload.get("clientOrderId") or client_order_id),
                symbol=trade_plan.symbol,
                side=trade_plan.side,
                order_type=local_trigger,
                status=close_status,
                price=close_price,
                quantity=position.quantity,
                executed_quantity=close_qty,
                is_testnet=True,
            )
            self.db.add(close_order)
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_local_exit_triggered",
                severity="warning",
                message=f"Salida local sintética ejecutada por {local_trigger} sin protección nativa disponible",
                context={
                    "symbol": trade_plan.symbol,
                    "triggered_order_type": local_trigger,
                    "mark_price": position.mark_price,
                    "effective_stop_loss": effective_stop_loss,
                    "effective_take_profit": effective_take_profit,
                    "external_order_id": close_order.external_order_id,
                },
            )
            self.db.commit()
            self.db.refresh(close_order)
            return {
                "synced": True,
                "reason": None,
                "triggered_order_type": local_trigger,
                "local_exit": True,
                "close_order_id": close_order.id,
            }

        triggered_order = None
        sibling_orders = []
        get_order = getattr(self.binance_client, "get_order", None)
        if not callable(get_order):
            return {"synced": False, "reason": "binance_get_order_unavailable"}

        refreshed_statuses: dict[int, str] = {}
        for order in protection_orders:
            try:
                refreshed = await get_order(
                    symbol=trade_plan.symbol,
                    **self._resolve_exchange_order_ref(order.external_order_id),
                )
            except Exception as exc:  # noqa: BLE001
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_exit_order_refresh_failed",
                    severity="warning",
                    message=f"No fue posible refrescar orden de protección: {exc}",
                    context={
                        "symbol": trade_plan.symbol,
                        "order_id": order.external_order_id,
                        "exception_type": type(exc).__name__,
                    },
                )
                self.db.commit()
                return {"synced": False, "reason": "exit_order_refresh_failed"}
            refreshed_statuses[order.id] = str(refreshed.get("status") or order.status).strip().lower()

        for order in protection_orders:
            refreshed_status = refreshed_statuses[order.id]
            order.status = refreshed_status
            if refreshed_status == "filled" and triggered_order is None:
                triggered_order = order
            else:
                sibling_orders.append(order)

        if triggered_order is None:
            self.db.commit()
            return {"synced": True, "reason": "no_triggered_exit"}

        position.status = "closed"
        trade_plan.status = "testnet_closed"
        self._log_risk_event(
            trade_plan_id=trade_plan.id,
            event_type="testnet_exit_order_filled",
            severity="info",
            message=f"Orden de salida ejecutada en testnet: {triggered_order.order_type}",
            context={
                "symbol": trade_plan.symbol,
                "triggered_order_id": triggered_order.external_order_id,
                "triggered_order_type": triggered_order.order_type,
            },
        )

        canceled_sibling = None
        cancel_order = getattr(self.binance_client, "cancel_order", None)
        live_sibling_orders = [
            sibling_order for sibling_order in sibling_orders if sibling_order.status not in self.TERMINAL_ORDER_STATUSES
        ]
        if live_sibling_orders and not callable(cancel_order):
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_exit_sibling_cancel_unavailable",
                severity="warning",
                message="No fue posible cancelar orden hermana: cancel_order no disponible en el cliente",
                context={
                    "symbol": trade_plan.symbol,
                    "sibling_order_ids": [order.external_order_id for order in live_sibling_orders],
                },
            )
        for sibling_order in live_sibling_orders:
            if not callable(cancel_order):
                continue
            try:
                await cancel_order(
                    symbol=trade_plan.symbol,
                    **self._resolve_exchange_order_ref(sibling_order.external_order_id),
                )
                sibling_order.status = "canceled"
                canceled_sibling = sibling_order.external_order_id
            except Exception as exc:  # noqa: BLE001
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_exit_sibling_cancel_failed",
                    severity="warning",
                    message=f"No fue posible cancelar la orden hermana: {exc}",
                    context={
                        "symbol": trade_plan.symbol,
                        "sibling_order_id": sibling_order.external_order_id,
                        "exception_type": type(exc).__name__,
                    },
                )

        self.db.commit()
        return {
            "synced": True,
            "reason": None,
            "triggered_order_type": triggered_order.order_type,
            "canceled_sibling_order_id": canceled_sibling,
        }

    async def sync_open_testnet_exits(self) -> dict:
        open_trade_plan_ids = [
            trade_plan_id
            for trade_plan_id, in (
                self.db.query(Position.trade_plan_id)
                .filter(Position.status == "open")
                .filter(Position.is_testnet.is_(True))
                .filter(Position.trade_plan_id.is_not(None))
                .distinct()
                .all()
            )
            if trade_plan_id is not None
        ]

        results: list[dict] = []
        for trade_plan_id in open_trade_plan_ids:
            try:
                result = await self.sync_exit_orders(int(trade_plan_id))
            except ValueError:
                continue
            except Exception as exc:  # noqa: BLE001
                self._log_risk_event(
                    trade_plan_id=int(trade_plan_id),
                    event_type="testnet_open_exits_sync_item_failed",
                    severity="warning",
                    message=f"Falló la sincronización de exits para trade plan {trade_plan_id}: {exc}",
                    context={
                        "trade_plan_id": int(trade_plan_id),
                        "exception_type": type(exc).__name__,
                    },
                )
                self.db.commit()
                results.append({
                    "trade_plan_id": int(trade_plan_id),
                    "synced": False,
                    "reason": "sync_item_failed",
                })
                continue
            results.append({"trade_plan_id": int(trade_plan_id), **result})

        triggered = sum(1 for item in results if item.get("triggered_order_type"))
        return {
            "synced": True,
            "open_trade_plan_count": len(open_trade_plan_ids),
            "checked_count": len(results),
            "triggered_count": triggered,
            "results": results,
        }

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
                context={"symbol": trade_plan.symbol, "status": trade_plan.status},
            )
            self.db.commit()
            return {"executed": False, "reason": "testnet_execution_disabled"}

        if trade_plan.status != "approved":
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_blocked_not_approved",
                severity="warning",
                message=f"Intento de ejecución testnet bloqueado para trade plan con estado {trade_plan.status}",
                context={"symbol": trade_plan.symbol, "status": trade_plan.status},
            )
            self.db.commit()
            return {"executed": False, "reason": "trade_plan_not_approved"}

        existing_open_position = (
            self.db.query(Position)
            .filter(Position.symbol == trade_plan.symbol)
            .filter(Position.side == trade_plan.side)
            .filter(Position.status == "open")
            .filter(Position.is_testnet.is_(True))
            .first()
        )
        if existing_open_position:
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_blocked_existing_open_position",
                severity="warning",
                message="Existe una posición testnet abierta para el mismo símbolo/lado; se bloquea una nueva entrada",
                context={
                    "symbol": trade_plan.symbol,
                    "side": trade_plan.side,
                    "existing_position_id": existing_open_position.id,
                },
            )
            self.db.commit()
            return {"executed": False, "reason": "existing_open_position"}

        stop_distance = abs(trade_plan.entry_price - trade_plan.stop_loss)
        raw_quantity = 0.0 if stop_distance == 0 else (trade_plan.capital_usdt * (trade_plan.applied_risk_pct / 100)) / stop_distance

        try:
            step_size = await self.binance_client.get_symbol_step_size(trade_plan.symbol)
        except Exception as exc:  # noqa: BLE001
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_step_size_unavailable",
                severity="critical",
                message=f"No fue posible obtener stepSize para {trade_plan.symbol}: {exc}",
                context={"symbol": trade_plan.symbol, "exception_type": type(exc).__name__},
            )
            self.db.commit()
            return {"executed": False, "reason": "symbol_step_size_unavailable"}

        quantity = self._round_to_step(raw_quantity, step_size)
        if quantity <= 0:
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_invalid_quantity",
                severity="critical",
                message=(
                    "Cantidad inválida calculada para ejecución testnet "
                    f"(raw={raw_quantity:.12f}, step_size={step_size})"
                ),
                context={
                    "symbol": trade_plan.symbol,
                    "raw_quantity": round(raw_quantity, 12),
                    "step_size": step_size,
                    "rounded_quantity": quantity,
                },
            )
            self.db.commit()
            return {"executed": False, "reason": "invalid_quantity"}

        if trade_plan.side not in {"long", "short"}:
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_invalid_side",
                severity="critical",
                message=f"Valor de side inválido: {trade_plan.side!r}",
                context={"symbol": trade_plan.symbol, "side": trade_plan.side},
            )
            self.db.commit()
            return {"executed": False, "reason": "invalid_side"}

        side = "BUY" if trade_plan.side == "long" else "SELL"
        exit_side = "SELL" if trade_plan.side == "long" else "BUY"
        client_order_id = f"tp-{trade_plan.id}-{int(time.time() * 1000)}"

        try:
            exchange_order = await self.binance_client.place_market_order(
                symbol=trade_plan.symbol,
                side=side,
                quantity=quantity,
                client_order_id=client_order_id,
            )
        except RuntimeError as exc:
            if str(exc) == "binance_credentials_missing":
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_execution_missing_credentials",
                    severity="critical",
                    message="Credenciales Binance faltantes para ejecución testnet",
                    context={"symbol": trade_plan.symbol, "side": side},
                )
                self.db.commit()
                return {"executed": False, "reason": "testnet_credentials_missing"}

            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_runtime_error",
                severity="critical",
                message=f"Error runtime en envío testnet: {exc}",
                context={
                    "symbol": trade_plan.symbol,
                    "side": side,
                    "quantity": quantity,
                    "client_order_id": client_order_id,
                    "exception_type": type(exc).__name__,
                },
            )
            self.db.commit()
            return {"executed": False, "reason": "testnet_api_error"}
        except Exception as exc:  # noqa: BLE001
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_execution_error",
                severity="critical",
                message=f"Error en envío testnet: {exc}",
                context={
                    "symbol": trade_plan.symbol,
                    "side": side,
                    "quantity": quantity,
                    "client_order_id": client_order_id,
                    "exception_type": type(exc).__name__,
                },
            )
            self.db.commit()
            return {"executed": False, "reason": "testnet_api_error"}

        try:
            exchange_order = await self._confirm_exchange_order(
                trade_plan_id=trade_plan.id,
                symbol=trade_plan.symbol,
                exchange_order=exchange_order,
                client_order_id=client_order_id,
            )
        except Exception as exc:  # noqa: BLE001
            # Última línea de defensa: la orden ya fue enviada, así que preferimos persistir con el payload original.
            self._log_risk_event(
                trade_plan_id=trade_plan.id,
                event_type="testnet_order_refresh_unexpected_error",
                severity="warning",
                message=f"Error inesperado en confirmación post-orden; se persiste payload original: {exc}",
                context={
                    "symbol": trade_plan.symbol,
                    "client_order_id": client_order_id,
                    "exception_type": type(exc).__name__,
                },
            )

        order_id = exchange_order.get("orderId")
        order_trades: list[dict] = []
        get_order_trades = getattr(self.binance_client, "get_order_trades", None)
        if callable(get_order_trades) and order_id is not None:
            try:
                order_trades = await get_order_trades(symbol=trade_plan.symbol, order_id=int(order_id))
            except Exception as exc:  # noqa: BLE001
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_order_trades_lookup_failed",
                    severity="warning",
                    message=f"No fue posible obtener fills reales de userTrades: {exc}",
                    context={
                        "symbol": trade_plan.symbol,
                        "order_id": order_id,
                        "client_order_id": client_order_id,
                        "exception_type": type(exc).__name__,
                    },
                )

        exchange_price = self._extract_fill_price_from_trades(
            order_trades,
            fallback=self._extract_fill_price(exchange_order, fallback=trade_plan.entry_price),
        )
        raw_executed_qty = self._extract_executed_quantity_from_trades(
            order_trades,
            fallback=self._to_float(exchange_order.get("executedQty"), fallback=0.0),
        )
        order_status = self._normalize_order_status(
            exchange_order.get("status"),
            executed_qty=raw_executed_qty,
            requested_qty=quantity,
        )
        executed_qty = raw_executed_qty
        if executed_qty <= 0 and order_status in {"filled", "partially_filled", "new"}:
            executed_qty = quantity
        external_order_id = str(exchange_order.get("orderId") or exchange_order.get("clientOrderId") or client_order_id)

        leverage = 1
        mark_price = exchange_price
        unrealized_pnl = 0.0
        get_position_risk = getattr(self.binance_client, "get_position_risk", None)
        if callable(get_position_risk):
            try:
                position_risk = await get_position_risk(trade_plan.symbol)
            except Exception as exc:  # noqa: BLE001
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_position_risk_lookup_failed",
                    severity="warning",
                    message=f"No fue posible obtener positionRisk real; fallback local ({exc})",
                    context={
                        "symbol": trade_plan.symbol,
                        "external_order_id": external_order_id,
                        "exception_type": type(exc).__name__,
                    },
                )
            else:
                if isinstance(position_risk, dict):
                    leverage = int(self._to_float(position_risk.get("leverage"), fallback=float(leverage)) or leverage)
                    live_mark_price = self._to_float(position_risk.get("markPrice"), fallback=0.0)
                    if live_mark_price > 0:
                        mark_price = live_mark_price
                    direction = 1 if trade_plan.side == "long" else -1
                    unrealized_pnl = round((mark_price - exchange_price) * executed_qty * direction, 8)
        else:
            try:
                leverage = await self.binance_client.get_symbol_leverage(trade_plan.symbol)
            except Exception as exc:  # noqa: BLE001
                self._log_risk_event(
                    trade_plan_id=trade_plan.id,
                    event_type="testnet_execution_leverage_fallback",
                    severity="warning",
                    message=f"No fue posible obtener leverage real; fallback a 1x ({exc})",
                    context={"symbol": trade_plan.symbol, "exception_type": type(exc).__name__},
                )

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
            mark_price=mark_price,
            unrealized_pnl=unrealized_pnl,
            leverage=leverage,
            status="open",
            is_testnet=True,
        )

        stop_order, take_profit_order, protection_reason = await self._place_protection_orders(
            trade_plan=trade_plan,
            exit_side=exit_side,
            external_order_id=external_order_id,
            exchange_price=exchange_price,
            mark_price=mark_price,
        )

        trade_plan.status = "testnet_executed"
        self._log_risk_event(
            trade_plan_id=trade_plan.id,
            event_type="testnet_execution_submitted",
            severity="info",
            message=f"Orden testnet enviada: external_order_id={external_order_id}",
            context={
                "symbol": trade_plan.symbol,
                "side": trade_plan.side,
                "quantity": quantity,
                "executed_quantity": executed_qty,
                "external_order_id": external_order_id,
                "order_status": order_status,
                "binance_side": side,
            },
        )

        objects_to_add = [order, position, trade_plan]
        if stop_order is not None:
            objects_to_add.append(stop_order)
        if take_profit_order is not None:
            objects_to_add.append(take_profit_order)
        self.db.add_all(objects_to_add)
        self.db.commit()
        self.db.refresh(order)
        self.db.refresh(position)
        if stop_order is not None:
            self.db.refresh(stop_order)
        if take_profit_order is not None:
            self.db.refresh(take_profit_order)

        return {
            "executed": True,
            "order_id": order.id,
            "position_id": position.id,
            "external_order_id": external_order_id,
            "stop_order_id": stop_order.id if stop_order is not None else None,
            "take_profit_order_id": take_profit_order.id if take_profit_order is not None else None,
            "reason": protection_reason,
        }
