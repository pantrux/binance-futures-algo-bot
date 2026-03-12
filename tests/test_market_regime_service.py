from apps.api.app.services.market_regime_service import MarketRegimeService


def test_trend_strength_scales_with_ema_spread_pct() -> None:
    assert MarketRegimeService._trend_strength(None) == 50.0
    assert MarketRegimeService._trend_strength(0.0) == 0.0
    assert MarketRegimeService._trend_strength(1.0) == 40.0


def test_volatility_score_scales_with_atr_pct() -> None:
    assert MarketRegimeService._volatility_score(None) == 50.0
    assert MarketRegimeService._volatility_score(0.0) == 0.0
    assert MarketRegimeService._volatility_score(1.0) == 18.0


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


def test_classify_regime_transicion_fallback() -> None:
    regime = MarketRegimeService._classify_regime(
        trend_bias="bullish",
        momentum_bias="neutral",
        volatility_regime="medium",
        trend_strength=45.0,
        volatility_score=50.0,
        momentum_score=55.0,
    )
    assert regime == "transicion"


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


def test_regime_confidence_bearish_increases_when_momentum_is_more_bearish() -> None:
    low_momentum_score = 30.0  # más bajista
    high_momentum_score = 70.0  # más alcista

    confidence_low = MarketRegimeService._regime_confidence(
        regime="tendencia_bajista",
        trend_strength=70.0,
        volatility_score=40.0,
        momentum_score=low_momentum_score,
    )
    confidence_high = MarketRegimeService._regime_confidence(
        regime="tendencia_bajista",
        trend_strength=70.0,
        volatility_score=40.0,
        momentum_score=high_momentum_score,
    )

    assert confidence_low > confidence_high


def test_regime_confidence_unknown_is_zero() -> None:
    confidence = MarketRegimeService._regime_confidence(
        regime="unknown",
        trend_strength=50.0,
        volatility_score=50.0,
        momentum_score=50.0,
    )
    assert confidence == 0.0


def test_regime_confidence_high_volatility_follows_volatility_score() -> None:
    confidence_low = MarketRegimeService._regime_confidence(
        regime="alta_volatilidad",
        trend_strength=50.0,
        volatility_score=30.0,
        momentum_score=50.0,
    )
    confidence_high = MarketRegimeService._regime_confidence(
        regime="alta_volatilidad",
        trend_strength=50.0,
        volatility_score=80.0,
        momentum_score=50.0,
    )
    assert confidence_high > confidence_low


def test_regime_confidence_bullish_increases_with_trend_and_momentum() -> None:
    c1 = MarketRegimeService._regime_confidence(
        regime="tendencia_alcista",
        trend_strength=60.0,
        volatility_score=40.0,
        momentum_score=55.0,
    )
    c2 = MarketRegimeService._regime_confidence(
        regime="tendencia_alcista",
        trend_strength=80.0,
        volatility_score=40.0,
        momentum_score=70.0,
    )
    assert c2 > c1


def test_regime_confidence_range_lateral_increases_when_low_trend_and_low_volatility() -> None:
    c1 = MarketRegimeService._regime_confidence(
        regime="rango_lateral",
        trend_strength=30.0,
        volatility_score=40.0,
        momentum_score=50.0,
    )
    c2 = MarketRegimeService._regime_confidence(
        regime="rango_lateral",
        trend_strength=10.0,
        volatility_score=20.0,
        momentum_score=50.0,
    )
    assert c2 > c1


def test_regime_confidence_transicion_prefers_neutral_momentum() -> None:
    c_neutral = MarketRegimeService._regime_confidence(
        regime="transicion",
        trend_strength=50.0,
        volatility_score=40.0,
        momentum_score=50.0,
    )
    c_extreme = MarketRegimeService._regime_confidence(
        regime="transicion",
        trend_strength=50.0,
        volatility_score=40.0,
        momentum_score=90.0,
    )
    assert c_neutral > c_extreme


def test_momentum_score_uses_pct_scale_not_absolute_price() -> None:
    # momentum_10_pct de +1% debería empujar el score por encima de 50 (sin saturar)
    score = MarketRegimeService._momentum_score(rsi_14=50.0, momentum_10_pct=1.0)
    assert 50.0 < score < 100.0
