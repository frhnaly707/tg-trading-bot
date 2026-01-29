from __future__ import annotations

import re
from typing import Optional

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import Settings
from app.services.analyzer import decide, decision_to_dict, format_decision, format_signal_card
from app.services.journal import append_event
from app.services.publisher import send_to_topic
from app.services.rag import build_context, format_context
from app.services.state import WatchItem, upsert_watch

router = Router()

TICKER_RE = re.compile(r"^[A-Za-z0-9]{4,15}$")


def _parse_ticker(text: str) -> Optional[str]:
    cleaned = text.strip().upper()
    if not cleaned or " " in cleaned:
        return None
    if not TICKER_RE.match(cleaned):
        return None
    return cleaned


@router.message()
async def analyze_message(message: types.Message, settings: Settings) -> None:
    if message.message_thread_id != settings.topic_analyze_id:
        return
    if not message.text:
        return

    symbol = _parse_ticker(message.text)
    if not symbol:
        return

    watch = WatchItem(symbol=symbol, tf="15m", enabled=True)
    upsert_watch(watch)

    decision = decide(symbol, "15m", price=None)
    context = build_context(symbol)
    analysis_text = (
        f"*Analysis — {symbol}*\n"
        f"*Technical Agent*: {decision.tech.summary}\n"
        f"*Fundamental Agent*: {decision.fund.summary}\n"
        f"{format_decision(symbol, '15m', decision)}\n"
        f"{format_context(context)}"
    )

    append_event(
        "analyze_auto",
        {
            "symbol": symbol,
            "tf": "15m",
            "decision": decision_to_dict(decision),
            "rag": context,
        },
    )

    markup = None
    if settings.allow_all_post_signal:
        builder = InlineKeyboardBuilder()
        builder.button(text="Post to SIGNAL", callback_data=f"post_signal:{symbol}")
        markup = builder.as_markup()

    await message.reply(analysis_text, parse_mode="Markdown", reply_markup=markup)


@router.callback_query(lambda call: call.data and call.data.startswith("post_signal:"))
async def post_signal_from_analysis(call: types.CallbackQuery, settings: Settings) -> None:
    if not settings.allow_all_post_signal:
        await call.answer("Posting disabled.", show_alert=True)
        return
    symbol = call.data.split(":", 1)[1]
    decision = decide(symbol, "15m", price=None)
    card = format_signal_card(symbol, "15m", decision, "Manual post from analysis")
    await send_to_topic(call.bot, settings.group_chat_id, settings.topic_signal_id, card)
    append_event(
        "signal_posted",
        {"symbol": symbol, "tf": "15m", "decision": decision_to_dict(decision)},
    )
    await call.answer("Posted to SIGNAL.")
