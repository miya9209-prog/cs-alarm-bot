import hashlib
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional
from urllib.parse import parse_qs, quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class BoardPost:
    board_name: str
    title: str
    url: str
    key: str
    post_id: str


def _norm_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    # 미샵 스킨에서 간혹 붙는 불필요한 말 제거
    text = re.sub(r"^\[게시판\]\s*", "", text).strip()
    return text


def _board_info(board_url: str) -> tuple[str, str]:
    if "board_no=4" in board_url or "/review/" in board_url:
        return "포토후기", "4"
    if "board_no=6" in board_url or "/상품문의/6/" in board_url or "/%EC%83%81%ED%92%88%EB%AC%B8%EC%9D%98/6/" in board_url:
        return "상품문의", "6"
    if "board_no=39" in board_url or "/이벤트/39/" in board_url or "/%EC%9D%B4%EB%B2%A4%ED%8A%B8/39/" in board_url:
        return "이벤트", "39"
    return "게시판", ""


def _make_key(board_no: str, post_no: str, url: str) -> str:
    # 제목이 수정되어도 같은 글은 같은 글로 보기 위해 게시판번호+글번호 중심으로 key 생성
    raw = f"{board_no}|{post_no or url}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _post_id_from_url(url: str) -> Optional[tuple[str, str]]:
    """Return (board_no, post_no) if url is a Cafe24 board post URL."""
    parsed = urlparse(url)
    path = parsed.path
    qs = parse_qs(parsed.query)

    # 포토후기: /board/review/read_photo.html?board_no=4&no=606983
    if "read_photo.html" in path or "read.html" in path:
        board_no = (qs.get("board_no") or [""])[0]
        post_no = (qs.get("no") or [""])[0]
        if board_no and post_no:
            return board_no, post_no

    # 상품문의/이벤트: /article/상품문의/6/606987/ , /article/이벤트/39/601108/categoryno/1/
    m = re.search(r"/article/[^/]+/(\d+)/(\d+)(?:/|$)", path)
    if m:
        return m.group(1), m.group(2)

    return None


def _is_noise_url(url: str) -> bool:
    bad = [
        "/product/list.html",
        "/product/search.html",
        "/product/detail.html",
        "/member/",
        "/order/",
        "/myshop/",
        "/exec/front/",
        "cate_no=",
        "category_no=",
        "keyword=",
    ]
    # article 이벤트 상세의 categoryno는 허용해야 함
    if "/article/" in url and re.search(r"/article/[^/]+/\d+/\d+", urlparse(url).path):
        return False
    return any(x in url for x in bad)


def _is_notice_or_reply(title: str) -> bool:
    t = _norm_text(title)
    # 공지는 알림 대상에서 제외. Q&A 답변글도 고객 새글이 아니므로 제외.
    if "공지" in t:
        return True
    if "답변드려요" in t:
        return True
    if t in {"글쓰기", "목록", "수정", "삭제", "답변쓰기", "전체보기", "포토", "리스트"}:
        return True
    return False


def fetch_board_posts(board_url: str, limit: int = 30) -> List[BoardPost]:
    board_name, wanted_board_no = _board_info(board_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    res = requests.get(board_url, headers=headers, timeout=20)
    res.raise_for_status()
    res.encoding = res.apparent_encoding or "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    posts: List[BoardPost] = []
    seen_ids: set[str] = set()

    for a in soup.find_all("a", href=True):
        raw_title = a.get_text(" ", strip=True)
        title = _norm_text(raw_title)
        if not title or len(title) < 2:
            continue

        full_url = urljoin(board_url, a.get("href", ""))
        if _is_noise_url(full_url):
            continue

        ids = _post_id_from_url(full_url)
        if not ids:
            continue
        board_no, post_no = ids

        # 현재 등록한 게시판의 글만 수집
        if wanted_board_no and board_no != wanted_board_no:
            continue

        if _is_notice_or_reply(title):
            continue

        unique_post = f"{board_no}:{post_no}"
        if unique_post in seen_ids:
            continue
        seen_ids.add(unique_post)

        key = _make_key(board_no, post_no, full_url)
        posts.append(
            BoardPost(
                board_name=board_name,
                title=title,
                url=full_url,
                key=key,
                post_id=unique_post,
            )
        )
        if len(posts) >= limit:
            break

    return posts


def fetch_all_boards(board_urls: Iterable[str], limit_per_board: int = 30) -> List[BoardPost]:
    all_posts: List[BoardPost] = []
    for board_url in board_urls:
        try:
            all_posts.extend(fetch_board_posts(board_url, limit=limit_per_board))
        except Exception as e:
            all_posts.append(
                BoardPost(
                    board_name="오류",
                    title=f"[오류] {board_url} / {e}",
                    url=board_url,
                    key=hashlib.md5(f"ERROR|{board_url}".encode("utf-8")).hexdigest(),
                    post_id="ERROR",
                )
            )
    return all_posts
