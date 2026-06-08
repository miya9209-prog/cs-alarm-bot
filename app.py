from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin
import hashlib
import requests
from bs4 import BeautifulSoup


@dataclass
class BoardPost:
    post_id: str
    board_name: str
    title: str
    author: str
    created_at: str
    url: str


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def fetch_posts_from_board_page(board_url: str, limit: int = 20) -> List[BoardPost]:
    """
    카페24 게시판 목록 페이지를 읽어 새글 후보를 가져옵니다.
    쇼핑몰 스킨마다 HTML 구조가 다르므로, 실제 미샵 게시판 구조에 맞춰 selector 조정이 필요할 수 있습니다.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MisharpCSAlertBot/1.0)",
    }
    r = requests.get(board_url, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    board_name = _text(soup.select_one("h2, .title h2, .board_title, .path ol li:last-child")) or "CS 게시판"
    rows = soup.select("table tbody tr")
    posts: List[BoardPost] = []

    for row in rows:
        link = row.select_one("a[href*='read.html'], a[href*='article'], a[href]")
        title = _text(link)
        if not link or not title or "공지" in title:
            continue

        href = link.get("href", "")
        full_url = urljoin(board_url, href)
        cells = [_text(td) for td in row.select("td")]
        author = cells[2] if len(cells) >= 3 else ""
        created_at = cells[3] if len(cells) >= 4 else ""
        raw_id = full_url or f"{board_url}|{title}|{author}|{created_at}"
        post_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24]

        posts.append(BoardPost(
            post_id=post_id,
            board_name=board_name,
            title=title,
            author=author,
            created_at=created_at,
            url=full_url,
        ))
        if len(posts) >= limit:
            break
    return posts
