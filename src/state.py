from __future__ import annotations
import json
from pathlib import Path

STATE_FILE = Path("state.json")


def state_exists() -> bool:
    return STATE_FILE.exists()


def load_seen() -> set[str]:
    if not STATE_FILE.exists():
        return set()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return set(data.get("seen", []))
    except Exception:
        return set()


def save_seen(seen: set[str]) -> None:
    STATE_FILE.write_text(json.dumps({"seen": sorted(seen)}, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_seen() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()
