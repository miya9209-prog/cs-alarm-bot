import hashlib
import re
from typing import List

from src.cafe24_board import BoardPost


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _make_key(product: str, author: str, message: str) -> str:
    # v4와 동일하게 후기 본문 중심 키를 유지합니다.
    # 상품명/작성자 파싱을 고쳐도 기존 후기가 다시 알림되는 것을 줄입니다.
    raw = f"crema|{_norm_text(message)[:120]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _safe_product(product: str) -> str:
    product = _norm_text(product)
    if not product:
        return "상품명 확인불가"
    if len(product) > 60:
        product = product[:60] + "..."
    return product


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

            # 후기 영역이 lazy-load 되는 경우를 대비해 충분히 스크롤합니다.
            for y in [600, 1200, 2000, 3000, 4200, 5600, 7200, 9000, 11000]:
                page.evaluate("(y) => window.scrollTo(0, y)", y)
                page.wait_for_timeout(1000)

            body_text = page.locator("body").inner_text(timeout=30000)
            print("CREMA_BODY_TEXT_SAMPLE", body_text[:500].replace("\n", " / "))

            reviews = page.evaluate(
                """
                (limit) => {
                  function clean(t) {
                    return (t || '').replace(/\s+/g, ' ').trim();
                  }

                  function text(el) {
                    return clean(el && el.innerText ? el.innerText : '');
                  }

                  function badMessage(t) {
                    if (!t) return true;
                    if (t.length < 4) return true;
                    if (t.length > 220) return true;
                    const bad = [
                      'LOGIN', 'JOIN', 'MYPAGE', 'CART', 'COMMUNITY',
                      'NOTICE', 'REVIEW', 'Q & A', 'FAQ', 'EVENT',
                      '상품 옵션', '평소사이즈', '몸무게', '신고 및 차단',
                      '리뷰 더보기', '댓글', '전체상품목록', '바로가기',
                      '회원가입', '아이디 찾기', '비밀번호 찾기', '고객센터',
                      '택배', '반품', '교환', '이용약관', '개인정보'
                    ];
                    return bad.some(x => t.includes(x));
                  }

                  function closestCard(el) {
                    let cur = el;
                    for (let i = 0; i < 18 && cur; i++, cur = cur.parentElement) {
                      const hasMsg = cur.querySelector('.AppReviewInfoSectionListV3__message, [class*="message"][class*="collapsible"]');
                      const hasProduct = cur.querySelector('[class*="AppProductInfoSection"]');
                      const hasUser = cur.querySelector('[class*="AppReviewUserInfoSection"]');
                      const t = text(cur);
                      if (hasMsg && hasProduct && hasUser) return cur;
                      if (hasMsg && (t.includes('신고 및 차단') || t.includes('평소사이즈'))) return cur;
                    }
                    return el.parentElement || el;
                  }

                  function productFrom(card) {
                    if (!card) return '';
                    const blocks = Array.from(card.querySelectorAll('[class*="AppProductInfoSection"]'));
                    for (const b of blocks) {
                      const lines = (b.innerText || '').split('\n').map(clean).filter(Boolean);
                      for (const line of lines) {
                        if (line === 'NEW') continue;
                        if (/^리뷰\s*\d+/.test(line)) continue;
                        if (line.includes('상품 옵션')) continue;
                        if (line.includes('color') || line.includes('슬랙스') || line.includes('블라우스') || line.includes('데님') || line.includes('팬츠') || line.includes('가디건') || line.includes('티셔츠') || line.includes('원피스') || line.includes('셔츠') || line.includes('니트') || line.includes('자켓')) {
                          return line.replace(/리뷰\s*\d+.*/, '').trim();
                        }
                      }
                    }
                    return '';
                  }

                  function authorFrom(card) {
                    if (!card) return '';
                    const blocks = Array.from(card.querySelectorAll('[class*="AppReviewUserInfoSection"]'));
                    for (const b of blocks) {
                      const lines = (b.innerText || '').split('\n').map(clean).filter(Boolean);
                      for (const line of lines) {
                        if (/^[가-힣]{2,4}\*+$/.test(line)) return line;
                      }
                    }
                    return '';
                  }

                  const selectors = [
                    '.AppReviewInfoSectionListV3__message',
                    '[class*="AppReviewInfoSectionListV3__message"]',
                    '[class*="message"][class*="collapsible"]'
                  ];

                  let nodes = [];
                  for (const s of selectors) {
                    nodes = Array.from(document.querySelectorAll(s)).filter(el => !badMessage(text(el)));
                    if (nodes.length > 0) break;
                  }

                  const out = [];
                  const seen = new Set();

                  for (const node of nodes) {
                    const message = text(node);
                    if (badMessage(message)) continue;
                    const messageKey = message.slice(0, 120);
                    if (seen.has(messageKey)) continue;
                    seen.add(messageKey);

                    const card = closestCard(node);
                    const product = productFrom(card);
                    const author = authorFrom(card);

                    out.push({
                      product,
                      author,
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
            product = _safe_product(str(r.get("product", "")))
            author = _norm_text(str(r.get("author", ""))) or "작성자 확인불가"
            message = _norm_text(str(r.get("message", "")))

            if not message:
                continue

            key = _make_key(product, author, message)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # title에는 상품명만, date_text에는 작성자만 넣습니다.
            # 텔레그램 알림은 monitor.py에서 2줄로 단순 출력합니다.
            posts.append(
                BoardPost(
                    board_name="크리마후기",
                    title=product,
                    url=review_url,
                    key=key,
                    post_id=key[:10],
                    board_no="crema",
                    post_no=0,
                    date_text=author,
                    sort_value=9_000_000 - idx,
                )
            )

        print("CREMA_FETCHED", len(posts))
        return posts

    except Exception as e:
        print(f"CREMA_ERROR_TYPE {type(e).__name__}")
        print(f"CREMA_ERROR_MESSAGE {str(e)[:1000]}")
        return _error_post(review_url, e)
