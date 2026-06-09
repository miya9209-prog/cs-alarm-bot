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
    """Fetch visible CREMA reviews from the rendered review page.

    CREMA renders reviews with JavaScript, so this function uses Playwright's
    headless Chromium instead of a plain requests HTML fetch.
    """
    if not review_url:
        return []

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1280, "height": 1600},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
                ),
                locale="ko-KR",
            )
            page.goto(review_url, wait_until="domcontentloaded", timeout=60000)
            # CREMA renders after JS and often after the review area is reached.
            # Scroll several times so the widget/list is actually mounted.
            page.wait_for_timeout(3000)
            for y in [800, 1600, 2400, 3200, 4200, 5200]:
                page.evaluate("(y) => window.scrollTo(0, y)", y)
                page.wait_for_timeout(1200)
                if page.locator(".AppReviewInfoSectionListV3__message").count() > 0:
                    break
            page.wait_for_selector(".AppReviewInfoSectionListV3__message", timeout=45000)

            reviews = page.evaluate(
                """
                (limit) => {
                  function text(el) {
                    return (el && el.innerText ? el.innerText : '').replace(/\s+/g, ' ').trim();
                  }
                  function closestReview(el) {
                    let cur = el;
                    for (let i = 0; i < 12 && cur; i++, cur = cur.parentElement) {
                      const hasProduct = cur.querySelector('[class*="AppProductInfoSection"]');
                      const hasUser = cur.querySelector('[class*="AppReviewUserInfoSection"]');
                      const hasMessage = cur.querySelector('.AppReviewInfoSectionListV3__message');
                      if (hasMessage && (hasProduct || hasUser)) return cur;
                    }
                    return el.closest('[class*="Body__review"], [class*="Review"], li, article, section, div');
                  }
                  function productText(card) {
                    const selectors = [
                      '[class*="AppProductInfoSectionV2__name"]',
                      '[class*="AppProductInfoSection__name"]',
                      '[class*="ProductInfoSection"]'
                    ];
                    for (const s of selectors) {
                      const el = card && card.querySelector(s);
                      const t = text(el);
                      if (t) return t.replace(/리뷰\s*\d+.*$/, '').replace(/NEW$/, '').trim();
                    }
                    return '';
                  }
                  function authorText(card) {
                    const selectors = [
                      '[class*="AppReviewUserInfoSectionListV3"]',
                      '[class*="AppReviewUserInfoSection"]',
                      '[class*="UserInfoSection"]'
                    ];
                    for (const s of selectors) {
                      const el = card && card.querySelector(s);
                      const t = text(el);
                      if (t) return t;
                    }
                    return '';
                  }
                  function ratingText(card) {
                    if (!card) return '';
                    const rate = card.querySelector('[class*="AppRate"], [class*="Rate"], [aria-label*="점"], [title*="점"]');
                    if (!rate) return '';
                    return rate.getAttribute('aria-label') || rate.getAttribute('title') || text(rate) || '';
                  }
                  const out = [];
                  const seen = new Set();
                  const messages = Array.from(document.querySelectorAll('.AppReviewInfoSectionListV3__message'));
                  for (const msg of messages) {
                    const message = text(msg);
                    if (!message || seen.has(message)) continue;
                    seen.add(message);
                    const card = closestReview(msg);
                    out.push({
                      product: productText(card),
                      author: authorText(card),
                      rating: ratingText(card),
                      message: message,
                      url: location.href
                    });
                    if (out.length >= limit) break;
                  }
                  return out;
                }
                """,
                limit,
            )
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
                    # Put CREMA reviews above old numeric Cafe24 board posts in debug logs.
                    sort_value=9_000_000 - idx,
                )
            )
        return posts
    except Exception as e:
        print(f"CREMA_ERROR_TYPE {type(e).__name__}")
        print(f"CREMA_ERROR_MESSAGE {str(e)[:500]}")
        return _error_post(review_url, e)
