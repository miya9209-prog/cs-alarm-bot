from typing import List
from .config import BOARD_URLS, CHECK_LIMIT
from .cafe24_board import BoardPost, fetch_posts_from_board_page
from .state import load_notified_ids, save_notified_ids
from .telegram_notify import send_telegram_message


def format_message(post: BoardPost) -> str:
    return (
        "🔔 <b>미샵 새 CS 문의</b>\n"
        f"게시판 : {post.board_name}\n"
        f"제목 : {post.title}\n"
        f"작성자 : {post.author or '-'}\n"
        f"시간 : {post.created_at or '-'}\n\n"
        f"바로가기\n{post.url}"
    )


def collect_posts() -> List[BoardPost]:
    posts: List[BoardPost] = []
    for url in BOARD_URLS:
        try:
            posts.extend(fetch_posts_from_board_page(url, CHECK_LIMIT))
        except Exception as e:
            print(f"게시판 확인 실패: {url} / {e}")
    return posts


def run_check(send_alert: bool = True) -> List[BoardPost]:
    notified = load_notified_ids()
    posts = collect_posts()
    new_posts = [p for p in posts if p.post_id not in notified]

    # 오래된 글부터 알림 발송
    for post in reversed(new_posts):
        if send_alert:
            send_telegram_message(format_message(post))
        notified.add(post.post_id)

    save_notified_ids(notified)
    return new_posts


if __name__ == "__main__":
    new_posts = run_check(send_alert=True)
    print(f"새 글 {len(new_posts)}건 확인")
