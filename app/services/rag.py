from __future__ import annotations

import re
from typing import Dict, List, Tuple

from app.services.journal import tail_events
from app.services.kb import read_knowledge

WORD_RE = re.compile(r"[A-Za-z0-9]{2,}")


def _score(text: str, keywords: List[str]) -> int:
    text_lower = text.lower()
    return sum(1 for word in keywords if word in text_lower)


def _split_snippets(text: str) -> List[str]:
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    return chunks


def build_context(symbol: str, top_k: int = 3, event_limit: int = 50) -> Dict[str, List[str]]:
    keywords = [symbol.lower()]
    journal = tail_events(event_limit)
    symbol_events: List[str] = []
    for event in journal[::-1]:
        payload = event.get("payload", {})
        if payload.get("symbol") == symbol or event.get("type") in {"signal_auto", "analyze_auto"}:
            summary = f"{event.get('type')} @ {event.get('ts')}"
            symbol_events.append(summary)
        if len(symbol_events) >= 5:
            break

    knowledge = read_knowledge()
    snippets: List[Tuple[int, str]] = []
    for name, content in knowledge.items():
        for snippet in _split_snippets(content):
            score = _score(snippet, keywords)
            if score:
                snippets.append((score, f"{name}: {snippet}"))

    snippets.sort(key=lambda item: item[0], reverse=True)
    top_snippets = [text[:220] for _, text in snippets[:top_k]]

    return {"events": symbol_events, "snippets": top_snippets}


def format_context(context: Dict[str, List[str]]) -> str:
    events = context.get("events", [])
    snippets = context.get("snippets", [])
    events_text = "\n".join(f"- {e}" for e in events) if events else "- none"
    snippets_text = "\n".join(f"- {s}" for s in snippets) if snippets else "- none"
    return (
        "*RAG Context (Memory)*\n"
        f"Recent events:\n{events_text}\n"
        f"Knowledge hits:\n{snippets_text}\n"
    )
