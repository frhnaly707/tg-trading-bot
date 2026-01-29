from __future__ import annotations

import asyncio
import time
from typing import Dict

from app.services.analyzer import decide, decision_to_dict, format_signal_card
from app.services.journal import append_event
from app.services.levels_auto import compute_levels_from_klines, store_levels
from app.services.publisher import send_to_topic
from app.services.state import list_watch
from app.services.trigger_engine import evaluate_trigger


async def monitor_loop(bot, provider, settings) -> None:
    cooldowns: Dict[str, float] = {}
    cooldown_sec = 60 * 15

    while True:
        for item in list_watch():
            if not item.enabled:
                continue
            key = f"{item.symbol}:{item.tf}"
            now = time.time()
            if cooldowns.get(key, 0) > now:
                continue
            try:
                klines = await provider.get_klines(item.symbol, item.tf, settings.klines_limit)
            except Exception:
                klines = None
            if not klines:
                continue

            try:
                levels = compute_levels_from_klines(klines)
                store_levels(item.symbol, item.tf, levels)
                trigger = evaluate_trigger(item.symbol, item.tf, klines, levels.__dict__)
            except Exception:
                continue

            if not trigger.fired:
                continue

            try:
                price = await provider.get_price(item.symbol)
            except Exception:
                price = None
            decision = decide(item.symbol, item.tf, price)
            card = format_signal_card(item.symbol, item.tf, decision, trigger.reason)

            try:
                await send_to_topic(
                    bot,
                    settings.group_chat_id,
                    settings.topic_signal_id,
                    card,
                )
                append_event(
                    "signal_auto",
                    {
                        "symbol": item.symbol,
                        "tf": item.tf,
                        "trigger": trigger.reason,
                        "decision": decision_to_dict(decision),
                    },
                )
            except Exception:
                append_event(
                    "errors",
                    {"symbol": item.symbol, "tf": item.tf, "error": "post_failed"},
                )
            cooldowns[key] = time.time() + cooldown_sec
        await asyncio.sleep(settings.monitor_interval_sec)
