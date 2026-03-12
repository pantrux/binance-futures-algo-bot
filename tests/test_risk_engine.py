import pytest

from apps.api.app.schemas.trading import MarketState, PortfolioState, PositionExposure, SignalSnapshot
from apps.api.app.services.risk_engine import RiskEngine, RiskPolicy


def test_risk_engine_approves_high_quality_setup():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=1.5,
        signals=SignalSnapshot(technical=82, fundamental=70, sentiment=77, confidence=80),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.2,
            trend_strength=74,
            liquidity_score=91,
            market_regime="tendencia_alcista",
            regime_confidence=80,
        ),
        entry_price=50000,
        stop_loss=49750,
    )
    assert decision.approved is True
    assert decision.suggested_risk_pct > 0
    assert decision.max_position_notional > 0
    assert decision.regime_confidence is not None


def test_risk_engine_degrades_sizing_in_high_volatility_vs_trend_regime():
    engine = RiskEngine()
    signals = SignalSnapshot(technical=90, fundamental=85, sentiment=88, confidence=90)

    trend_decision = engine.evaluate(
        capital_usdt=2000,
        existing_risk_pct=0.5,
        signals=signals,
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.0,
            trend_strength=78,
            liquidity_score=95,
            market_regime="tendencia_alcista",
            regime_confidence=82,
        ),
        entry_price=50000,
        stop_loss=49750,
    )

    high_vol_decision = engine.evaluate(
        capital_usdt=2000,
        existing_risk_pct=0.5,
        signals=signals,
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=4.6,
            trend_strength=78,
            liquidity_score=95,
            market_regime="alta_volatilidad",
            regime_confidence=82,
        ),
        entry_price=50000,
        stop_loss=49750,
    )

    assert trend_decision.approved is True
    assert high_vol_decision.approved is True
    assert high_vol_decision.suggested_risk_pct < trend_decision.suggested_risk_pct


def test_risk_engine_high_volatility_near_threshold_degrades_less_than_high_confidence_case():
    engine = RiskEngine()
    signals = SignalSnapshot(technical=88, fundamental=80, sentiment=82, confidence=84)

    near_threshold = engine.evaluate(
        capital_usdt=1500,
        existing_risk_pct=0.0,
        signals=signals,
        market_state=MarketState(
            symbol="ETHUSDT",
            timeframe="15m",
            volatility_pct=2.6,
            trend_strength=62,
            liquidity_score=90,
            market_regime="alta_volatilidad",
            regime_confidence=45,
        ),
        entry_price=3000,
        stop_loss=2960,
    )

    high_confidence_same_vol = engine.evaluate(
        capital_usdt=1500,
        existing_risk_pct=0.0,
        signals=signals,
        market_state=MarketState(
            symbol="ETHUSDT",
            timeframe="15m",
            volatility_pct=2.6,
            trend_strength=62,
            liquidity_score=90,
            market_regime="alta_volatilidad",
            regime_confidence=82,
        ),
        entry_price=3000,
        stop_loss=2960,
    )

    assert near_threshold.approved is True
    assert high_confidence_same_vol.approved is True
    assert near_threshold.suggested_risk_pct > high_confidence_same_vol.suggested_risk_pct


def test_risk_engine_rejects_if_score_below_dynamic_threshold():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=1.0,
        signals=SignalSnapshot(technical=45, fundamental=48, sentiment=46, confidence=50),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=1.8,
            trend_strength=60,
            liquidity_score=70,
            market_regime="transicion",
            regime_confidence=60,
        ),
        entry_price=50000,
        stop_loss=49800,
    )
    assert decision.approved is False
    assert "insuficiente" in decision.reason.lower()


def test_risk_engine_uses_neutral_confidence_for_unexpected_regime_name():
    engine = RiskEngine()
    confidence = engine.estimate_regime_confidence(
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.0,
            trend_strength=70,
            liquidity_score=90,
        ),
        regime="regimen_futuro_no_soportado",
    )
    assert confidence == 50.0


def test_risk_engine_uses_policy_defaults_for_symbol_and_cluster_limits_when_portfolio_state_is_missing():
    engine = RiskEngine(policy=RiskPolicy(default_max_symbol_risk_pct=0.2, default_max_cluster_risk_pct=0.8))
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=0.0,
        signals=SignalSnapshot(technical=86, fundamental=76, sentiment=80, confidence=84),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=1.8,
            trend_strength=75,
            liquidity_score=91,
            market_regime="tendencia_alcista",
            regime_confidence=80,
        ),
        entry_price=50000,
        stop_loss=49750,
    )

    assert decision.approved is True
    assert decision.suggested_risk_pct <= 0.2
    assert any(event.event_type == "risk_pct_capped_by_portfolio" for event in decision.risk_events)


