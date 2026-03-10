from apps.api.app.schemas.trading import MarketState, SignalSnapshot
from apps.api.app.services.risk_engine import RiskEngine


def test_risk_engine_approves_high_quality_setup():
    engine = RiskEngine()
    decision = engine.evaluate(
        capital_usdt=1000,
        existing_risk_pct=1.5,
        signals=SignalSnapshot(technical=82, fundamental=70, sentiment=77, confidence=80),
        market_state=MarketState(symbol="BTCUSDT", timeframe="15m", volatility_pct=2.2, trend_strength=74, liquidity_score=91),
        entry_price=50000,
        stop_loss=49750,
    )
    assert decision.approved is True
    assert decision.suggested_risk_pct > 0
    assert decision.max_position_notional > 0


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
