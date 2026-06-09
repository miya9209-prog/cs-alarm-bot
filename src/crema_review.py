import hashlib
import re
from typing import List

from src.cafe24_board import BoardPost


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _make_key(message: str) -> str:
    # 후기 본문 중심 키. 상품명/작성자 파싱이 달라져도 중복 알림이 줄어듭니다.
    raw = f"crema|{_norm_text(message)[:140]}"
    return "crema:" + hashlib.md5(raw.encode("utf-8")).hexdigest()


def _safe_product(product: str) -> str:
    product = _norm_text(product)
    bad_words = [
        "LOGIN", "JOIN", "MYPAGE", "CART", "COMMUNITY", "NOTICE", "REVIEW",
        "Q & A", "FAQ", "EVENT", "장바구니", "회원가입", "로그인", "아이디 찾기",
        "비밀번호", "최근 본 상품", "바로 구매", "바로가기", "고객센터",
    ]
    if not product or any(w in product for w in bad_words):
        return "상품명 확인불가"
    return product[:60] + "..." if len(product) > 60 else product


def _safe_author(author: str) -> str:
    author = _norm_text(author)
    if not author:
        return "작성자 확인불가"
    return author[:20]


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
                viewport={"width": 1440, "height": 2400},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="ko-KR",
            )

            page.goto(review_url, wait_until="networkidle", timeout=90000)
            page.wait_for_timeout(8000)

            # 크리마 리뷰는 스크롤 후 늦게 붙는 경우가 있어 여러 번 내려봅니다.
            for y in [700, 1400, 2300, 3400, 4800, 6400, 8200, 10400, 12800]:
                page.evaluate("(y) => window.scrollTo(0, y)", y)
                page.wait_for_timeout(1200)

            body_text = page.locator("body").inner_text(timeout=30000)
            print("CREMA_BODY_TEXT_SAMPLE", body_text[:500].replace("\n", " / "))

            # 주의: raw string으로 유지해야 JS 내부 \n, \s가 깨지지 않습니다.
            reviews = page.evaluate(
                r"""
                (limit) => {
                  function clean(t) {
                    return (t || '').replace(/\s+/g, ' ').trim();
                  }

                  function text(el) {
                    return clean(el && el.innerText ? el.innerText : '');
                  }

                  function splitLines(t) {
                    return (t || '').split('\n').map(clean).filter(Boolean);
                  }

                  function badLine(t) {
                    if (!t) return true;
                    const bad = [
                      'LOGIN', 'JOIN', 'MYPAGE', 'CART', 'COMMUNITY', 'NOTICE', 'REVIEW',
                      'Q & A', 'FAQ', 'EVENT', 'BANK INFO', 'COMPANY', 'AGREEMENT', 'PRIVACY',
                      '상품 옵션', '평소사이즈', '몸무게', '신고 및 차단', '리뷰 더보기', '댓글',
                      '전체상품목록', '바로가기', '회원가입', '아이디 찾기', '비밀번호 찾기',
                      '고객센터', '택배', '반품', '교환', '이용약관', '개인정보', '장바구니',
                      '최근 본 상품', '바로 구매'
                    ];
                    return bad.some(x => t.includes(x));
                  }

                  function looksLikeReviewMessage(t) {
                    if (!t) return false;
                    if (t.length < 5 || t.length > 180) return false;
                    if (badLine(t)) return false;
                    if (!/[가-힣]/.test(t)) return false;
                    return true;
                  }

                  function closestReviewCard(el) {
                    let cur = el;
                    for (let i = 0; i < 16 && cur; i++, cur = cur.parentElement) {
                      const t = text(cur);
                      const hasReviewSignal =
                        t.includes('신고 및 차단') ||
                        t.includes('평소사이즈') ||
                        t.includes('상품 옵션') ||
                        cur.querySelector('[class*="AppProductInfoSection"]') ||
                        cur.querySelector('[class*="AppReviewUserInfoSection"]');
                      if (hasReviewSignal) return cur;
                    }
                    return el.parentElement || el;
                  }

                  function productFrom(card) {
                    if (!card) return '';
                    const productBlocks = Array.from(card.querySelectorAll('[class*="AppProductInfoSection"]'));
                    for (const block of productBlocks) {
                      const lines = splitLines(block.innerText);
                      for (const line of lines) {
                        if (badLine(line)) continue;
                        if (/^리뷰\s*\d+/.test(line)) continue;
                        if (
                          line.includes('color') || line.includes('슬랙스') || line.includes('블라우스') ||
                          line.includes('데님') || line.includes('팬츠') || line.includes('가디건') ||
                          line.includes('티셔츠') || line.includes('원피스') || line.includes('셔츠') ||
                          line.includes('니트') || line.includes('자켓') || line.includes('스커트') ||
                          line.includes('코트') || line.includes('점퍼')
                        ) {
                          return line.replace(/리뷰\s*\d+.*/, '').trim();
                        }
                      }
                    }
                    return '';
                  }

                  function authorFrom(card) {
                    if (!card) return '';
                    const userBlocks = Array.from(card.querySelectorAll('[class*="AppReviewUserInfoSection"]'));
                    for (const block of userBlocks) {
                      const lines = splitLines(block.innerText);
                      for (const line of lines) {
                        if (/^[가-힣]{2,4}\*$/.test(line) || /^[가-힣]{2,4}\*+$/.test(line)) return line;
                      }
                    }
                    return '';
                  }

                  const selectors = [
                    '.AppReviewInfoSectionListV3__message',
                    '[class*="AppReviewInfoSectionListV3__message"]',
                    '[class*="message"][class*="collapsible"]'
                  ];

                  let messageNodes = [];
                  for (const s of selectors) {
                    messageNodes = Array.from(document.querySelectorAll(s))
                      .filter(el => looksLikeReviewMessage(text(el)));
                    if (messageNodes.length > 0) break;
                  }

                  // 클래스명이 안 잡힐 때만 보조 수단 사용.
                  // 단, 리뷰 카드 신호가 있는 영역 안의 짧은 leaf div만 후보로 둡니다.
                  if (messageNodes.length === 0) {
                    messageNodes = Array.from(document.querySelectorAll('div'))
                      .filter(el => {
                        const t = text(el);
                        if (!looksLikeReviewMessage(t)) return false;
                        if (el.children.length > 0) return false;
                        const card = closestReviewCard(el);
                        const cardText = text(card);
                        return cardText.includes('신고 및 차단') || cardText.includes('평소사이즈') || cardText.includes('상품 옵션');
                      });
                  }

                  const out = [];
                  const seen = new Set();

                  for (const node of messageNodes) {
                    const message = text(node);
                    if (!looksLikeReviewMessage(message)) continue;
                    const msgKey = message.slice(0, 120);
                    if (seen.has(msgKey)) continue;
                    seen.add(msgKey);

                    const card = closestReviewCard(node);
                    out.push({
                      product: productFrom(card),
                      author: authorFrom(card),
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
            author = _safe_author(str(r.get("author", "")))
            message = _norm_text(str(r.get("message", "")))

            if not message:
                continue

            key = _make_key(message)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            posts.append(
                BoardPost(
                    board_name="크리마후기",
                    title=product,
                    url=review_url,
                    key=key,
                    post_id=key.replace("crema:", "")[:10],
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
