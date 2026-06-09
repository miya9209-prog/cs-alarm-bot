import hashlib
import re
from typing import List

from src.cafe24_board import BoardPost


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _make_key(product: str, author: str, message: str) -> str:
    # 크리마는 후기 ID가 DOM에 안정적으로 노출되지 않아 본문 중심으로 키를 만듭니다.
    raw = f"crema|{_norm_text(message)[:160]}"
    return "crema:" + hashlib.md5(raw.encode("utf-8")).hexdigest()


def _clean_product(product: str) -> str:
    product = _norm_text(product)
    bad_words = [
        "LOGIN", "JOIN", "MYPAGE", "CART", "COMMUNITY", "NOTICE", "REVIEW", "Q & A", "FAQ", "EVENT",
        "장바구니", "회원가입", "로그인", "아이디", "비밀번호", "최근 본 상품", "바로 구매", "바로가기",
        "고객센터", "BANK INFO", "COMPANY", "AGREEMENT", "PRIVACY", "전체상품목록", "카톡 플러스친구",
    ]
    if not product or any(w in product for w in bad_words):
        return "상품명 확인불가"
    return product[:70] + "..." if len(product) > 70 else product


def _clean_author(author: str) -> str:
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
    """Fetch CREMA reviews rendered on the public review page.

    GitHub Actions 환경에서는 데스크톱 뷰에서 크리마 후기 영역이 늦게 붙거나
    아예 안 붙는 경우가 있어 모바일 뷰포트로 충분히 기다리며 스크롤합니다.
    """
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
                    "--disable-gpu",
                ],
            )

            context = browser.new_context(
                viewport={"width": 430, "height": 1400},
                is_mobile=True,
                has_touch=True,
                device_scale_factor=2,
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/17.0 Mobile/15E148 Safari/604.1"
                ),
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page.goto(review_url, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(8000)

            review_selector = ".AppReviewInfoSectionListV3__message"
            found_count = 0

            # 크리마 위젯이 늦게 마운트되는 경우를 위해 최대 약 90초까지 반복합니다.
            for round_no in range(1, 10):
                # 맨 위에서 아래로 여러 번 이동해야 lazy-load가 붙는 경우가 있습니다.
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(700)
                for y in [500, 1000, 1600, 2300, 3100, 4200, 5600, 7200, 9000, 11200, 13800, 16800]:
                    page.evaluate("(y) => window.scrollTo(0, y)", y)
                    page.wait_for_timeout(700)
                    found_count = page.locator(review_selector).count()
                    if found_count > 0:
                        break
                print(f"CREMA_WAIT_ROUND {round_no} COUNT {found_count}")
                if found_count > 0:
                    break
                page.wait_for_timeout(3000)
                try:
                    page.reload(wait_until="domcontentloaded", timeout=90000)
                    page.wait_for_timeout(6000)
                except Exception:
                    pass

            body_text = page.locator("body").inner_text(timeout=30000)
            print("CREMA_BODY_TEXT_SAMPLE", body_text[:700].replace("\n", " / "))

            reviews = page.evaluate(
                r"""
                (limit) => {
                  function clean(t) {
                    return (t || '').replace(/\s+/g, ' ').trim();
                  }
                  function linesOf(el) {
                    return ((el && el.innerText) || '').split('\n').map(clean).filter(Boolean);
                  }
                  function text(el) {
                    return clean(el && el.innerText ? el.innerText : '');
                  }
                  function isBadLine(t) {
                    if (!t) return true;
                    const bad = [
                      'LOGIN','JOIN','MYPAGE','CART','COMMUNITY','NOTICE','REVIEW','Q & A','FAQ','EVENT',
                      'BANK INFO','COMPANY','AGREEMENT','PRIVACY','장바구니','회원가입','로그인','아이디 찾기',
                      '비밀번호','전체상품목록','바로가기','이용약관','개인정보','고객센터','택배 배송','반품 주소',
                      '신고 및 차단','리뷰 더보기','댓글','상품 옵션','평소사이즈','몸무게','키 ', 'NEW'
                    ];
                    return bad.some(x => t.includes(x));
                  }
                  function validMessage(t) {
                    if (!t) return false;
                    if (t.length < 4 || t.length > 260) return false;
                    if (!/[가-힣]/.test(t)) return false;
                    if (isBadLine(t)) return false;
                    return true;
                  }
                  function nearestCard(el) {
                    let cur = el;
                    for (let i = 0; i < 20 && cur; i++, cur = cur.parentElement) {
                      const t = text(cur);
                      if (
                        cur.querySelector('[class*="AppProductInfoSection"]') ||
                        cur.querySelector('[class*="AppReviewUserInfoSection"]') ||
                        t.includes('신고 및 차단') ||
                        t.includes('평소사이즈') ||
                        t.includes('상품 옵션')
                      ) return cur;
                    }
                    return el.parentElement || el;
                  }
                  function findProduct(card) {
                    if (!card) return '';
                    const blocks = Array.from(card.querySelectorAll('[class*="AppProductInfoSection"]'));
                    for (const block of blocks) {
                      const lines = linesOf(block);
                      for (const line of lines) {
                        if (isBadLine(line)) continue;
                        if (/^리뷰\s*\d+/.test(line)) continue;
                        if (
                          line.includes('color') || line.includes('슬랙스') || line.includes('블라우스') ||
                          line.includes('데님') || line.includes('팬츠') || line.includes('가디건') ||
                          line.includes('티셔츠') || line.includes('원피스') || line.includes('셔츠') ||
                          line.includes('니트') || line.includes('자켓') || line.includes('스커트') ||
                          line.includes('코트') || line.includes('점퍼') || line.includes('블라')
                        ) return line.replace(/리뷰\s*\d+.*/, '').trim();
                      }
                    }
                    return '';
                  }
                  function findAuthor(card) {
                    if (!card) return '';
                    const blocks = Array.from(card.querySelectorAll('[class*="AppReviewUserInfoSection"]'));
                    for (const block of blocks) {
                      const lines = linesOf(block);
                      for (const line of lines) {
                        if (/^[가-힣]{2,4}\*+$/.test(line)) return line;
                      }
                    }
                    const lines = linesOf(card);
                    for (const line of lines) {
                      if (/^[가-힣]{2,4}\*+$/.test(line)) return line;
                    }
                    return '';
                  }

                  let nodes = Array.from(document.querySelectorAll('.AppReviewInfoSectionListV3__message'));
                  if (nodes.length === 0) {
                    nodes = Array.from(document.querySelectorAll('[class*="AppReviewInfoSectionListV3__message"], [class*="message--collapsible"]'));
                  }
                  if (nodes.length === 0) {
                    nodes = Array.from(document.querySelectorAll('div')).filter(el => {
                      const t = text(el);
                      if (!validMessage(t)) return false;
                      if (el.children.length > 0) return false;
                      const card = nearestCard(el);
                      const ct = text(card);
                      return ct.includes('신고 및 차단') || ct.includes('평소사이즈') || ct.includes('상품 옵션');
                    });
                  }

                  const out = [];
                  const seen = new Set();
                  for (const node of nodes) {
                    const message = text(node);
                    if (!validMessage(message)) continue;
                    const key = message.slice(0, 150);
                    if (seen.has(key)) continue;
                    seen.add(key);
                    const card = nearestCard(node);
                    out.push({
                      product: findProduct(card),
                      author: findAuthor(card),
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
            print("CREMA_RAW_COUNT", len(reviews or []))
            context.close()
            browser.close()

        posts: List[BoardPost] = []
        seen_keys = set()
        for idx, r in enumerate(reviews or []):
            product = _clean_product(str(r.get("product", "")))
            author = _clean_author(str(r.get("author", "")))
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
