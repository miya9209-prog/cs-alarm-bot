import hashlib
import re
from datetime import datetime
from typing import List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from src.cafe24_board import BoardPost

DEFAULT_SMARTSTORE_QNA_URL = "https://smartstore.naver.com/misharp2006/qna"


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _make_key(author: str, date_text: str, row_text: str) -> str:
    raw = f"smartstore|{_norm_text(author)}|{_norm_text(date_text)}|{_norm_text(row_text)[:200]}"
    return "smartstore|" + hashlib.md5(raw.encode("utf-8")).hexdigest()


def _extract_date(text: str) -> str:
    # 스마트스토어 공개 Q&A는 보통 YYYY.MM.DD. 형태로 표시됩니다.
    m = re.search(r"(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})\.?(?:\s+(\d{1,2}:\d{2}))?", text)
    if not m:
        return ""
    y, mo, d, hm = m.groups()
    base = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return f"{base} {hm}" if hm else base


def _date_sort_value(date_text: str, fallback_idx: int) -> int:
    # 최신순 페이지에서 같은 날짜가 여러 개일 때는 화면 순서를 유지하기 위해 fallback을 보정합니다.
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_text, fmt)
            return int(dt.strftime("%Y%m%d%H%M")) * 1000 - fallback_idx
        except Exception:
            pass
    return 8_000_000_000 - fallback_idx


def _extract_author(text: str) -> str:
    # banj*****, rika**** 형태를 우선 추출합니다.
    patterns = [
        r"\b([A-Za-z0-9_.\-]{2,20}\*{2,})\b",
        r"\b([가-힣A-Za-z0-9_.\-]{2,20}\*{1,})\b",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return "확인불가"


def _candidate_container(tag: Tag) -> Tag:
    # 답변상태/날짜/작성자가 함께 들어있는 행 단위 컨테이너를 찾습니다.
    cur: Optional[Tag] = tag
    best: Tag = tag
    for _ in range(10):
        if cur is None:
            break
        txt = _norm_text(cur.get_text(" ", strip=True))
        if _extract_date(txt) and re.search(r"\*{2,}", txt) and ("답변" in txt or len(txt) < 800):
            best = cur
            # 너무 큰 컨테이너까지 올라가지 않도록 적당한 크기에서 멈춥니다.
            if 30 <= len(txt) <= 700:
                return cur
        cur = cur.parent if isinstance(cur.parent, Tag) else None
    return best


def _collect_rows_from_status(soup: BeautifulSoup) -> List[Tag]:
    rows: List[Tag] = []
    seen: set[int] = set()
    status_re = re.compile(r"답변\s*(완료|대기|접수|중)")

    for node in soup.find_all(string=status_re):
        parent = node.parent
        if not isinstance(parent, Tag):
            continue
        row = _candidate_container(parent)
        row_id = id(row)
        row_text = _norm_text(row.get_text(" ", strip=True))
        if row_id in seen:
            continue
        if not _extract_date(row_text):
            continue
        if "답변" not in row_text:
            continue
        seen.add(row_id)
        rows.append(row)
    return rows


def _collect_rows_line_fallback(soup: BeautifulSoup) -> List[str]:
    # HTML 구조가 바뀌어 row 태그 탐색이 실패할 때를 대비한 보조 파서입니다.
    text = soup.get_text("\n", strip=True)
    lines = [_norm_text(x) for x in text.splitlines() if _norm_text(x)]
    chunks: List[str] = []
    for i, line in enumerate(lines):
        if not re.match(r"답변\s*(완료|대기|접수|중)", line):
            continue
        chunk = " ".join(lines[i:i + 8])
        if _extract_date(chunk):
            chunks.append(chunk)
    return chunks


def fetch_smartstore_qna(qna_url: str = DEFAULT_SMARTSTORE_QNA_URL, limit: int = 10) -> List[BoardPost]:
    if not qna_url:
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://smartstore.naver.com/",
    }

    posts: List[BoardPost] = []
    seen_keys: set[str] = set()

    try:
        res = requests.get(qna_url, headers=headers, timeout=25)
        res.raise_for_status()
        res.encoding = res.apparent_encoding or "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        row_texts: List[str] = []
        for row in _collect_rows_from_status(soup):
            txt = _norm_text(row.get_text(" ", strip=True))
            if txt and txt not in row_texts:
                row_texts.append(txt)

        if not row_texts:
            row_texts = _collect_rows_line_fallback(soup)

        print(f"SMARTSTORE_RAW_COUNT {len(row_texts)}")

        for idx, row_text in enumerate(row_texts[:limit]):
            date_text = _extract_date(row_text)
            author = _extract_author(row_text)
            if not date_text and author == "확인불가":
                continue

            key = _make_key(author, date_text, row_text)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            posts.append(
                BoardPost(
                    board_name="스마트스토어문의",
                    title="스마트스토어 새 문의",
                    url=qna_url,
                    key=key,
                    post_id=author,
                    board_no="smartstore",
                    post_no=0,
                    date_text=date_text or "확인불가",
                    sort_value=_date_sort_value(date_text, idx),
                )
            )

        print(f"SMARTSTORE_FETCHED {len(posts)}")
        return posts

    except Exception as e:
        print(f"SMARTSTORE_ERROR_TYPE {type(e).__name__}")
        print(f"SMARTSTORE_ERROR_MESSAGE {str(e)[:500]}")
        return [
            BoardPost(
                board_name="오류",
                title=f"[오류] 스마트스토어 문의 확인 실패: {type(e).__name__}",
                url=qna_url,
                key="smartstore|error",
                post_id="ERROR",
                board_no="smartstore",
                post_no=0,
                date_text="",
                sort_value=0,
            )
        ]
