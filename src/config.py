import os
from typing import List


def get_secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value.strip()

    try:
        import streamlit as st
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
    for line in raw.replace(",", "\n").splitlines():
        line = line.strip()
        if line:
            parts.append(line)

    return parts


def get_board_urls() -> List[str]:
    return parse_board_urls(get_secret("BOARD_URLS"))


def get_telegram_token() -> str:
    return get_secret("TELEGRAM_BOT_TOKEN")


def get_telegram_chat_id() -> str:
    return get_secret("TELEGRAM_CHAT_ID")


# 기존 코드 호환용 별칭
def board_urls() -> List[str]:
    return get_board_urls()


def telegram_bot_token() -> str:
    return get_telegram_token()


def telegram_chat_id() -> str:
    return get_telegram_chat_id()
