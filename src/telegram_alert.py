import requests


def send_telegram_message(token: str, chat_id: str, text: str) -> tuple[bool, str]:
    if not token:
        return False, "TELEGRAM_BOT_TOKEN이 비어 있습니다."
    if not chat_id:
        return False, "TELEGRAM_CHAT_ID가 비어 있습니다."
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.ok:
            return True, "전송 성공"
        return False, f"전송 실패: {res.status_code} {res.text[:500]}"
    except Exception as e:
        return False, f"전송 오류: {e}"
