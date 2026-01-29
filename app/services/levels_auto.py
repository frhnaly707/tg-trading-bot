from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from app.services.marketdata import MarketProvider
from app.services.state import list_watch

LEVELS_PATH = Path("data/levels.json")


@dataclass
class Levels:
    support: List[float]
    resistance: List[float]
    mid: Optional[float]


def _load_levels() -> Dict[str, Dict[str, object]]:
    if not LEVELS_PATH.exists():
        return {}
    try:
        with LEVELS_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {}


def _save_levels(data: Dict[str, Dict[str, object]]) -> None:
    LEVELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEVELS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def compute_levels_from_klines(klines: List[dict]) -> Levels:
    highs = [float(k["high"]) for k in klines]
    lows = [float(k["low"]) for k in klines]
    closes = [float(k["close"]) for k in klines]
    last_close = closes[-1]

    swing_highs: List[float] = []
    swing_lows: List[float] = []
    for i in range(2, len(klines) - 2):
        window_highs = highs[i - 2 : i] + highs[i + 1 : i + 3]
        window_lows = lows[i - 2 : i] + lows[i + 1 : i + 3]
        if window_highs and highs[i] > max(window_highs):
            swing_highs.append(highs[i])
        if window_lows and lows[i] < min(window_lows):
            swing_lows.append(lows[i])

    swing_highs = sorted(set(swing_highs), key=lambda x: abs(x - last_close))[:3]
    swing_lows = sorted(set(swing_lows), key=lambda x: abs(x - last_close))[:3]

    nearest_support = min(swing_lows, default=None, key=lambda x: abs(x - last_close))
    nearest_resistance = min(swing_highs, default=None, key=lambda x: abs(x - last_close))
    mid = None
    if nearest_support is not None and nearest_resistance is not None:
        mid = round((nearest_support + nearest_resistance) / 2, 4)

    return Levels(support=swing_lows, resistance=swing_highs, mid=mid)


def store_levels(symbol: str, tf: str, levels: Levels) -> None:
    data = _load_levels()
    key = f"{symbol}:{tf}"
    data[key] = {
        "support": levels.support,
        "resistance": levels.resistance,
        "mid": levels.mid,
    }
    _save_levels(data)


def get_cached_levels(symbol: str, tf: str) -> Optional[Dict[str, object]]:
    data = _load_levels()
    return data.get(f"{symbol}:{tf}")


async def auto_levels_loop(provider: MarketProvider, settings) -> None:
    while True:
        for item in list_watch():
            if not item.enabled:
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
            except Exception:
                continue
        await asyncio.sleep(settings.monitor_interval_sec)
