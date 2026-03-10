from dataclasses import dataclass

from apps.api.app.schemas.trading import MarketState, RiskDecision, SignalSnapshot


@dataclass
class RiskPolicy:
    max_account_risk_pct: float = 5.0
    base_risk_per_trade_pct: float = 1.0
    max_single_trade_pct: float = 1.25


class RiskEngine:
    def __init__(self, policy: RiskPolicy | None = None):
        self.policy = policy or RiskPolicy()

    def classify_market_regime(self, market_state: MarketState) -> str:
        if market_state.volatility_pct >= 4.0:
            return "alta_volatilidad"
        if market_state.trend_strength >= 70:
            return "tendencia_fuerte"
        if market_state.trend_strength <= 35:
            return "rango_lateral"
        return "transicion"

    def aggregate_score(self, signals: SignalSnapshot, market_state: MarketState) -> float:
        weights = {
            "technical": 0.40,
            "fundamental": 0.20,
            "sentiment": 0.20,
            "confidence": 0.15,
            "liquidity": 0.05,
        }
        return round(
            signals.technical * weights["technical"]
            + signals.fundamental * weights["fundamental"]
            + signals.sentiment * weights["sentiment"]
            + signals.confidence * weights["confidence"]
            + market_state.liquidity_score * weights["liquidity"],
            2,
        )

    def suggest_risk_pct(self, score: float, regime: str) -> float:
        base = self.policy.base_risk_per_trade_pct
        if regime == "alta_volatilidad":
            return round(min(base * 0.5, self.policy.max_single_trade_pct), 2)
        if score >= 80:
            return round(min(base * 1.1, self.policy.max_single_trade_pct), 2)
        if score >= 70:
            return round(min(base, self.policy.max_single_trade_pct), 2)
        if score >= 60:
            return round(min(base * 0.75, self.policy.max_single_trade_pct), 2)
        return 0.0

    def evaluate(self, *, capital_usdt: float, existing_risk_pct: float, signals: SignalSnapshot, market_state: MarketState, entry_price: float, stop_loss: float) -> RiskDecision:
        regime = self.classify_market_regime(market_state)
        score = self.aggregate_score(signals, market_state)
        suggested_risk_pct = self.suggest_risk_pct(score, regime)

        if suggested_risk_pct == 0:
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason="Score insuficiente para abrir operación",
                market_regime=regime,
                score=score,
            )

        available_risk_pct = max(self.policy.max_account_risk_pct - existing_risk_pct, 0)
        applied_risk_pct = min(suggested_risk_pct, available_risk_pct)

        if applied_risk_pct <= 0:
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason="Sin margen de riesgo disponible dentro del límite global del 5%",
                market_regime=regime,
                score=score,
            )

        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0:
            return RiskDecision(
                approved=False,
                max_position_notional=0,
                suggested_risk_pct=0,
                reason="Stop loss inválido: distancia cero",
                market_regime=regime,
                score=score,
            )

        capital_at_risk = capital_usdt * (applied_risk_pct / 100)
        quantity = capital_at_risk / stop_distance
        notional = round(quantity * entry_price, 2)

        return RiskDecision(
            approved=True,
            max_position_notional=notional,
            suggested_risk_pct=applied_risk_pct,
            reason="Operación aprobada por el motor de riesgo",
            market_regime=regime,
            score=score,
        )
