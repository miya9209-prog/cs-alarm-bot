from typing import Dict, List

from src.cafe24_board import BoardPost, fetch_all_boards
from src.config import get_board_urls, get_telegram_chat_id, get_telegram_token
from src.state import load_seen, save_seen, reset_seen
from src.telegram_alert import send_telegram_message


def get_current_posts() -> List[BoardPost]:
    return fetch_all_boards(get_board_urls(), limit_per_board=10)


def initialize_current_posts() -> Dict[str, object]:
    posts = get_current_posts()
    keys = [p.key for p in posts if not p.title.startswith("[오류]")]
    save_seen(keys)
    return {"saved": len(keys), "total": len(posts), "posts": posts}


def reset_state() -> Dict[str, object]:
    reset_seen()
    return {"ok": True}


def check_new_posts(send_alert: bool = True) -> Dict[str, object]:
    posts = get_current_posts()
    seen = set(load_seen())
    new_posts = [p for p in posts if p.key not in seen and not p.title.startswith("[오류]")]

    if send_alert and new_posts:
        token = get_telegram_token()
        chat_id = get_telegram_chat_id()
        for p in reversed(new_posts):
            send_telegram_message(
                token,
                chat_id,
                f"🔔 미샵 CS 새글 알림\n\n게시판: {p.board_name}\n제목: {p.title}\n링크: {p.url}",
            )

    # Always update baseline after checking, so duplicates are not resent.
    save_seen([p.key for p in posts if not p.title.startswith("[오류]")])
    return {"new_count": len(new_posts), "total": len(posts), "new_posts": new_posts, "posts": new_posts}


def main():
    result = check_new_posts(send_alert=True)
    print(f"new_count={result['new_count']}, total={result['total']}")


if __name__ == "__main__":
    main()
