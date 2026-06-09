import requests


def send_telegram_message(token: str, chat_id: str, message: str) -> bool:
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN이 비어 있습니다.")
    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID가 비어 있습니다.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    response.raise_for_status()
    return True
