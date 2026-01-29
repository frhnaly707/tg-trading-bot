from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher

from app.config import load_settings
from app.handlers import all_routers
from app.services.levels_auto import auto_levels_loop
from app.services.marketdata import (
    AutoProvider,
    BinanceProvider,
    BitgetProvider,
    BybitProvider,
    DummyProvider,
    KucoinProvider,
    OkxProvider,
)
from app.services.monitor import monitor_loop


async def _on_startup(bot: Bot, provider, settings) -> None:
    asyncio.create_task(monitor_loop(bot, provider, settings))
    asyncio.create_task(auto_levels_loop(provider, settings))


def _ensure_dirs() -> None:
    Path("data/knowledge").mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )
    _ensure_dirs()
    settings = load_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp["settings"] = settings
    if settings.market_provider == "bybit":
        provider = BybitProvider()
    elif settings.market_provider == "bitget":
        provider = BitgetProvider()
    elif settings.market_provider == "auto":
        provider = AutoProvider(
            [
                BybitProvider(),
                BitgetProvider(),
                OkxProvider(),
                BinanceProvider(),
                KucoinProvider(),
            ]
        )
    else:
        provider = DummyProvider()
    dp["provider"] = provider

    for router in all_routers:
        dp.include_router(router)

    async def startup_handler() -> None:
        await _on_startup(bot, provider, settings)

    dp.startup.register(startup_handler)
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
