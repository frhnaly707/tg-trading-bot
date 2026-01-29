from __future__ import annotations

from pathlib import Path
from typing import Dict

KB_FILES = {
    "rules": Path("data/knowledge/rules.md"),
    "playbook": Path("data/knowledge/playbook.md"),
    "notes": Path("data/knowledge/notes.md"),
}


def read_knowledge() -> Dict[str, str]:
    data: Dict[str, str] = {}
    for key, path in KB_FILES.items():
        if path.exists():
            data[key] = path.read_text(encoding="utf-8")
        else:
            data[key] = ""
    return data
