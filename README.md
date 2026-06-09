# 미샵 CS 게시판 새글 알림봇 v12 - 크리마 후기 알림 추가

## 이번 버전에서 추가된 기능
- 기존 상품문의 게시판 알림은 그대로 유지합니다.
- 크리마 후기 페이지는 JavaScript 위젯으로 렌더링되므로 Playwright headless Chromium으로 화면 렌더링 후 후기 내용을 감지합니다.
- 신규 후기 감지 시 텔레그램으로 `미샵 새 후기 알림`을 발송합니다.
- 첫 실행 또는 state.json 초기화 후에는 현재 보이는 글/후기를 기준값으로 저장하고 알림을 보내지 않습니다.

## GitHub Secrets
기존 Secret은 그대로 유지합니다.

필수:
```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
BOARD_URLS
```

크리마 후기용 추가 Secret:
```text
CREMA_REVIEW_URL
```

값:
```text
https://misharp.co.kr/board/review/photo.html?board_no=4
```

`CREMA_REVIEW_URL`을 만들지 않아도 위 URL을 기본값으로 사용하지만, GitHub Secrets에 넣어두는 것을 권장합니다.

## BOARD_URLS 예시
상품문의는 기존처럼 유지하세요. 크리마 후기는 `CREMA_REVIEW_URL`에서 별도 감지하므로 `BOARD_URLS`에는 상품문의만 두는 것을 권장합니다.

```text
https://misharp.co.kr/board/product/list.html?board_no=6
```

기존처럼 여러 줄 입력도 가능합니다.

```text
https://misharp.co.kr/board/product/list.html?board_no=6
https://misharp.co.kr/board/gallery/list.html?board_no=39&category_no=1
```

## GitHub Actions 변경사항
워크플로우에서 아래 명령이 추가되었습니다.

```bash
python -m playwright install --with-deps chromium
```

크리마 후기는 브라우저에서 렌더링된 HTML을 읽어야 하므로 필요합니다.

## 테스트 순서
1. 수정된 ZIP을 GitHub 레포에 업로드/커밋합니다.
2. GitHub > Settings > Secrets and variables > Actions에서 `CREMA_REVIEW_URL`을 추가합니다.
3. Actions > Board Monitor > Run workflow를 1회 실행합니다.
4. 첫 실행은 기준값 저장용입니다. 기존 후기는 알림이 가지 않는 것이 정상입니다.
5. 이후 새 후기가 올라오면 다음 실행부터 텔레그램 알림이 발송됩니다.

## 알림 예시
```text
🔔 미샵 새 후기 알림

상품명: 여름 동행 블라우스 (2 color)
별점: ★★★★★
후기: 택배 오자마자 입어봤어요...

링크: https://misharp.co.kr/board/review/photo.html?board_no=4
```

## 주의
- 크리마 화면 구조가 바뀌면 CSS 선택자를 조정해야 할 수 있습니다.
- 스마트스토어 문의 알림은 이번 ZIP에 포함하지 않았습니다. 이번 버전은 크리마 후기 알림만 추가한 안정화 버전입니다.
