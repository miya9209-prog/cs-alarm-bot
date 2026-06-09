# 미샵 CS 알림봇

미샵 Cafe24 상품문의 게시판과 네이버 스마트스토어 공개 Q&A 페이지를 확인해 새 문의가 생기면 텔레그램으로 알림을 보내는 봇입니다.

## 현재 포함 기능

- Cafe24 상품문의 게시판 새글 알림
- 네이버 스마트스토어 공개 Q&A 새 문의 알림
- `state.json` 기반 중복 알림 방지
- GitHub Actions 실행 지원

## GitHub Secrets

필수:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
BOARD_URLS
```

선택:

```text
SMARTSTORE_QNA_URL
```

`SMARTSTORE_QNA_URL`을 만들지 않으면 기본값으로 아래 주소를 사용합니다.

```text
https://smartstore.naver.com/misharp2006/qna
```

## BOARD_URLS 값

상품문의 게시판만 넣는 것을 권장합니다.

```text
https://www.misharp.co.kr/board/product/list.html?board_no=6
```

## 스마트스토어 알림 형식

```text
🔔 스마트스토어 새 문의

문의일: 2026-06-10
작성자: banj*****
링크: https://smartstore.naver.com/misharp2006/qna
```

## 첫 실행 주의

`state.json`이 없으면 현재 보이는 글을 기준값으로 저장하고 알림을 보내지 않습니다.

스마트스토어 기능을 처음 추가한 실행에서도 현재 보이는 스마트스토어 문의는 기준값으로만 저장합니다. 이후 새 문의부터 알림이 발송됩니다.

## 크리마 후기

크리마 후기 알림은 GitHub Actions 환경에서 안정적으로 렌더링되지 않아 제거했습니다.
