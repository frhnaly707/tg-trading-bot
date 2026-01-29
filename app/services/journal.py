from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

JOURNAL_PATH = Path("data/journal.jsonl")


def append_event(event_type: str, payload: Dict[str, Any]) -> None:
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "payload": payload,
    }
    with JOURNAL_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def tail_events(limit: int = 50) -> List[Dict[str, Any]]:
    if not JOURNAL_PATH.exists():
        return []
    with JOURNAL_PATH.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    items = []
    for line in lines[-limit:]:
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items
