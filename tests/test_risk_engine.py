from apps.api.app.schemas.trading import MarketState, SignalSnapshot
from apps.api.app.services.risk_engine import RiskEngine


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

    severe_high_vol = engine.evaluate(
        capital_usdt=1500,
        existing_risk_pct=0.0,
        signals=signals,
        market_state=MarketState(
            symbol="ETHUSDT",
            timeframe="15m",
            volatility_pct=4.8,
            trend_strength=62,
            liquidity_score=90,
            market_regime="alta_volatilidad",
            regime_confidence=82,
        ),
        entry_price=3000,
        stop_loss=2960,
    )

    assert near_threshold.approved is True
    assert severe_high_vol.approved is True
    assert near_threshold.suggested_risk_pct > severe_high_vol.suggested_risk_pct


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
    assert "5%" in decision.reason


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
