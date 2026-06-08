import json
from pathlib import Path
from typing import Set
from .config import STATE_FILE


def load_notified_ids() -> Set[str]:
    path = Path(STATE_FILE)
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_notified_ids(ids: Set[str]) -> None:
    path = Path(STATE_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 파일이 너무 커지지 않도록 최근 3000개만 보관
    trimmed = list(ids)[-3000:]
    path.write_text(json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8")
