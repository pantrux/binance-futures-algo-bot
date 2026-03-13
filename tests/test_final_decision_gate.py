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


def test_final_gate_score_does_not_double_count_liquidity_component() -> None:
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

    # score_wo_liq = 82 - (85 * 0.05) = 77.75
    # final = (77.75 * 0.5) + (78 * 0.3) + (85 * 0.2) = 79.275 -> 79.28
    assert out.final_score == 79.28


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


def test_final_gate_blocks_on_extreme_volatility_breaker_at_threshold() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision()
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=6.0,
        trend_strength=70.0,
        liquidity_score=80.0,
        market_regime="alta_volatilidad",
        regime_confidence=65.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert "extreme_volatility" in out.triggered_breakers


def test_final_gate_blocks_when_portfolio_risk_after_is_unknown() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision().model_copy(update={"portfolio_risk_pct_after": None})
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=2.2,
        trend_strength=72.0,
        liquidity_score=82.0,
        market_regime="tendencia_alcista",
        regime_confidence=72.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert "portfolio_risk_unknown" in out.triggered_breakers
    assert any(event.event_type == "circuit_breaker_portfolio_risk_unknown" for event in out.events)


def test_final_gate_blocks_on_low_liquidity_breaker() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision()
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=2.0,
        trend_strength=70.0,
        liquidity_score=18.0,
        market_regime="transicion",
        regime_confidence=60.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert "low_liquidity" in out.triggered_breakers
    assert any(event.event_type == "circuit_breaker_low_liquidity" for event in out.events)


def test_final_gate_blocks_on_low_liquidity_breaker_at_threshold() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision()
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=2.0,
        trend_strength=70.0,
        liquidity_score=20.0,
        market_regime="transicion",
        regime_confidence=60.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert "low_liquidity" in out.triggered_breakers


def test_final_gate_blocks_on_portfolio_overheat_breaker() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision().model_copy(update={"portfolio_risk_pct_after": 4.8})
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=2.1,
        trend_strength=72.0,
        liquidity_score=84.0,
        market_regime="tendencia_alcista",
        regime_confidence=74.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert "portfolio_overheat" in out.triggered_breakers
    assert any(event.event_type == "circuit_breaker_portfolio_overheat" for event in out.events)


def test_final_gate_blocks_on_regime_uncertainty_breaker_at_threshold() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision().model_copy(update={"regime_confidence": 30.0})
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=2.0,
        trend_strength=70.0,
        liquidity_score=84.0,
        market_regime="transicion",
        regime_confidence=30.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert "regime_uncertainty" in out.triggered_breakers
    assert any(event.event_type == "circuit_breaker_regime_uncertainty" for event in out.events)


def test_final_gate_blocks_when_regime_confidence_is_unknown() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision().model_copy(update={"regime_confidence": None})
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=2.0,
        trend_strength=70.0,
        liquidity_score=84.0,
        market_regime="transicion",
        regime_confidence=None,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert "regime_confidence_unknown" in out.triggered_breakers
    assert any(event.event_type == "circuit_breaker_regime_confidence_unknown" for event in out.events)


def test_final_gate_blocks_on_low_composed_score_without_breakers() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision().model_copy(update={"score": 52.0, "regime_confidence": 52.0})
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=1.5,
        trend_strength=55.0,
        liquidity_score=45.0,
        market_regime="transicion",
        regime_confidence=52.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert out.triggered_breakers == []
    assert "score compuesto insuficiente" in out.reason.lower()
    assert any(event.event_type == "final_gate_low_score" for event in out.events)


def test_final_gate_keeps_risk_engine_reason_when_pre_rejected_and_preserves_breakers() -> None:
    gate = FinalDecisionGate()
    decision = _base_decision().model_copy(
        update={"approved": False, "reason": "Bloqueado por riesgo base", "regime_confidence": 20.0}
    )
    market_state = MarketState(
        symbol="BTCUSDT",
        timeframe="15m",
        volatility_pct=6.3,
        trend_strength=72.0,
        liquidity_score=15.0,
        market_regime="alta_volatilidad",
        regime_confidence=20.0,
    )

    out = gate.evaluate(risk_decision=decision, market_state=market_state)

    assert out.passed is False
    assert out.reason == "Bloqueado por riesgo base"
    assert {"extreme_volatility", "low_liquidity", "regime_uncertainty"}.issubset(set(out.triggered_breakers))
