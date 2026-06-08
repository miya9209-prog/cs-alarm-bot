from __future__ import annotations
from datetime import datetime, timezone, timedelta
from .config import board_urls, telegram_bot_token, telegram_chat_id
from .cafe24_board import fetch_all_boards, BoardPost
from .telegram_alert import send_telegram_message
from .state import load_seen, save_seen

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


def run_monitor(send_alerts: bool = True, initialize_only: bool = False) -> dict:
    urls = board_urls()
    if not urls:
        return {"ok": False, "message": "BOARD_URLS가 비어 있습니다.", "new_count": 0, "posts": []}

    posts = fetch_all_boards(urls, limit_per_board=10)
    seen = load_seen()

    if not seen:
        # First run: save current posts so old posts are not all sent as new.
        save_seen({p.key for p in posts})
        return {
            "ok": True,
            "message": "초기 실행입니다. 현재 게시글을 기준값으로 저장했습니다. 다음 새글부터 알림을 보냅니다.",
            "new_count": 0,
            "posts": posts,
        }

    new_posts = [p for p in posts if p.key not in seen and not p.title.startswith("[오류]")]
    sent = []
    errors = []

    if initialize_only:
        seen.update(p.key for p in posts)
        save_seen(seen)
        return {"ok": True, "message": "현재 게시글을 기준값으로 저장했습니다.", "new_count": 0, "posts": posts}

    if send_alerts:
        token = telegram_bot_token()
        chat_id = telegram_chat_id()
        for post in reversed(new_posts):
            ok, msg = send_telegram_message(token, chat_id, format_post_message(post))
            if ok:
                sent.append(post)
            else:
                errors.append(msg)

    seen.update(p.key for p in posts)
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
    result = run_monitor(send_alerts=True)
    print(result["message"])
    print(f"new_count={result.get('new_count', 0)}")
