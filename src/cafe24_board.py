import hashlib
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass
class BoardPost:
    board_name: str
    board_url: str
    title: str
    link: str
    unique_id: str


def _make_id(title: str, link: str) -> str:
    raw = f"{title}|{link}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _get_board_name(board_url: str) -> str:
    if "board_no=4" in board_url:
        return "포토후기"
    if "board_no=6" in board_url:
        return "상품문의"
    if "board_no=39" in board_url:
        return "갤러리"
    return "게시판"


def fetch_board_posts(board_url: str, limit: int = 20) -> List[BoardPost]:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    response = requests.get(board_url, headers=headers, timeout=15)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")
    posts: List[BoardPost] = []
    seen = set()
    board_name = _get_board_name(board_url)

    links = soup.select('a[href*="/board/"], a[href*="read.html"], a[href*="no="]')

    for a in links:
        title = a.get_text(" ", strip=True)
        href = a.get("href", "").strip()

        if not title or not href or len(title) < 2:
            continue

        if title in ["로그인", "회원가입", "장바구니", "검색", "목록", "쓰기", "수정", "삭제", "답변", "이전", "다음"]:
            continue

        full_link = urljoin(board_url, href)

        if "read.html" not in full_link and "no=" not in full_link:
            continue

        key = f"{title}|{full_link}"
        if key in seen:
            continue

        seen.add(key)
        posts.append(
            BoardPost(
                board_name=board_name,
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
            all_posts.extend(fetch_board_posts(board_url, limit=limit_per_board))
        except Exception as e:
            print(f"[ERROR] {board_url} / {e}")

    return all_posts
