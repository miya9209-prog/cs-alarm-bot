from typing import Dict, List

from src.cafe24_board import BoardPost, fetch_all_boards
from src.config import get_board_urls, get_telegram_chat_id, get_telegram_token
from src.state import load_seen, save_seen, reset_seen, state_exists
from src.telegram_alert import send_telegram_message


def get_current_posts() -> List[BoardPost]:
    return fetch_all_boards(get_board_urls(), limit_per_board=30)


def _valid_posts(posts: List[BoardPost]) -> List[BoardPost]:
    return [p for p in posts if not p.title.startswith("[오류]")]


def initialize_current_posts() -> Dict[str, object]:
    posts = get_current_posts()
    valid = _valid_posts(posts)
    save_seen([p.key for p in valid])
    return {"saved": len(valid), "total": len(posts), "posts": posts}


def reset_state() -> Dict[str, object]:
    reset_seen()
    return {"ok": True}


def check_new_posts(send_alert: bool = True, initialize_if_missing: bool = True) -> Dict[str, object]:
    posts = get_current_posts()
    valid = _valid_posts(posts)

    # GitHub Actions 첫 실행 때는 과거 글 30개를 모두 알림 보내지 않고 기준값만 생성
    if initialize_if_missing and not state_exists():
        save_seen([p.key for p in valid])
        return {
            "new_count": 0,
            "total": len(posts),
            "new_posts": [],
            "posts": posts,
            "initialized": True,
        }

    seen = set(load_seen())
    new_posts = [p for p in valid if p.key not in seen]

    if send_alert and new_posts:
        token = get_telegram_token()
        chat_id = get_telegram_chat_id()
        # 오래된 새글부터 순서대로 발송
        for p in reversed(new_posts):
            send_telegram_message(
                token,
                chat_id,
                f"🔔 미샵 CS 새글 알림\n\n게시판: {p.board_name}\n제목: {p.title}\n링크: {p.url}",
            )

    # 이번에 확인한 최신 30개를 기준값으로 저장
    save_seen([p.key for p in valid])
    return {
        "new_count": len(new_posts),
        "total": len(posts),
        "new_posts": new_posts,
        "posts": posts,
        "initialized": False,
    }


def main():
    result = check_new_posts(send_alert=True, initialize_if_missing=True)
    print(
        f"initialized={result.get('initialized')}, "
        f"new_count={result['new_count']}, total={result['total']}"
    )
    for p in result.get("new_posts", []):
        print(f"NEW {p.board_name} {p.post_id} {p.title} {p.url}")


if __name__ == "__main__":
    main()
