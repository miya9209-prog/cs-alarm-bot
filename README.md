# 미샵 CS 게시판 새글 알림봇

Streamlit + GitHub Actions + Telegram 알림봇입니다.

## 필수 Secrets

Streamlit Cloud Secrets와 GitHub Repository Secrets에 동일하게 입력하세요.

```toml
TELEGRAM_BOT_TOKEN = "봇토큰"
TELEGRAM_CHAT_ID = "채팅방ID"
BOARD_URLS = """
https://misharp.co.kr/board/review/list.html?board_no=4
https://misharp.co.kr/board/product/list.html?board_no=6
https://misharp.co.kr/board/gallery/list.html?board_no=39&category_no=1
"""
```

## 최초 사용 순서

1. Streamlit 접속
2. 현재 게시판 글 확인
3. 정상 게시글이 나오면 기준값 저장
4. 이후 새글 확인 후 알림 발송 또는 GitHub Actions 자동 실행
