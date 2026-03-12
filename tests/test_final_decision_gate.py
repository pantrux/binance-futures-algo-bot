from apps.api.app.schemas.trading import MarketState, RiskDecision
from apps.api.app.services.final_decision_gate import FinalDecisionGate


def _base_decision() -> RiskDecision:
    return RiskDecision(
        approved=True,
        max_position_notional=200.0,
        suggested_risk_pct=1.0,
        reason="Operación aprobada por el motor de riesgo",
        market_regime="tendencia_alcista",
        score=82.0,
        regime_confidence=78.0,
        portfolio_risk_pct_before=2.0,
        portfolio_risk_pct_after=3.0,
    )


def test_final_gate_passes_under_normal_conditions() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision()
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=2.0,
        trend_strength=75.0,
        liquidity_score=85.0,
        market_regime="tendencia_alcista",
        regime_confidence=78.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is True
    assert out.final_score >= 65.0
    assert out.triggered_breakers == []
    assert any(event.event_type == "final_gate_pass" for event in out.events)


def test_final_gate_blocks_on_extreme_volatility_breaker() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision()
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=6.2,
        trend_strength=70.0,
        liquidity_score=80.0,
        market_regime="alta_volatilidad",
        regime_confidence=65.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert "extreme_volatility" in out.triggered_breakers
    assert any(event.event_type == "circuit_breaker_extreme_volatility" for event in out.events)
