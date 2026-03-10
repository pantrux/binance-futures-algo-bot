import asyncio

from trading_bot.config.settings import WorkerSettings
from trading_bot.services.api_client import TradingBotApiClient
from trading_bot.services.demo_signal_service import DemoSignalService


async def main() -> None:
    settings = WorkerSettings()
    demo_service = DemoSignalService()
    api_client = TradingBotApiClient(settings.api_base_url)

    for symbol in settings.symbols:
        signals, context, thesis, levels = demo_service.build_signal_pack(symbol)
        payload = {
            "symbol": symbol,
            "side": "long",
            "entry_price": levels["entry"],
            "stop_loss": levels["stop"],
            "take_profit": levels["take_profit"],
            "capital_usdt": settings.seed_capital_usdt,
            "existing_risk_pct": 0.0,
            "thesis": thesis,
            "signals": {
                "technical": signals.technical,
                "fundamental": signals.fundamental,
                "sentiment": signals.sentiment,
                "confidence": signals.confidence,
            },
            "market_state": {
                "symbol": context.symbol,
                "timeframe": context.timeframe,
                "volatility_pct": context.volatility_pct,
                "trend_strength": context.trend_strength,
                "liquidity_score": context.liquidity_score,
            },
        }
        created = await api_client.create_trade_plan(payload)
        print({"symbol": symbol, "trade_plan": created})
        if settings.paper_trading and created.get("status") == "approved":
            executed = await api_client.execute_paper_trade(created["id"])
            print({"symbol": symbol, "paper_execution": executed})


if __name__ == "__main__":
    asyncio.run(main())
