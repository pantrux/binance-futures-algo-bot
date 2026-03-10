from trading_bot.engines.signal_aggregator import SignalAggregator
from trading_bot.models.signals import MarketContext
from trading_bot.services.plan_service import PlanService


def main() -> None:
    aggregator = SignalAggregator()
    planner = PlanService()

    signals = aggregator.aggregate(technical=78, fundamental=61, sentiment=83, confidence=75)
    context = MarketContext(symbol="BTCUSDT", timeframe="15m", volatility_pct=2.8, trend_strength=72, liquidity_score=90)
    plan = planner.build_plan("BTCUSDT", signals, context)
    print(plan)


if __name__ == "__main__":
    main()
