from fastapi import APIRouter

from apps.api.app.schemas.trading import RiskDecision, TradePlanRequest
from apps.api.app.services.risk_engine import RiskEngine

router = APIRouter()
risk_engine = RiskEngine()


@router.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "service": "api"}


@router.post("/risk/evaluate", response_model=RiskDecision)
def evaluate_risk(payload: TradePlanRequest) -> RiskDecision:
    return risk_engine.evaluate(
        capital_usdt=payload.capital_usdt,
        existing_risk_pct=payload.existing_risk_pct,
        signals=payload.signals,
        market_state=payload.market_state,
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
    )