def test_portfolio_state_rejects_inconsistent_limit_hierarchy():
    with pytest.raises(ValueError):
        PortfolioState(max_symbol_risk_pct=3.0, max_cluster_risk_pct=2.0, max_portfolio_risk_pct=5.0)


def test_risk_policy_rejects_inconsistent_default_limit_hierarchy():
    with pytest.raises(ValueError):
        RiskPolicy(default_max_symbol_risk_pct=3.0, default_max_cluster_risk_pct=2.0)


def test_risk_policy_rejects_high_volatility_threshold_below_minimum_supported_bucket():
    with pytest.raises(ValueError):
        RiskPolicy(high_volatility_threshold_pct=1.5)
    with pytest.raises(ValueError):
        RiskPolicy(high_volatility_threshold_pct=2.0)



def test_risk_engine_correlation_normalization_respects_custom_portfolio_max_risk():
    engine = RiskEngine(policy=RiskPolicy(max_account_risk_pct=10.0))
    decision = engine.evaluate(
        capital_usdt=2000,
        existing_risk_pct=0.0,
        signals=SignalSnapshot(technical=90, fundamental=85, sentiment=88, confidence=90),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.0,
            trend_strength=78,
            liquidity_score=95,
            market_regime="tendencia_alcista",
            regime_confidence=82,
        ),
        entry_price=50000,
        stop_loss=49750,
        symbol="BTCUSDT",
        side="long",
        portfolio_state=PortfolioState(
            positions=[PositionExposure(symbol="BTCUSDT", side="long", notional_usdt=8000, risk_pct=5.0)],
            max_portfolio_risk_pct=10.0,
            max_cluster_risk_pct=8.0,
            max_symbol_risk_pct=7.0,
        ),
    )

    assert decision.approved is True
    assert decision.correlation_multiplier == pytest.approx(0.92, abs=1e-6)


def test_risk_engine_respects_custom_high_volatility_threshold_in_volatility_multiplier():
    engine_default = RiskEngine()
    engine_custom = RiskEngine(policy=RiskPolicy(high_volatility_threshold_pct=3.0))

    default_decision = engine_default.evaluate(
        capital_usdt=1000,
        existing_risk_pct=0.0,
        signals=SignalSnapshot(technical=88, fundamental=82, sentiment=84, confidence=86),
        market_state=MarketState(
            symbol="ETHUSDT",
            timeframe="15m",
            volatility_pct=3.5,
            trend_strength=68,
            liquidity_score=90,
            market_regime="alta_volatilidad",
            regime_confidence=75,
        ),
        entry_price=3000,
        stop_loss=2960,
    )

    custom_decision = engine_custom.evaluate(
        capital_usdt=1000,
        existing_risk_pct=0.0,
        signals=SignalSnapshot(technical=88, fundamental=82, sentiment=84, confidence=86),
        market_state=MarketState(
            symbol="ETHUSDT",
            timeframe="15m",
            volatility_pct=3.5,
            trend_strength=68,
            liquidity_score=90,
            market_regime="alta_volatilidad",
            regime_confidence=75,
        ),
        entry_price=3000,
        stop_loss=2960,
    )

    # Con threshold custom más bajo (3.0), el mismo 3.5% debe degradar más que el default (4.0).
    assert default_decision.approved is True
    assert custom_decision.approved is True
    assert custom_decision.suggested_risk_pct < default_decision.suggested_risk_pct


def test_risk_engine_preserves_mild_volatility_bucket_with_low_custom_threshold():
    engine = RiskEngine(policy=RiskPolicy(high_volatility_threshold_pct=3.0))

    mild = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=0.0,
        signals=SignalSnapshot(technical=88, fundamental=82, sentiment=84, confidence=86),
        market_state=MarketState(
            symbol="ETHUSDT",
            timeframe="15m",
            volatility_pct=1.8,
            trend_strength=68,
            liquidity_score=90,
            market_regime="transicion",
            regime_confidence=60,
        ),
        entry_price=3000,
        stop_loss=2960,
    )

    elevated = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=0.0,
        signals=SignalSnapshot(technical=88, fundamental=82, sentiment=84, confidence=86),
        market_state=MarketState(
            symbol="ETHUSDT",
            timeframe="15m",
            volatility_pct=2.2,
            trend_strength=68,
            liquidity_score=90,
            market_regime="transicion",
            regime_confidence=60,
        ),
        entry_price=3000,
        stop_loss=2960,
    )

    assert mild.approved is True
    assert elevated.approved is True
    assert mild.suggested_risk_pct > elevated.suggested_risk_pct


