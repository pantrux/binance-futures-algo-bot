from dataclasses import dataclass

from apps.api.app.schemas.trading import MarketState, RiskDecision, RiskEventDetail
from apps.api.app.services.risk_engine import RiskEngine


@dataclass
class FinalGatePolicy:
    min_final_score: float = 65.0
    extreme_volatility_pct: float = 6.0
    min_liquidity_score: float = 20.0
    max_portfolio_risk_pct: float = 4.8
    min_regime_confidence: float = 30.0


@dataclass
class FinalGateDecision:
    passed: bool
    final_score: float
    reason: str
    triggered_breakers: list[str]
    events: list[RiskEventDetail]


class FinalDecisionGate:
    def __init__(self, policy: FinalGatePolicy | None = None):
        self.policy = policy or FinalGatePolicy()

    def _score_components(self, *, risk_decision: RiskDecision, market_state: MarketState) -> tuple[float, float, float]:
        # `risk_decision.score` ya incluye liquidez desde `RiskEngine.aggregate_score`.
        # Usamos la misma constante del motor para evitar acoplamiento frágil.
        base_score_wo_liquidity = max(
            0.0,
            min(100.0, risk_decision.score - (market_state.liquidity_score * RiskEngine.LIQUIDITY_WEIGHT)),
        )
        score_component = base_score_wo_liquidity * 0.5

        # Fallback conservador: si no hay confianza de régimen, no se bonifica el score final.
        regime_component = (risk_decision.regime_confidence if risk_decision.regime_confidence is not None else 0.0) * 0.3
        liquidity_component = market_state.liquidity_score * 0.2
        return score_component, regime_component, liquidity_component

    def evaluate(self, *, risk_decision: RiskDecision, market_state: MarketState) -> FinalGateDecision:
        score_component, regime_component, liquidity_component = self._score_components(
            risk_decision=risk_decision,
            market_state=market_state,
        )
        final_score = round(score_component + regime_component + liquidity_component, 2)

        triggered_breakers: list[str] = []
        events: list[RiskEventDetail] = []

        if market_state.volatility_pct >= self.policy.extreme_volatility_pct:
            triggered_breakers.append("extreme_volatility")
            events.append(
                RiskEventDetail(
                    event_type="circuit_breaker_extreme_volatility",
                    severity="critical",
                    message="Circuit breaker activado por volatilidad extrema",
                    context={
                        "volatility_pct": market_state.volatility_pct,
                        "threshold": self.policy.extreme_volatility_pct,
                    },
                )
            )

        if market_state.liquidity_score <= self.policy.min_liquidity_score:
            triggered_breakers.append("low_liquidity")
            events.append(
                RiskEventDetail(
                    event_type="circuit_breaker_low_liquidity",
                    severity="critical",
                    message="Circuit breaker activado por liquidez crítica",
                    context={
                        "liquidity_score": market_state.liquidity_score,
                        "threshold": self.policy.min_liquidity_score,
                    },
                )
            )

        portfolio_after = risk_decision.portfolio_risk_pct_after
        if portfolio_after is None:
            triggered_breakers.append("portfolio_risk_unknown")
            events.append(
                RiskEventDetail(
                    event_type="circuit_breaker_portfolio_risk_unknown",
                    severity="critical",
                    message="Circuit breaker activado por riesgo de portafolio desconocido",
                    context={"threshold": self.policy.max_portfolio_risk_pct},
                )
            )
        elif portfolio_after >= self.policy.max_portfolio_risk_pct:
            triggered_breakers.append("portfolio_overheat")
            events.append(
                RiskEventDetail(
                    event_type="circuit_breaker_portfolio_overheat",
                    severity="critical",
                    message="Circuit breaker activado por sobrecalentamiento de portafolio",
                    context={
                        "portfolio_risk_pct_after": portfolio_after,
                        "threshold": self.policy.max_portfolio_risk_pct,
                    },
                )
            )

        regime_confidence = risk_decision.regime_confidence
        if regime_confidence is None:
            triggered_breakers.append("regime_confidence_unknown")
            events.append(
                RiskEventDetail(
                    event_type="circuit_breaker_regime_confidence_unknown",
                    severity="critical",
                    message="Circuit breaker activado por confianza de régimen desconocida",
                    context={"threshold": self.policy.min_regime_confidence},
                )
            )
        elif regime_confidence <= self.policy.min_regime_confidence:
            triggered_breakers.append("regime_uncertainty")
            events.append(
                RiskEventDetail(
                    event_type="circuit_breaker_regime_uncertainty",
                    severity="critical",
                    message="Circuit breaker activado por incertidumbre de régimen",
                    context={
                        "regime_confidence": regime_confidence,
                        "threshold": self.policy.min_regime_confidence,
                    },
                )
            )

        if not risk_decision.approved:
            return FinalGateDecision(
                passed=False,
                final_score=final_score,
                reason=risk_decision.reason,
                triggered_breakers=triggered_breakers,
                events=events,
            )

        if triggered_breakers:
            return FinalGateDecision(
                passed=False,
                final_score=final_score,
                reason="Bloqueado por circuit breaker del gate final",
                triggered_breakers=triggered_breakers,
                events=events,
            )

        if final_score < self.policy.min_final_score:
            events.append(
                RiskEventDetail(
                    event_type="final_gate_low_score",
                    severity="warning",
                    message="Gate final rechazó por score compuesto insuficiente",
                    context={"final_score": final_score, "threshold": self.policy.min_final_score},
                )
            )
            return FinalGateDecision(
                passed=False,
                final_score=final_score,
                reason="Bloqueado por gate final: score compuesto insuficiente",
                triggered_breakers=[],
                events=events,
            )

        events.append(
            RiskEventDetail(
                event_type="final_gate_pass",
                severity="info",
                message="Gate final aprobado",
                context={"final_score": final_score, "threshold": self.policy.min_final_score},
            )
        )
        return FinalGateDecision(
            passed=True,
            final_score=final_score,
            reason="Gate final aprobado",
            triggered_breakers=[],
            events=events,
        )
