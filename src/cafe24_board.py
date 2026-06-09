import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


@dataclass(frozen=True)
class BoardPost:
    board_name: str
    title: str
    url: str
    key: str
    post_id: str
    board_no: str
    post_no: int
    date_text: str = ""
    sort_value: int = 0


def _norm_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
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
    raw = f"{board_no}|{post_no or url}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _post_id_from_url(url: str) -> Optional[tuple[str, str]]:
    parsed = urlparse(url)
    path = parsed.path
    qs = parse_qs(parsed.query)

    # 후기/포토후기: /board/review/read_photo.html?board_no=4&no=606983
    if "read_photo.html" in path or "read.html" in path:
        board_no = (qs.get("board_no") or [""])[0]
        post_no = (qs.get("no") or [""])[0]
        if board_no and post_no:
            return board_no, post_no

    # 상품문의/이벤트: /article/상품문의/6/606987/ , /article/이벤트/39/606730/categoryno/1/
    m = re.search(r"/article/[^/]+/(\d+)/(\d+)(?:/|$)", path)
    if m:
        return m.group(1), m.group(2)

    return None


def _is_noise_url(url: str) -> bool:
    # 상품/카테고리/회원/검색 링크는 게시글이 아니므로 제외
    bad = [
        "/product/list.html",
        "/product/search.html",
        "/product/detail.html",
        "/member/",
        "/order/",
        "/myshop/",
        "/exec/front/",
        "cate_no=",
        "keyword=",
    ]
    parsed = urlparse(url)
    path = parsed.path
    # article 게시글의 categoryno는 허용
    if "/article/" in path and re.search(r"/article/[^/]+/\d+/\d+", path):
        return False
    return any(x in url for x in bad)


def _is_notice_or_reply(title: str, full_url: str, row_text: str) -> bool:
    t = _norm_text(title)
    r = _norm_text(row_text)
    if "공지" in t or r.startswith("공지 ") or " 공지 " in r[:20]:
        return True
    if "답변드려요" in t:
        return True
    if t in {"글쓰기", "목록", "수정", "삭제", "답변쓰기", "전체보기", "포토", "리스트"}:
        return True
    return False


def _candidate_container(a: Tag) -> Tag:
    # 게시판 테이블은 tr 단위, 포토후기는 li/div 단위인 경우가 많다.
    for name in ["tr", "li", "div"]:
        parent = a.find_parent(name)
        if parent is not None:
            txt = parent.get_text(" ", strip=True)
            if len(txt) >= len(a.get_text(" ", strip=True)):
                return parent
    return a


def _extract_date_from_text(text: str) -> str:
    m = re.search(r"(20\d{2})[-./](\d{1,2})[-./](\d{1,2})", text)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    m = re.search(r"(\d{2})[-./](\d{1,2})[-./](\d{1,2})", text)
    if m:
        y, mo, d = m.groups()
        return f"20{int(y):02d}-{int(mo):02d}-{int(d):02d}"
    return ""


def _date_near_anchor(a: Tag) -> str:
    # 1) 같은 행/카드에서 날짜 찾기
    node: Optional[Tag] = a
    for _ in range(5):
        if node is None:
            break
        text = node.get_text(" ", strip=True)
        date_text = _extract_date_from_text(text)
        if date_text:
            return date_text
        node = node.parent if isinstance(node.parent, Tag) else None
    # 2) 다음 형제 주변에서 날짜 찾기
    for sib in a.find_all_next(string=True, limit=12):
        date_text = _extract_date_from_text(str(sib))
        if date_text:
            return date_text
    return ""


def _sort_value(date_text: str, post_no: str) -> int:
    # 날짜가 있으면 날짜 우선 + 글번호. 날짜가 없으면 글번호만 사용.
    try:
        post_int = int(post_no)
    except Exception:
        post_int = 0
    if date_text:
        try:
            dt = datetime.strptime(date_text, "%Y-%m-%d")
            return int(dt.strftime("%Y%m%d")) * 10_000_000 + post_int
        except Exception:
            pass
    return post_int


def _clean_title(title: str) -> str:
    t = _norm_text(title)
    # 카페24 비밀글/NEW 이미지 alt가 제목에 붙는 경우 정리
    t = t.replace("비밀글", "").replace("NEW", "").replace("HIT", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


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
        title = _clean_title(raw_title)
        if not title or len(title) < 2:
            continue

        full_url = urljoin(board_url, a.get("href", ""))
        if _is_noise_url(full_url):
            continue

        ids = _post_id_from_url(full_url)
        if not ids:
            continue
        board_no, post_no = ids

        if wanted_board_no and board_no != wanted_board_no:
            continue

        container = _candidate_container(a)
        row_text = container.get_text(" ", strip=True)
        if _is_notice_or_reply(title, full_url, row_text):
            continue

        unique_post = f"{board_no}:{post_no}"
        if unique_post in seen_ids:
            continue
        seen_ids.add(unique_post)

        date_text = _date_near_anchor(a)
        key = _make_key(board_no, post_no, full_url)
        posts.append(
            BoardPost(
                board_name=board_name,
                title=title,
                url=full_url,
                key=key,
                post_id=unique_post,
                board_no=board_no,
                post_no=int(post_no) if str(post_no).isdigit() else 0,
                date_text=date_text,
                sort_value=_sort_value(date_text, post_no),
            )
        )
        if len(posts) >= limit:
            break

    # 각 게시판 내부도 최신순으로 정렬
    posts.sort(key=lambda p: p.sort_value, reverse=True)
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
                    board_no="",
                    post_no=0,
                    date_text="",
                    sort_value=0,
                )
            )
    # 전체 게시판을 한꺼번에 최신순 정렬
    all_posts.sort(key=lambda p: p.sort_value, reverse=True)
    return all_posts
