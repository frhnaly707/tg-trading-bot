from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TriggerResult:
    fired: bool
    direction: Optional[str]
    reason: str


def _volume_spike(volumes: List[float]) -> bool:
    if len(volumes) < 10:
        return False
    avg = sum(volumes[:-1]) / (len(volumes) - 1)
    return volumes[-1] > avg * 1.5


def evaluate_trigger(
    symbol: str,
    tf: str,
    klines: List[dict],
    levels: Optional[Dict[str, object]],
) -> TriggerResult:
    if not levels:
        return TriggerResult(False, None, "Auto-levels pending")

    last = klines[-1]
    close = float(last["close"])
    volumes = [float(k.get("volume", 0) or 0) for k in klines]
    support = [float(v) for v in levels.get("support", [])]
    resistance = [float(v) for v in levels.get("resistance", [])]

    if resistance and close > min(resistance):
        if _volume_spike(volumes) or volumes[-1] == 0:
            return TriggerResult(True, "BUY", "Break & close above resistance")
    if support and close < min(support):
        if _volume_spike(volumes) or volumes[-1] == 0:
            return TriggerResult(True, "SELL", "Break & close below support")

    return TriggerResult(False, None, "No trigger")
