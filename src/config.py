import os
from typing import List


def get_secret(name: str, default: str = "") -> str:
    # 1) GitHub Actions / local env
    value = os.getenv(name)
    if value:
        return value.strip()

    # 2) Streamlit Secrets
    try:
        import streamlit as st  # type: ignore
        value = st.secrets.get(name, default)
        if value is None:
            return default
        return str(value).strip()
    except Exception:
        return default


def parse_board_urls(raw: str) -> List[str]:
    if not raw:
        return []
    parts = []
    for line in raw.replace(',', '\n').splitlines():
        line = line.strip()
        if line:
            parts.append(line)
    return parts


def board_urls() -> List[str]:
    return parse_board_urls(get_secret("BOARD_URLS"))


def telegram_bot_token() -> str:
    return get_secret("TELEGRAM_BOT_TOKEN")


def telegram_chat_id() -> str:
    return get_secret("TELEGRAM_CHAT_ID")
