from sqlalchemy.orm import Session

from apps.api.app.db.models import RiskEvent, TradePlan
from apps.api.app.schemas.trade_plan import TradePlanCreateRequest, TradePlanCreateResponse
from apps.api.app.services.outline_service import OutlineService
from apps.api.app.services.risk_engine import RiskEngine


class TradePlanService:
    def __init__(self, db: Session, risk_engine: RiskEngine | None = None, outline_service: OutlineService | None = None) -> None:
        self.db = db
        self.risk_engine = risk_engine or RiskEngine()
        self.outline_service = outline_service or OutlineService()

    async def create_trade_plan(self, payload: TradePlanCreateRequest) -> TradePlanCreateResponse:
        decision = self.risk_engine.evaluate(
            capital_usdt=payload.capital_usdt,
            existing_risk_pct=payload.existing_risk_pct,
            signals=payload.signals,
            market_state=payload.market_state,
            entry_price=payload.entry_price,
            stop_loss=payload.stop_loss,
            symbol=payload.symbol,
            side=payload.side,
            portfolio_state=payload.portfolio_state,
        )
        trade_plan = TradePlan(
            symbol=payload.symbol,
            side=payload.side,
            timeframe=payload.market_state.timeframe,
            market_regime=decision.market_regime,
            technical_score=payload.signals.technical,
            fundamental_score=payload.signals.fundamental,
            sentiment_score=payload.signals.sentiment,
            confidence_score=payload.signals.confidence,
            aggregate_score=decision.score,
            entry_price=payload.entry_price,
            stop_loss=payload.stop_loss,
            take_profit=payload.take_profit,
            capital_usdt=payload.capital_usdt,
            applied_risk_pct=decision.suggested_risk_pct,
            max_position_notional=decision.max_position_notional,
            thesis=payload.thesis,
            status="approved" if decision.approved else "blocked",
            is_testnet=True,
        )
        self.db.add(trade_plan)
        self.db.commit()
        self.db.refresh(trade_plan)

        for event in decision.risk_events:
            context_payload = ", ".join(f"{key}={value}" for key, value in sorted(event.context.items()))
            composed_message = event.message
            if context_payload:
                composed_message = f"{composed_message} | {context_payload}"
            composed_message = (
                f"{composed_message} | market_regime={decision.market_regime}, regime_confidence={decision.regime_confidence}"
            )

            risk_event = RiskEvent(
                trade_plan_id=trade_plan.id,
                event_type=event.event_type,
                severity=event.severity,
                message=composed_message,
            )
            self.db.add(risk_event)
        self.db.commit()

        outline_result = await self.outline_service.create_trade_plan_document(
            request=payload,
            risk_summary={
                "market_regime": decision.market_regime,
                "score": decision.score,
                "suggested_risk_pct": decision.suggested_risk_pct,
                "max_position_notional": decision.max_position_notional,
                "reason": decision.reason,
                "regime_confidence": decision.regime_confidence,
                "cluster_key": decision.cluster_key,
                "correlation_multiplier": decision.correlation_multiplier,
                "portfolio_risk_pct_before": decision.portfolio_risk_pct_before,
                "portfolio_risk_pct_after": decision.portfolio_risk_pct_after,
            },
        )
        outline_url = outline_result.get("data", {}).get("url") if isinstance(outline_result, dict) else None
        if outline_url:
            trade_plan.outline_url = outline_url
            self.db.add(trade_plan)
            self.db.commit()

        return TradePlanCreateResponse(
            id=trade_plan.id,
            status=trade_plan.status,
            outline_url=trade_plan.outline_url,
            market_regime=trade_plan.market_regime,
            aggregate_score=trade_plan.aggregate_score,
            applied_risk_pct=trade_plan.applied_risk_pct,
            max_position_notional=trade_plan.max_position_notional,
        )
