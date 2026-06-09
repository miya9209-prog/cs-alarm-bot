import hashlib
import re
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class BoardPost:
    board_name: str
    title: str
    url: str
    key: str
    board_url: str = ""
    link: str = ""
    unique_id: str = ""


def make_key(board_name: str, title: str, url: str) -> str:
    # URL에 글번호가 들어가므로 제목이 바뀌어도 같은 글로 인식하기 위해 URL 중심으로 생성
    canonical = url.split("#")[0].rstrip("/")
    return hashlib.md5(f"{board_name}|{canonical}".encode("utf-8")).hexdigest()


def get_board_no(board_url: str) -> str:
    match = re.search(r"board_no=(\d+)", board_url)
    return match.group(1) if match else ""


def get_board_name(board_url: str) -> str:
    board_no = get_board_no(board_url)
    if board_no == "4":
        return "포토후기"
    if board_no == "6":
        return "상품문의"
    if board_no == "39":
        return "이벤트/갤러리"
    return f"게시판{board_no}" if board_no else "게시판"


def normalize_title(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    # NEW, HIT 같은 이미지 alt가 섞일 수 있어 불필요한 짧은 문구 정리
    return text


def is_noise_title(title: str) -> bool:
    if not title:
        return True

    exact_noise = {
        "LOGIN", "JOIN", "MYPAGE", "CART", "ABOUT", "SHOP", "SPECIAL",
        "TIME SALE", "COMMUNITY", "NOTICE", "REVIEW", "Q & A", "FAQ",
        "EVENT", "출석체크", "검색", "목록", "글쓰기", "쓰기", "수정",
        "삭제", "답변쓰기", "전체보기", "포토", "리스트", "게시판",
        "홈", "상품보기", "장바구니 이동", "이용약관", "개인정보처리방침",
        "이용안내", "상세보기",
    }
    if title in exact_noise:
        return True

    # 상품 카테고리명, 메뉴명 제외
    category_words = [
        "베스트50", "미샵제작", "신상", "티셔츠", "블라우스", "셔츠",
        "원피스", "스커트", "니트", "가디건", "팬츠", "아우터",
        "코디아이템", "세일", "화장품", "데일리/필수템",
    ]
    if title in category_words:
        return True

    # 너무 짧은 숫자/기호만 있는 텍스트 제외
    if len(title) < 2:
        return True

    return False


def is_target_post_url(full_url: str, board_no: str) -> bool:
    parsed = urlparse(full_url)
    path = parsed.path
    query = parsed.query

    # 상품 카테고리/상품 리스트/로그인 등 제외
    bad_fragments = [
        "/product/list.html", "/product/detail.html", "/member/",
        "/order/", "/myshop/", "/shopinfo/", "/board/free/list.html",
    ]
    if any(x in path for x in bad_fragments):
        return False
    if "cate_no=" in query:
        return False

    # 포토후기: /board/review/read_photo.html?board_no=4&no=606983
    if board_no == "4":
        return (
            "/board/review/read_photo.html" in path
            and "board_no=4" in query
            and "no=" in query
        )

    # 상품문의: /article/상품문의/6/606987/ 또는 read.html 계열
    if board_no == "6":
        if re.search(r"/article/[^/]+/6/\d+/?", path):
            return True
        return (
            "/board/product/read.html" in path
            and "board_no=6" in query
            and "no=" in query
        )

    # 이벤트/갤러리: /article/이벤트/39/601108/categoryno/1/
    if board_no == "39":
        if re.search(r"/article/[^/]+/39/\d+/?", path):
            return True
        return (
            ("/board/gallery/read.html" in path or "/board/gallery/read2.html" in path)
            and "board_no=39" in query
            and "no=" in query
        )

    # 기타 카페24 게시판 fallback
    return (
        ("/read.html" in path or "/read_photo.html" in path)
        and f"board_no={board_no}" in query
        and "no=" in query
    )


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def fetch_board_posts(board_url: str, limit: int = 10) -> List[BoardPost]:
    board_no = get_board_no(board_url)
    board_name = get_board_name(board_url)

    html = fetch_html(board_url)
    soup = BeautifulSoup(html, "html.parser")

    posts: List[BoardPost] = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        full_url = urljoin(board_url, href).split("#")[0]

        if not is_target_post_url(full_url, board_no):
            continue

        title = normalize_title(a.get_text(" ", strip=True))
        if is_noise_title(title):
            # 링크 안의 텍스트가 비어 있거나 이미지 alt만 있는 경우는 제외
            continue

        # 답변글은 새 문의/새 후기 알림 대상에서 제외
        if "답변드려요" in title or title.startswith("RE:"):
            continue

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        key = make_key(board_name, title, full_url)
        posts.append(
            BoardPost(
                board_name=board_name,
                title=title,
                url=full_url,
                key=key,
                board_url=board_url,
                link=full_url,
                unique_id=key,
            )
        )

        if len(posts) >= limit:
            break

    return posts


def fetch_all_boards(board_urls: List[str], limit_per_board: int = 10) -> List[BoardPost]:
    all_posts: List[BoardPost] = []

    for board_url in board_urls:
        try:
            all_posts.extend(fetch_board_posts(board_url, limit=limit_per_board))
        except Exception as e:
            board_name = get_board_name(board_url)
            message = f"[오류] {board_name}: {e}"
            key = make_key(board_name, message, board_url)
            all_posts.append(
                BoardPost(
                    board_name=board_name,
                    title=message,
                    url=board_url,
                    key=key,
                    board_url=board_url,
                    link=board_url,
                    unique_id=key,
                )
            )

    return all_posts
