```python
import hashlib
import re
from typing import List

from src.cafe24_board import BoardPost


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _make_key(product: str, author: str, message: str) -> str:
    raw = f"crema|{_norm_text(product)}|{_norm_text(author)}|{_norm_text(message)[:80]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _safe_title(product: str, message: str) -> str:
    product = _norm_text(product) or "상품명 확인불가"
    message = _norm_text(message)
    if len(message) > 40:
        message = message[:40] + "..."
    return f"{product} / {message or '후기내용 확인불가'}"


def _error_post(review_url: str, error: Exception) -> List[BoardPost]:
    return [
        BoardPost(
            board_name="크리마후기",
            title=f"[오류] 크리마 후기 확인 실패: {type(error).__name__}",
            url=review_url,
            key="",
            post_id="",
            board_no="crema",
            post_no=0,
            date_text="",
            sort_value=0,
        )
    ]


def fetch_crema_reviews(review_url: str, limit: int = 10) -> List[BoardPost]:
    if not review_url:
        return []

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            page = browser.new_page(
                viewport={"width": 1440, "height": 2200},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="ko-KR",
            )

            page.goto(review_url, wait_until="networkidle", timeout=90000)

            page.wait_for_timeout(8000)

            for y in [500, 1000, 1600, 2200, 3000, 4000, 5200, 6500, 8000]:
                page.evaluate("(y) => window.scrollTo(0, y)", y)
                page.wait_for_timeout(1500)

            body_text = page.locator("body").inner_text(timeout=30000)

            print(
                "CREMA_BODY_TEXT_SAMPLE",
                body_text[:1000].replace("\n", " / ")
            )

            reviews = page.evaluate(
                """
                (limit) => {
                  function clean(t) {
                    return (t || '').replace(/\\s+/g, ' ').trim();
                  }

                  const rows = Array.from(
                    document.querySelectorAll('div, li, article, section')
                  );

                  const out = [];
                  const seen = new Set();

                  for (const row of rows) {

                    const txt = clean(row.innerText);

                    if (!txt) continue;

                    const hasReviewWord = txt.includes('리뷰');
                    const hasReport = txt.includes('신고 및 차단');
                    const hasStar =
                      txt.includes('★★★★★') ||
                      txt.includes('★★★★') ||
                      txt.includes('별점');

                    const hasOption =
                      txt.includes('상품 옵션');

                    if (!(hasReviewWord || hasReport || hasStar || hasOption))
                      continue;

                    if (txt.length < 15 || txt.length > 800)
                      continue;

                    let product = '';
                    let author = '';
                    let message = '';

                    const lines = txt
                      .split('\\n')
                      .map(v => clean(v))
                      .filter(Boolean);

                    for (const line of lines) {
                      if (!product && line.includes('리뷰')) {
                        product = line
                          .replace(/리뷰\\s*\\d+.*/, '')
                          .trim();
                      }
                    }

                    for (const line of lines) {
                      if (
                        !author &&
                        /^[가-힣A-Za-z0-9*]{2,12}$/.test(line) &&
                        !line.includes('리뷰')
                      ) {
                        author = line;
                      }
                    }

                    const ignore = [
                      'NEW',
                      '신고 및 차단',
                      '댓글',
                      '리뷰 더보기',
                    ];

                    const candidates = lines.filter(line =>
                      line.length >= 8 &&
                      !ignore.some(x => line.includes(x)) &&
                      !line.includes('상품 옵션') &&
                      !line.includes('평소사이즈') &&
                      !line.includes('몸무게') &&
                      !line.includes('키 ')
                    );

                    message =
                      candidates[candidates.length - 1] || '';

                    const uniq =
                      clean(product + '|' + author + '|' + message);

                    if (!message) continue;
                    if (seen.has(uniq)) continue;

                    seen.add(uniq);

                    out.push({
                      product,
                      author,
                      rating: txt.includes('★★★★★')
                        ? '★★★★★'
                        : '',
                      message,
                      url: location.href
                    });

                    if (out.length >= limit)
                      break;
                  }

                  return out;
                }
                """,
                limit,
            )

            print("CREMA_RAW_COUNT", len(reviews or []))

            browser.close()

        posts: List[BoardPost] = []

        for idx, r in enumerate(reviews or []):

            product = _norm_text(str(r.get("product", "")))
            author = _norm_text(str(r.get("author", "")))
            rating = _norm_text(str(r.get("rating", "")))
            message = _norm_text(str(r.get("message", "")))

            if not message:
                continue

            key = _make_key(product, author, message)

            posts.append(
                BoardPost(
                    board_name="크리마후기",
                    title=_safe_title(product, message),
                    url=review_url,
                    key=key,
                    post_id=key[:10],
                    board_no="crema",
                    post_no=0,
                    date_text=rating,
                    sort_value=9_000_000 - idx,
                )
            )

        print("CREMA_FETCHED", len(posts))

        return posts

    except Exception as e:
        print(f"CREMA_ERROR_TYPE {type(e).__name__}")
        print(f"CREMA_ERROR_MESSAGE {str(e)[:1000]}")
        return _error_post(review_url, e)
```
