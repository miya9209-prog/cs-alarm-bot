import hashlib
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


@dataclass
class BoardPost:
    board_name: str
    title: str
    url: str
    key: str


def make_key(title: str, url: str) -> str:
    return hashlib.md5(f"{title}|{url}".encode("utf-8")).hexdigest()


def get_board_name(board_url: str) -> str:
    if "board_no=4" in board_url:
        return "포토후기"
    if "board_no=6" in board_url:
        return "상품문의"
    if "board_no=39" in board_url:
        return "갤러리"
    return "게시판"


def fetch_board_posts(board_url: str, limit: int = 10) -> List[BoardPost]:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    res = requests.get(board_url, headers=headers, timeout=15)
    res.raise_for_status()
    res.encoding = res.apparent_encoding

    soup = BeautifulSoup(res.text, "html.parser")
    board_name = get_board_name(board_url)

    posts = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        title = a.get_text(" ", strip=True)

        if not title or len(title) < 2:
            continue

        full_url = urljoin(board_url, href)

        # 실제 게시글 URL만 수집
        is_post = (
            "read.html" in full_url
            or "read_photo.html" in full_url
            or "/board/review/" in full_url and "no=" in full_url
            or "/board/product/" in full_url and "no=" in full_url
            or "/board/gallery/" in full_url and "no=" in full_url
        )

        if not is_post:
            continue

        # 카테고리/상품목록 제외
        if "product/list.html" in full_url:
            continue
        if "cate_no=" in full_url:
            continue

        key = make_key(title, full_url)

        if key in seen:
            continue

        seen.add(key)

        posts.append(
            BoardPost(
                board_name=board_name,
                title=title,
                url=full_url,
                key=key,
            )
        )

        if len(posts) >= limit:
            break

    return posts


def fetch_all_boards(board_urls: List[str], limit_per_board: int = 10) -> List[BoardPost]:
    all_posts = []

    for board_url in board_urls:
        try:
            all_posts.extend(fetch_board_posts(board_url, limit_per_board))
        except Exception as e:
            print(f"[ERROR] {board_url}: {e}")

    return all_posts
