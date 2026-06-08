import hashlib
import re
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
    url: str
    key: str
    unique_id: str


def _make_id(title: str, link: str) -> str:
    return hashlib.md5(f"{title}|{link}".encode("utf-8")).hexdigest()


def _get_board_name(board_url: str) -> str:
    if "board_no=4" in board_url:
        return "포토후기"
    if "board_no=6" in board_url:
        return "상품문의"
    if "board_no=39" in board_url:
        return "갤러리"
    return "게시판"


def _clean_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def fetch_board_posts(board_url: str, limit: int = 20) -> List[BoardPost]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    }
    resp = requests.get(board_url, headers=headers, timeout=20)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")

    board_name = _get_board_name(board_url)
    posts: List[BoardPost] = []
    seen = set()

    # Only real Cafe24 board post detail links, not product category links.
    candidates = soup.select('a[href*="/board/"][href*="read.html"]')

    for a in candidates:
        href = (a.get("href") or "").strip()
        full_link = urljoin(board_url, href)

        if "read.html" not in full_link:
            continue
        if "product/list.html" in full_link or "cate_no=" in full_link:
            continue
        if "board_no=" not in full_link:
            continue
        # Cafe24 board detail links usually include no= or product_no.
        if "no=" not in full_link and "product_no=" not in full_link:
            continue

        title = _clean_title(a.get_text(" ", strip=True))
        if not title or len(title) < 2:
            # Try parent row/card text if link text is only an image.
            parent = a.find_parent(["tr", "li", "div"])
            if parent:
                title = _clean_title(parent.get_text(" ", strip=True))
        if not title or len(title) < 2:
            title = "제목 없는 게시글"

        skip = ["로그인", "회원가입", "장바구니", "검색", "목록", "쓰기", "수정", "삭제", "답변", "이전", "다음"]
        if title in skip:
            continue

        post_key = _make_id(title, full_link)
        if post_key in seen:
            continue
        seen.add(post_key)

        posts.append(BoardPost(
            board_name=board_name,
            board_url=board_url,
            title=title,
            link=full_link,
            url=full_link,
            key=post_key,
            unique_id=post_key,
        ))
        if len(posts) >= limit:
            break

    return posts


def fetch_all_boards(board_urls: List[str], limit_per_board: int = 10) -> List[BoardPost]:
    all_posts: List[BoardPost] = []
    for url in board_urls:
        try:
            all_posts.extend(fetch_board_posts(url, limit=limit_per_board))
        except Exception as e:
            key = _make_id(f"[오류] {url}", str(e))
            all_posts.append(BoardPost(
                board_name="오류",
                board_url=url,
                title=f"[오류] {url} / {e}",
                link=url,
                url=url,
                key=key,
                unique_id=key,
            ))
    return all_posts
