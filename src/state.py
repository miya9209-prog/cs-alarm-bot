import json
from pathlib import Path
from typing import Iterable, List

STATE_PATH = Path("state.json")


def load_seen() -> List[str]:
    if not STATE_PATH.exists():
        return []
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return list(data.get("seen", []))
        if isinstance(data, list):
            return list(data)
    except Exception:
        return []
    return []


def save_seen(keys: Iterable[str]) -> None:
    unique = []
    seen = set()
    for key in keys:
        if key and key not in seen:
            unique.append(str(key))
            seen.add(str(key))

    STATE_PATH.write_text(
        json.dumps({"seen": unique}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def reset_seen() -> None:
    if STATE_PATH.exists():
        STATE_PATH.unlink()


def state_exists() -> bool:
    return STATE_PATH.exists()
