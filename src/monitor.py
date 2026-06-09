from typing import Dict, List

from src.cafe24_board import BoardPost, fetch_all_boards
from src.config import (
    get_board_urls,
    get_smartstore_qna_url,
    get_telegram_chat_id,
    get_telegram_token,
)
from src.smartstore_qna import fetch_smartstore_qna
from src.state import load_seen, reset_seen, save_seen, state_exists
from src.telegram_alert import send_telegram_message


def get_current_posts() -> List[BoardPost]:
    posts = fetch_all_boards(get_board_urls(), limit_per_board=30)

    smartstore_url = get_smartstore_qna_url()
    if smartstore_url:
        posts.extend(fetch_smartstore_qna(smartstore_url, limit=10))

    posts.sort(key=lambda p: p.sort_value, reverse=True)
    return posts


def _valid_posts(posts: List[BoardPost]) -> List[BoardPost]:
    return [p for p in posts if not p.title.startswith("[오류]") and p.key]


def _is_smartstore_post(p: BoardPost) -> bool:
    return p.board_name == "스마트스토어문의" or p.key.startswith("smartstore|")


def initialize_current_posts() -> Dict[str, object]:
    posts = get_current_posts()
    valid = _valid_posts(posts)
    save_seen([p.key for p in valid])
    return {"saved": len(valid), "total": len(posts), "posts": posts}


def reset_state() -> Dict[str, object]:
    reset_seen()
    return {"ok": True}


def _message_for_post(p: BoardPost) -> str:
    if _is_smartstore_post(p):
        return (
            "🔔 스마트스토어 새 문의\n\n"
            f"문의일: {p.date_text or '확인불가'}\n"
            f"작성자: {p.post_id or '확인불가'}\n"
            f"링크: {p.url}"
        )

    return (
        "🔔 미샵 CS 새글 알림\n\n"
        f"게시판: {p.board_name}\n"
        f"제목: {p.title}\n"
        f"작성일: {p.date_text or '확인불가'}\n"
        f"ID: {p.post_id}\n"
        f"링크: {p.url}"
    )


def check_new_posts(send_alert: bool = True, initialize_if_missing: bool = True) -> Dict[str, object]:
    posts = get_current_posts()
    valid = _valid_posts(posts)

    if initialize_if_missing and not state_exists():
        save_seen([p.key for p in valid])
        return {
            "new_count": 0,
            "total": len(posts),
            "new_posts": [],
            "posts": posts,
            "initialized": True,
            "message": "state.json이 없어 현재 글을 기준값으로 저장했습니다. 다음 실행부터 새글 알림이 발송됩니다.",
        }

    seen = set(load_seen())

    # 스마트스토어 기능을 처음 추가한 실행에서는 현재 보이는 스마트스토어 문의를 기준값으로만 저장합니다.
    # 그래야 과거 문의가 한꺼번에 알림으로 쏟아지지 않습니다.
    smartstore_posts = [p for p in valid if _is_smartstore_post(p)]
    smartstore_already_initialized = any(str(k).startswith("smartstore|") for k in seen)
    smartstore_keys_to_initialize = []
    if smartstore_posts and not smartstore_already_initialized:
        smartstore_keys_to_initialize = [p.key for p in smartstore_posts]
        seen.update(smartstore_keys_to_initialize)
        print(f"SMARTSTORE_INITIALIZED {len(smartstore_keys_to_initialize)}")

    new_posts = [p for p in valid if p.key not in seen]

    if send_alert and new_posts:
        token = get_telegram_token()
        chat_id = get_telegram_chat_id()
        for p in reversed(new_posts):
            send_telegram_message(token, chat_id, _message_for_post(p))

    save_seen(list(seen) + [p.key for p in valid])
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
    print("CURRENT POSTS")
    counts = {}
    for p in result.get("posts", []):
        counts[p.board_name] = counts.get(p.board_name, 0) + 1
    print(f"BOARD_COUNTS {counts}")
    for p in result.get("posts", [])[:30]:
        print(f"POST {p.sort_value} {p.board_name} {p.post_id} {p.date_text} {p.title} {p.url}")
    for p in result.get("new_posts", []):
        print(f"NEW {p.board_name} {p.post_id} {p.title} {p.url}")


if __name__ == "__main__":
    main()
