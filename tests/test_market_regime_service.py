from apps.api.app.services.market_regime_service import MarketRegimeService


def test_classify_regime_high_volatility_has_priority() -> None:
    regime = MarketRegimeService._classify_regime(
        trend_bias="bullish",
        momentum_bias="bullish",
        volatility_regime="high",
        trend_strength=80.0,
        volatility_score=80.0,
        momentum_score=80.0,
    )
    assert regime == "alta_volatilidad"


def test_classify_regime_bullish_trend() -> None:
    regime = MarketRegimeService._classify_regime(
        trend_bias="bullish",
        momentum_bias="bullish",
        volatility_regime="medium",
        trend_strength=60.0,
        volatility_score=40.0,
        momentum_score=60.0,
    )
    assert regime == "tendencia_alcista"


def test_classify_regime_bearish_trend() -> None:
    regime = MarketRegimeService._classify_regime(
        trend_bias="bearish",
        momentum_bias="bearish",
        volatility_regime="medium",
        trend_strength=60.0,
        volatility_score=40.0,
        momentum_score=40.0,
    )
    assert regime == "tendencia_bajista"


def test_classify_regime_range_lateral() -> None:
    regime = MarketRegimeService._classify_regime(
        trend_bias="neutral",
        momentum_bias="neutral",
        volatility_regime="low",
        trend_strength=30.0,
        volatility_score=50.0,
        momentum_score=50.0,
    )
    assert regime == "rango_lateral"


def test_classify_regime_unknown_when_inputs_unknown() -> None:
    regime = MarketRegimeService._classify_regime(
        trend_bias="unknown",
        momentum_bias="neutral",
        volatility_regime="medium",
        trend_strength=50.0,
        volatility_score=50.0,
        momentum_score=50.0,
    )
    assert regime == "unknown"


def test_classify_regime_unknown_has_priority_over_trend() -> None:
    regime = MarketRegimeService._classify_regime(
        trend_bias="bullish",
        momentum_bias="bullish",
        volatility_regime="unknown",
        trend_strength=80.0,
        volatility_score=40.0,
        momentum_score=80.0,
    )
    assert regime == "unknown"


def test_classify_regime_high_volatility_triggered_by_score_even_if_regime_not_high() -> None:
    regime = MarketRegimeService._classify_regime(
        trend_bias="neutral",
        momentum_bias="neutral",
        volatility_regime="medium",
        trend_strength=40.0,
        volatility_score=72.0,
        momentum_score=50.0,
    )
    assert regime == "alta_volatilidad"


def test_regime_confidence_unknown_is_zero() -> None:
    confidence = MarketRegimeService._regime_confidence(
        regime="unknown",
        trend_strength=50.0,
        volatility_score=50.0,
        momentum_score=50.0,
    )
    assert confidence == 0.0
