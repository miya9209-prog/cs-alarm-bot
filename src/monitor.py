import os
from typing import Dict, List

from src.cafe24_board import BoardPost, fetch_all_boards
from src.config import get_board_urls, get_telegram_chat_id, get_telegram_token
from src.state import load_seen, reset_seen, save_seen, state_exists
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
    valid_posts = [p for p in posts if not p.title.startswith("[오류]")]

    # GitHub Actions 첫 실행 시 state.json이 없으면 전체 발송하지 않고 기준값만 저장
    # 이렇게 해야 기존 글 수십 개가 한꺼번에 알림으로 오지 않습니다.
    first_run = not state_exists()
    seen = set(load_seen())

    new_posts = []
    if not first_run:
        new_posts = [p for p in valid_posts if p.key not in seen]

    if send_alert and new_posts:
        token = get_telegram_token()
        chat_id = get_telegram_chat_id()

        # 오래된 글부터 보내야 채팅방에서 시간순으로 읽기 좋습니다.
        for p in reversed(new_posts):
            message = (
                "🔔 미샵 CS 새글 알림\n\n"
                f"게시판: {p.board_name}\n"
                f"제목: {p.title}\n"
                f"링크: {p.url}"
            )
            send_telegram_message(token, chat_id, message)

    # 확인한 최신 목록을 항상 저장해서 중복 발송을 막습니다.
    save_seen([p.key for p in valid_posts])

    return {
        "new_count": len(new_posts),
        "total": len(posts),
        "new_posts": new_posts,
        "posts": posts,
        "first_run": first_run,
    }


def main() -> None:
    result = check_new_posts(send_alert=True)
    print(
        f"first_run={result['first_run']}, "
        f"new_count={result['new_count']}, total={result['total']}"
    )


if __name__ == "__main__":
    main()
