from typing import Dict, List

from src.cafe24_board import BoardPost, fetch_all_boards
from src.config import get_board_urls, get_telegram_chat_id, get_telegram_token
from src.state import load_seen, save_seen, reset_seen
from src.telegram_alert import send_telegram_message


def get_current_posts() -> List[BoardPost]:
    board_urls = get_board_urls()
    return fetch_all_boards(board_urls, limit_per_board=10)


def initialize_current_posts() -> Dict[str, int]:
    posts = get_current_posts()
    seen_keys = [p.key for p in posts if not p.title.startswith("[오류]")]
    save_seen(seen_keys)

    return {
        "saved": len(seen_keys),
        "total": len(posts),
    }


def reset_state() -> Dict[str, bool]:
    reset_seen()
    return {"ok": True}


def check_new_posts(send_alert: bool = True) -> Dict[str, object]:
    posts = get_current_posts()
    seen = set(load_seen())

    new_posts = []
    for post in posts:
        if post.key not in seen and not post.title.startswith("[오류]"):
            new_posts.append(post)

    if send_alert and new_posts:
        token = get_telegram_token()
        chat_id = get_telegram_chat_id()

        for post in reversed(new_posts):
            message = (
                f"🔔 미샵 CS 새글 알림\n\n"
                f"게시판: {post.board_name}\n"
                f"제목: {post.title}\n"
                f"링크: {post.url}"
            )
            send_telegram_message(token, chat_id, message)

    all_keys = [p.key for p in posts if not p.title.startswith("[오류]")]
    save_seen(all_keys)

    return {
        "new_count": len(new_posts),
        "total": len(posts),
        "new_posts": new_posts,
    }


def main():
    result = check_new_posts(send_alert=True)
    print(f"new_count={result['new_count']}, total={result['total']}")


if __name__ == "__main__":
    main()
