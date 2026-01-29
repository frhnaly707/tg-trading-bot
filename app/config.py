from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _get_int(value: Optional[str], default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _get_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    group_chat_id: int
    topic_signal_id: int
    topic_analyze_id: int
    allow_all_post_signal: bool
    monitor_interval_sec: int
    klines_limit: int
    market_provider: str


def load_settings() -> Settings:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    group_chat_id = _get_int(os.getenv("GROUP_CHAT_ID"), 0)
    topic_signal_id = _get_int(os.getenv("TOPIC_SIGNAL_ID"), 0)
    topic_analyze_id = _get_int(os.getenv("TOPIC_ANALYZE_ID"), 0)
    allow_all_post_signal = _get_bool(os.getenv("ALLOW_ALL_POST_SIGNAL"), False)
    monitor_interval_sec = _get_int(os.getenv("MONITOR_INTERVAL_SEC"), 15)
    klines_limit = _get_int(os.getenv("KLINES_LIMIT"), 200)
    market_provider = os.getenv("MARKET_PROVIDER", "auto").strip().lower()

    if not bot_token:
        raise ValueError("BOT_TOKEN is required")

    return Settings(
        bot_token=bot_token,
        group_chat_id=group_chat_id,
        topic_signal_id=topic_signal_id,
        topic_analyze_id=topic_analyze_id,
        allow_all_post_signal=allow_all_post_signal,
        monitor_interval_sec=monitor_interval_sec,
        klines_limit=klines_limit,
        market_provider=market_provider,
    )
