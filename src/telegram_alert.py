import requests


def send_telegram_message(token: str, chat_id: str, message: str) -> bool:
    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 비어 있습니다.")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return True
