from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

STATE_PATH = Path("data/state.json")


@dataclass
class WatchItem:
    symbol: str
    tf: str
    enabled: bool = True


def _load_state() -> Dict[str, List[Dict[str, object]]]:
    if not STATE_PATH.exists():
        return {"watchlist": []}
    try:
        with STATE_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return {"watchlist": []}


def _save_state(data: Dict[str, List[Dict[str, object]]]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def list_watch() -> List[WatchItem]:
    data = _load_state()
    items = []
    for item in data.get("watchlist", []):
        items.append(WatchItem(**item))
    if not items:
        items.append(WatchItem(symbol="BTCUSDT", tf="15m", enabled=True))
        upsert_watch(items[0])
    return items


def upsert_watch(item: WatchItem) -> None:
    data = _load_state()
    items = data.get("watchlist", [])
    updated = False
    for idx, existing in enumerate(items):
        if existing.get("symbol") == item.symbol and existing.get("tf") == item.tf:
            items[idx] = asdict(item)
            updated = True
            break
    if not updated:
        items.append(asdict(item))
    data["watchlist"] = items
    _save_state(data)