def test_risk_engine_respects_custom_min_score_policy_threshold():
    engine = RiskEngine(policy=RiskPolicy(min_score_to_trade=55.0))
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=0.0,
        signals=SignalSnapshot(technical=57, fundamental=57, sentiment=57, confidence=57),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=1.5,
            trend_strength=70,
            liquidity_score=57,
            market_regime="tendencia_alcista",
            regime_confidence=70,
        ),
        entry_price=50000,
        stop_loss=49800,
    )
    assert decision.approved is True
    assert decision.suggested_risk_pct > 0


def test_risk_engine_caps_explicit_regime_when_observed_volatility_is_high():
    engine = RiskEngine()
    signals = SignalSnapshot(technical=90, fundamental=85, sentiment=88, confidence=90)

    # Escenario de riesgo: régimen explícito no-volátil sin confidence, pero con volatilidad observada alta.
    explicit_stale_regime = engine.evaluate(
        capital_usdt=2000,
        existing_risk_pct=0.0,
        signals=signals,
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=5.0,
            trend_strength=30,
            liquidity_score=95,
            market_regime="rango_lateral",
            regime_confidence=None,
        ),
        entry_price=50000,
        stop_loss=49750,
    )

    # Referencia conservadora: sin régimen explícito, el fallback clasifica alta volatilidad.
    internal_fallback = engine.evaluate(
        capital_usdt=2000,
        existing_risk_pct=0.0,
        signals=signals,
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=5.0,
            trend_strength=30,
            liquidity_score=95,
            market_regime=None,
            regime_confidence=None,
        ),
        entry_price=50000,
        stop_loss=49750,
    )

    assert explicit_stale_regime.approved is True
    assert internal_fallback.approved is True
    assert explicit_stale_regime.suggested_risk_pct <= internal_fallback.suggested_risk_pct


def test_risk_engine_blocks_when_symbol_risk_limit_is_exceeded():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=1.0,
        signals=SignalSnapshot(technical=88, fundamental=78, sentiment=80, confidence=84),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=1.8,
            trend_strength=75,
            liquidity_score=90,
            market_regime="tendencia_alcista",
            regime_confidence=78,
        ),
        entry_price=50000,
        stop_loss=49750,
        symbol="BTCUSDT",
        side="long",
        portfolio_state=PortfolioState(
            positions=[PositionExposure(symbol="BTCUSDT", side="long", notional_usdt=1200, risk_pct=1.6)],
            max_symbol_risk_pct=1.6,
            max_cluster_risk_pct=3.0,
            max_portfolio_risk_pct=5.0,
        ),
    )

    assert decision.approved is False
    assert "símbolo" in decision.reason.lower()
    assert any(event.event_type == "symbol_risk_limit_breached" for event in decision.risk_events)


def test_risk_engine_blocks_when_cluster_risk_limit_is_exceeded():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=2.0,
        signals=SignalSnapshot(technical=85, fundamental=77, sentiment=79, confidence=83),
        market_state=MarketState(
            symbol="ETHUSDT",
            timeframe="15m",
            volatility_pct=2.1,
            trend_strength=72,
            liquidity_score=88,
            market_regime="tendencia_alcista",
            regime_confidence=74,
        ),
        entry_price=3000,
        stop_loss=2960,
        symbol="ETHUSDT",
        side="long",
        portfolio_state=PortfolioState(
            positions=[
                PositionExposure(symbol="ETHUSDT", side="long", notional_usdt=900, risk_pct=1.4),
                PositionExposure(symbol="ETHFIUSDT", side="long", notional_usdt=450, risk_pct=1.0),
            ],
            max_symbol_risk_pct=2.0,
            max_cluster_risk_pct=2.4,
            max_portfolio_risk_pct=5.0,
        ),
    )

    assert decision.approved is False
    assert "clúster" in decision.reason.lower() or "cluster" in decision.reason.lower()
    assert any(event.event_type == "cluster_risk_limit_breached" for event in decision.risk_events)


def test_risk_engine_emits_all_breaches_when_symbol_and_cluster_limits_are_both_exhausted():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=1.0,
        signals=SignalSnapshot(technical=87, fundamental=78, sentiment=81, confidence=85),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.0,
            trend_strength=77,
            liquidity_score=90,
            market_regime="tendencia_alcista",
            regime_confidence=79,
        ),
        entry_price=50000,
        stop_loss=49750,
        symbol="BTCUSDT",
        side="long",
        portfolio_state=PortfolioState(
            positions=[
                PositionExposure(symbol="BTCUSDT", side="long", notional_usdt=1000, risk_pct=1.6),
                PositionExposure(symbol="BTCUSDT", side="long", notional_usdt=900, risk_pct=1.4),
            ],
            max_symbol_risk_pct=1.6,
            max_cluster_risk_pct=3.0,
            max_portfolio_risk_pct=5.0,
        ),
    )

    assert decision.approved is False
    event_types = {event.event_type for event in decision.risk_events}
    assert "symbol_risk_limit_breached" in event_types
    assert "cluster_risk_limit_breached" in event_types


