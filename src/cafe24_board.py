import hashlib
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass
class BoardPost:
    board_url: str
    title: str
    link: str
    unique_id: str


def _make_id(title: str, link: str) -> str:
    raw = f"{title}|{link}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def fetch_board_posts(board_url: str, limit: int = 20) -> List[BoardPost]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    response = requests.get(board_url, headers=headers, timeout=15)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")
    posts: List[BoardPost] = []
    seen = set()

    links = soup.select(
        'a[href*="/board/"], '
        'a[href*="read.html"], '
        'a[href*="product_no"], '
        'a[href*="no="]'
    )

    skip_words = [
        "로그인", "회원가입", "마이쇼핑", "장바구니", "주문조회",
        "검색", "목록", "쓰기", "수정", "삭제", "답변", "이전", "다음",
        "공지", "이벤트", "상품정보", "확대보기", "게시판", "상품후기",
        "상품문의", "포토후기", "REVIEW", "Q&A"
    ]

    for a in links:
        title = a.get_text(" ", strip=True)
        href = a.get("href", "").strip()

        if not title or not href:
            continue

        if title in skip_words:
            continue

        if len(title) < 2:
            continue

        full_link = urljoin(board_url, href)

        if not (
            "read.html" in full_link
            or "no=" in full_link
            or "board_no=" in full_link
        ):
            continue

        unique_key = f"{title}|{full_link}"
        if unique_key in seen:
            continue

        seen.add(unique_key)

        posts.append(
            BoardPost(
                board_url=board_url,
                title=title,
                link=full_link,
                unique_id=_make_id(title, full_link),
            )
        )

        if len(posts) >= limit:
            break

    return posts


def fetch_all_boards(board_urls: List[str], limit_per_board: int = 20) -> List[BoardPost]:
    all_posts: List[BoardPost] = []

    for board_url in board_urls:
        try:
            posts = fetch_board_posts(board_url, limit=limit_per_board)
            all_posts.extend(posts)
        except Exception as e:
            print(f"[ERROR] Failed to fetch board: {board_url} / {e}")

    return all_posts
