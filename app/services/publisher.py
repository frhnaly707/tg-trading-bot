from __future__ import annotations

from aiogram import Bot


async def send_to_topic(
    bot: Bot,
    chat_id: int,
    thread_id: int,
    text: str,
    parse_mode: str = "Markdown",
) -> None:
    await bot.send_message(
        chat_id=chat_id,
        message_thread_id=thread_id,
        text=text,
        parse_mode=parse_mode,
        disable_web_page_preview=True,
    )