def test_risk_engine_emits_portfolio_breach_alongside_symbol_and_cluster_breaches():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=2.2,
        signals=SignalSnapshot(technical=87, fundamental=78, sentiment=81, confidence=85),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.0,
            trend_strength=77,
            liquidity_score=90,
            market_regime="tendencia_alcista",
            regime_confidence=79,
        ),
        entry_price=50000,
        stop_loss=49750,
        symbol="BTCUSDT",
        side="long",
        portfolio_state=PortfolioState(
            positions=[
                PositionExposure(symbol="BTCUSDT", side="long", notional_usdt=1000, risk_pct=1.6),
                PositionExposure(symbol="BTCUSDT", side="long", notional_usdt=900, risk_pct=1.4),
            ],
            max_symbol_risk_pct=1.6,
            max_cluster_risk_pct=3.0,
            max_portfolio_risk_pct=5.0,
        ),
    )

    assert decision.approved is False
    event_types = {event.event_type for event in decision.risk_events}
    assert "portfolio_risk_limit_breached" in event_types
    assert "symbol_risk_limit_breached" in event_types
    assert "cluster_risk_limit_breached" in event_types


def test_risk_engine_degrades_sizing_under_correlation_pressure():
    engine = RiskEngine()
    signals = SignalSnapshot(technical=90, fundamental=84, sentiment=86, confidence=89)

    baseline = engine.evaluate(
        capital_usdt=1500,
        existing_risk_pct=1.0,
        signals=signals,
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.0,
            trend_strength=78,
            liquidity_score=93,
            market_regime="tendencia_alcista",
            regime_confidence=80,
        ),
        entry_price=50000,
        stop_loss=49750,
        symbol="BTCUSDT",
        side="long",
        portfolio_state=PortfolioState(positions=[]),
    )

    pressured = engine.evaluate(
        capital_usdt=1500,
        existing_risk_pct=1.0,
        signals=signals,
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.0,
            trend_strength=78,
            liquidity_score=93,
            market_regime="tendencia_alcista",
            regime_confidence=80,
        ),
        entry_price=50000,
        stop_loss=49750,
        symbol="BTCUSDT",
        side="long",
        portfolio_state=PortfolioState(
            positions=[
                PositionExposure(symbol="ETHUSDT", side="long", notional_usdt=1500, risk_pct=1.0),
                PositionExposure(symbol="BTCUSDT", side="long", notional_usdt=1800, risk_pct=2.4),
            ],
            max_symbol_risk_pct=3.0,
            max_cluster_risk_pct=4.0,
            max_portfolio_risk_pct=5.0,
        ),
    )

    assert baseline.approved is True
    assert pressured.approved is True
    assert pressured.suggested_risk_pct < baseline.suggested_risk_pct
    assert pressured.correlation_multiplier is not None
    assert pressured.correlation_multiplier < 1.0
    assert any(event.event_type == "correlation_pressure" for event in pressured.risk_events)


def test_risk_engine_rejects_if_global_risk_exhausted():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=5.0,
        signals=SignalSnapshot(technical=90, fundamental=90, sentiment=90, confidence=90),
        market_state=MarketState(symbol="BTCUSDT", timeframe="15m", volatility_pct=1.8, trend_strength=80, liquidity_score=95),
        entry_price=50000,
        stop_loss=49900,
    )
    assert decision.approved is False
    assert "margen" in decision.reason.lower() or "portafolio" in decision.reason.lower()


def test_risk_engine_notional_matches_applied_risk_pct_formula():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=0.0,
        signals=SignalSnapshot(technical=85, fundamental=80, sentiment=82, confidence=86),
        market_state=MarketState(
            symbol="BTCUSDT",
            timeframe="15m",
            volatility_pct=2.0,
            trend_strength=75,
            liquidity_score=90,
            market_regime="tendencia_alcista",
            regime_confidence=80,
        ),
        entry_price=50000,
        stop_loss=49750,
    )

    assert decision.approved is True
    expected_capital_at_risk = 1000 * (decision.suggested_risk_pct / 100)
    expected_quantity = expected_capital_at_risk / 250
    expected_notional = round(expected_quantity * 50000, 2)
    assert decision.max_position_notional == expected_notional
