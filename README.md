# 미샵 CS 게시판 새글 알림봇 v9

미샵 카페24 게시판 새글을 감지해 텔레그램으로 알림을 보내는 Streamlit + GitHub Actions 프로그램입니다.

## 이번 버전에서 잡은 문제

- 포토후기 실제 링크: `/board/review/read_photo.html?board_no=4&no=...`
- 상품문의 실제 링크: `/article/상품문의/6/.../`
- 이벤트 실제 링크: `/article/이벤트/39/.../categoryno/1/`
- 상품 카테고리/상품목록 링크 제외
- 공지글/답변글 제외
- GitHub Actions 실행 후 `state.json` 자동 커밋

## Secrets

Streamlit Cloud Secrets와 GitHub Repository Secrets에 동일하게 입력하세요.

```toml
TELEGRAM_BOT_TOKEN = "봇토큰"
TELEGRAM_CHAT_ID = "-5152305178"
BOARD_URLS = """
https://misharp.co.kr/board/review/photo.html?board_no=4
https://misharp.co.kr/board/product/list.html?board_no=6
https://misharp.co.kr/board/gallery/list.html?board_no=39&category_no=1
"""
```

## 사용 순서

1. Streamlit에서 `현재 게시판 글 확인`을 눌러 실제 게시글이 보이는지 확인합니다.
2. `기준값 저장`을 누릅니다. 이 버튼은 현재 글 30개를 “이미 확인한 글”로 등록합니다.
3. 기준값 저장 직후 `새글 확인 후 알림 발송`을 누르면 새글 0개가 정상입니다.
4. 그 이후 공개 게시판에 새글이 올라오면 `새글 확인 후 알림 발송` 또는 GitHub Actions 자동 실행 때 알림이 갑니다.

## GitHub Actions

`.github/workflows/board_monitor.yml`이 10분마다 실행됩니다. 첫 실행 때 `state.json`이 없으면 과거 글을 알림 보내지 않고 기준값만 생성합니다.
