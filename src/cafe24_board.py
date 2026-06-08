from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, parse_qs
import re
import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class BoardPost:
    board_url: str
    board_name: str
    title: str
    url: str
    writer: str = ""
    date: str = ""

    @property
    def key(self) -> str:
        return f"{self.board_name}|{self.url}|{self.title}"


def infer_board_name(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    board_no = (qs.get("board_no") or [""])[0]
    category_no = (qs.get("category_no") or [""])[0]
    if board_no == "4":
        return "포토후기/리뷰"
    if board_no == "6":
        return "상품문의/Q&A"
    if board_no == "39":
        return "갤러리/CS게시판" + (f" 카테고리{category_no}" if category_no else "")
    return f"게시판 {board_no}" if board_no else "게시판"


def fetch_board_posts(board_url: str, limit: int = 10) -> list[BoardPost]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }
    res = requests.get(board_url, headers=headers, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    board_name = infer_board_name(board_url)

    posts: list[BoardPost] = []
    seen: set[str] = set()

    # Cafe24 board links usually contain /board/.../read.html or board_no + no.
    for a in soup.select('a[href]'):
        href = a.get('href', '').strip()
        title = a.get_text(' ', strip=True)
        if not title or len(title) < 2:
            continue
        if 'read.html' not in href and not re.search(r'[?&]no=\d+', href):
            continue
        if 'board' not in href:
            continue
        abs_url = urljoin(board_url, href)
        key = abs_url.split('#')[0]
        if key in seen:
            continue
        seen.add(key)

        # Remove common noise
        title = re.sub(r'\s+', ' ', title).strip()
        if title in {"수정", "삭제", "답변", "이전", "다음"}:
            continue

        writer = ""
        date = ""
        tr = a.find_parent('tr')
        if tr:
            cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
            # Best effort: Cafe24 often has no/title/writer/date/view
            if len(cells) >= 3:
                writer = cells[-3] if len(cells) >= 5 else ""
                date = cells[-2] if len(cells) >= 4 else ""

        posts.append(BoardPost(board_url=board_url, board_name=board_name, title=title, url=abs_url, writer=writer, date=date))
        if len(posts) >= limit:
            break

    return posts


def fetch_all_boards(board_urls: list[str], limit_per_board: int = 10) -> list[BoardPost]:
    all_posts: list[BoardPost] = []
    for url in board_urls:
        try:
            all_posts.extend(fetch_board_posts(url, limit=limit_per_board))
        except Exception as e:
            all_posts.append(BoardPost(board_url=url, board_name=infer_board_name(url), title=f"[오류] 게시판 확인 실패: {e}", url=url))
    return all_posts
