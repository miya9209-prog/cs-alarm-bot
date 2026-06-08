from __future__ import annotations
from datetime import datetime, timezone, timedelta
from .config import board_urls, telegram_bot_token, telegram_chat_id
from .cafe24_board import fetch_all_boards, BoardPost
from .telegram_alert import send_telegram_message
from .state import load_seen, save_seen, state_exists

KST = timezone(timedelta(hours=9))


def format_post_message(post: BoardPost) -> str:
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    parts = [
        "🔔 미샵 CS 게시판 새글 알림",
        "",
        f"게시판: {post.board_name}",
        f"제목: {post.title}",
    ]
    if post.writer:
        parts.append(f"작성자: {post.writer}")
    if post.date:
        parts.append(f"작성일: {post.date}")
    parts.extend(["", f"바로가기: {post.url}", f"확인시간: {now}"])
    return "\n".join(parts)


def initialize_current_posts() -> dict:
    urls = board_urls()
    if not urls:
        return {"ok": False, "message": "BOARD_URLS가 비어 있습니다.", "new_count": 0, "posts": []}
    posts = fetch_all_boards(urls, limit_per_board=10)
    save_seen({p.key for p in posts if not p.title.startswith("[오류]")})
    return {"ok": True, "message": "현재 게시글을 기준값으로 저장했습니다. 이제 이후 새글부터 알림이 갑니다.", "new_count": 0, "posts": posts}


def run_monitor(send_alerts: bool = True, initialize_only: bool = False, first_run_send_current: bool = False) -> dict:
    urls = board_urls()
    if not urls:
        return {"ok": False, "message": "BOARD_URLS가 비어 있습니다.", "new_count": 0, "posts": []}

    posts = fetch_all_boards(urls, limit_per_board=10)
    current_keys = {p.key for p in posts if not p.title.startswith("[오류]")}

    if initialize_only:
        save_seen(current_keys)
        return {"ok": True, "message": "현재 게시글을 기준값으로 저장했습니다. 이제 이후 새글부터 알림이 갑니다.", "new_count": 0, "posts": posts}

    seen = load_seen()
    first_run = not state_exists() or not seen

    if first_run and not first_run_send_current:
        # GitHub Actions first run: prevent old posts from flooding Telegram.
        save_seen(current_keys)
        return {
            "ok": True,
            "message": "첫 실행이라 현재 게시글을 기준값으로 저장했습니다. 다음 새글부터 알림을 보냅니다.",
            "new_count": 0,
            "posts": posts,
            "new_posts": [],
        }

    if first_run and first_run_send_current:
        new_posts = [p for p in posts if not p.title.startswith("[오류]")]
    else:
        new_posts = [p for p in posts if p.key not in seen and not p.title.startswith("[오류]")]

    sent = []
    errors = []

    if send_alerts:
        token = telegram_bot_token()
        chat_id = telegram_chat_id()
        for post in reversed(new_posts):
            ok, msg = send_telegram_message(token, chat_id, format_post_message(post))
            if ok:
                sent.append(post)
            else:
                errors.append(msg)

    seen.update(current_keys)
    save_seen(seen)

    return {
        "ok": len(errors) == 0,
        "message": "완료" if not errors else " / ".join(errors),
        "new_count": len(new_posts),
        "sent_count": len(sent),
        "posts": posts,
        "new_posts": new_posts,
    }


if __name__ == "__main__":
    # GitHub Actions uses safe mode: first run saves baseline only.
    result = run_monitor(send_alerts=True, first_run_send_current=False)
    print(result["message"])
    print(f"new_count={result.get('new_count', 0)}")
    print(f"sent_count={result.get('sent_count', 0)}")
