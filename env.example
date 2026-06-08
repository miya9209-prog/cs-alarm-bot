import os
from dotenv import load_dotenv

load_dotenv()


def get_secret(name: str, default: str = "") -> str:
    """환경변수 또는 Streamlit secrets에서 값을 읽습니다."""
    value = os.getenv(name)
    if value:
        return value.strip()
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return default


TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")
BOARD_URLS = [u.strip() for u in get_secret("BOARD_URLS", "").split(",") if u.strip()]
CHECK_LIMIT = int(get_secret("CHECK_LIMIT", "20") or 20)
STATE_FILE = get_secret("STATE_FILE", "data/notified_posts.json")
CAFE24_MALL_ID = get_secret("CAFE24_MALL_ID")
CAFE24_ACCESS_TOKEN = get_secret("CAFE24_ACCESS_TOKEN")
