import os
from typing import List


def get_secret(name: str, default: str = "") -> str:
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
    """Return only Cafe24 CS board URLs.

Do not put the review/photo URL here. CREMA reviews are JavaScript-rendered
and must be monitored through CREMA_REVIEW_URL. If a review URL is
accidentally left in BOARD_URLS, it is ignored here to prevent old Cafe24
review-board posts from being mixed into the current CREMA review feed.
"""
    urls = parse_board_urls(get_secret("BOARD_URLS"))
    filtered = []
    for url in urls:
        low = url.lower()
        if "board/review" in low or "board_no=4" in low:
            print(f"SKIP_REVIEW_URL_IN_BOARD_URLS {url}")
            continue
        filtered.append(url)
    return filtered


def get_telegram_token() -> str:
    return get_secret("TELEGRAM_BOT_TOKEN")


def get_telegram_chat_id() -> str:
    return get_secret("TELEGRAM_CHAT_ID")


def get_crema_review_url() -> str:
    return get_secret("CREMA_REVIEW_URL", "https://misharp.co.kr/board/review/photo.html?board_no=4")
