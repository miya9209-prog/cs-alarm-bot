import os
from typing import List


def get_secret(name: str, default: str = "") -> str:
    """Read a value from environment variables first, then Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value.strip()

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

    urls: List[str] = []
    for line in raw.replace(",", "\n").splitlines():
        line = line.strip()
        if line:
            urls.append(line)
    return urls


def get_board_urls() -> List[str]:
    return parse_board_urls(get_secret("BOARD_URLS"))


def get_telegram_token() -> str:
    return get_secret("TELEGRAM_BOT_TOKEN")


def get_telegram_chat_id() -> str:
    return get_secret("TELEGRAM_CHAT_ID")


# Backward-compatible aliases
board_urls = get_board_urls
telegram_bot_token = get_telegram_token
telegram_chat_id = get_telegram_chat_id
