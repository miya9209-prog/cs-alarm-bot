import hashlib
import re
from typing import List

from src.cafe24_board import BoardPost


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _short_text(text: str, max_len: int = 90) -> str:
    text = _norm_text(text)
    return text if len(text) <= max_len else text[:max_len] + "..."


def _make_key(product: str, author: str, message: str) -> str:
    # 상품명/작성자 파싱이 조금 달라져도 같은 후기는 같은 키가 되도록
    # 후기 본문 중심으로 고유키를 만듭니다.
    raw = f"crema|{_norm_text(message)[:120]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _safe_title(product: str, message: str) -> str:
    product = _norm_text(product) or "상품명 확인불가"
    return f"{product} / {_short_text(message, 45) or '후기내용 확인불가'}"


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

            for y in [600, 1200, 2000, 3000, 4200, 5600, 7200, 9000]:
                page.evaluate("(y) => window.scrollTo(0, y)", y)
                page.wait_for_timeout(1200)

            body_text = page.locator("body").inner_text(timeout=30000)
            print("CREMA_BODY_TEXT_SAMPLE", body_text[:700].replace("\n", " / "))

            reviews = page.evaluate(
                """
                (limit) => {
                  function clean(t) {
                    return (t || '').replace(/\\s+/g, ' ').trim();
                  }

                  function isBadMessage(t) {
                    if (!t) return true;
                    if (t.length < 5) return true;
                    if (t.length > 350) return true;

                    const badWords = [
                      'LOGIN',
                      'JOIN',
                      'MYPAGE',
                      'CART',
                      'COMMUNITY',
                      'NOTICE',
                      'REVIEW',
                      'Q & A',
                      'FAQ',
                      'EVENT',
                      'BANK INFO',
                      'COMPANY',
                      'AGREEMENT',
                      'PRIVACY',
                      '신고 및 차단',
                      '리뷰 더보기',
                      '댓글',
                      '상품 옵션',
                      '평소사이즈',
                      '몸무게',
                      '전체상품목록',
                      '바로가기',
                      '이용약관',
                      '개인정보',
                      '고객센터',
                      '택배 배송',
                      '반품 주소'
                    ];

                    return badWords.some(w => t.includes(w));
                  }

                  function text(el) {
                    return clean(el && el.innerText ? el.innerText : '');
                  }

                  function closestCard(el) {
                    let cur = el;
                    for (let i = 0; i < 12 && cur; i++, cur = cur.parentElement) {
                      const t = text(cur);
                      if (
                        t.includes('신고 및 차단') ||
                        t.includes('상품 옵션') ||
                        t.includes('평소사이즈') ||
                        t.includes('리뷰 더보기')
                      ) {
                        return cur;
                      }
                    }
                    return el.parentElement || el;
                  }

                  function findProduct(card) {
                    if (!card) return '';

                    const selectors = [
                      '[class*="ProductInfoSection"]',
                      '[class*="product"]',
                      '[class*="Product"]'
                    ];

                    for (const s of selectors) {
                      const nodes = Array.from(card.querySelectorAll(s));
                      for (const n of nodes) {
                        const lines = (n.innerText || '')
                          .split('\\n')
                          .map(clean)
                          .filter(Boolean);

                        for (const line of lines) {
                          if (
                            line.includes('color') ||
                            line.includes('슬랙스') ||
                            line.includes('블라우스') ||
                            line.includes('데님') ||
                            line.includes('팬츠') ||
                            line.includes('가디건') ||
                            line.includes('티셔츠') ||
                            line.includes('원피스') ||
                            line.includes('셔츠') ||
                            line.includes('니트') ||
                            line.includes('자켓')
                          ) {
                            return line.replace(/리뷰\\s*\\d+.*/, '').trim();
                          }
                        }
                      }
                    }

                    const lines = (card.innerText || '')
                      .split('\\n')
                      .map(clean)
                      .filter(Boolean);

                    for (const line of lines) {
                      if (line.includes('리뷰')) {
                        return line.replace(/리뷰\\s*\\d+.*/, '').trim();
                      }
                    }

                    return '';
                  }

                  function findAuthor(card) {
                    if (!card) return '';

                    const lines = (card.innerText || '')
                      .split('\\n')
                      .map(clean)
                      .filter(Boolean);

                    for (const line of lines) {
                      if (/^[가-힣]{2,4}\\*+$/.test(line)) {
                        return line;
                      }
                    }

                    return '';
                  }

                  const messageSelectors = [
                    '.AppReviewInfoSectionListV3__message',
                    '[class*="ReviewInfoSection"][class*="message"]',
                    '[class*="message"][class*="collapsible"]',
                    '[class*="review"][class*="message"]'
                  ];

                  let messageNodes = [];

                  for (const s of messageSelectors) {
                    messageNodes = Array.from(document.querySelectorAll(s))
                      .filter(el => !isBadMessage(text(el)));

                    if (messageNodes.length > 0) break;
                  }

                  if (messageNodes.length === 0) {
                    messageNodes = Array.from(document.querySelectorAll('div'))
                      .filter(el => {
                        const t = text(el);
                        if (isBadMessage(t)) return false;
                        if (el.children.length > 1) return false;
                        return /[가-힣]/.test(t);
                      });
                  }

                  const out = [];
                  const seenMessage = new Set();

                  for (const msg of messageNodes) {
                    const message = text(msg);

                    if (isBadMessage(message)) continue;

                    const msgKey = message.slice(0, 120);
                    if (seenMessage.has(msgKey)) continue;
                    seenMessage.add(msgKey);

                    const card = closestCard(msg);
                    const product = findProduct(card);
                    const author = findAuthor(card);
                    const cardText = text(card);
                    const rating =
                      cardText.includes('★★★★★') ? '★★★★★' :
                      cardText.includes('★★★★') ? '★★★★' :
                      '';

                    out.push({
                      product,
                      author,
                      rating,
                      message,
                      url: location.href
                    });

                    if (out.length >= limit) break;
                  }

                  return out;
                }
                """,
                limit,
            )

            print("CREMA_RAW_COUNT", len(reviews or []))
            browser.close()

        posts: List[BoardPost] = []
        seen_keys = set()

        for idx, r in enumerate(reviews or []):
            product = _norm_text(str(r.get("product", "")))
            author = _norm_text(str(r.get("author", "")))
            rating = _norm_text(str(r.get("rating", "")))
            message = _norm_text(str(r.get("message", "")))

            if not message:
                continue

            key = _make_key(product, author, message)

            if key in seen_keys:
                continue
            seen_keys.add(key)

            posts.append(
                BoardPost(
                    board_name="크리마후기",
                    title=_safe_title(product, message),
                    url=review_url,
                    key=key,
                    post_id=key[:10],
                    board_no="crema",
                    post_no=0,
                    date_text=rating or "별점 확인불가",
                    sort_value=9_000_000 - idx,
                )
            )

        print("CREMA_FETCHED", len(posts))
        return posts

    except Exception as e:
        print(f"CREMA_ERROR_TYPE {type(e).__name__}")
        print(f"CREMA_ERROR_MESSAGE {str(e)[:1000]}")
        return _error_post(review_url, e)
