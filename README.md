# 미샵 CS 게시판 새글 알림봇

카페24 게시판 새글을 확인해서 텔레그램 단체방으로 알려주는 프로그램입니다.

## 이번 버전 핵심 수정

- 미샵 포토후기 게시판의 실제 링크 형식인 `/board/review/read_photo.html?board_no=4&no=...`를 감지합니다.
- 상품문의 게시판의 실제 링크 형식인 `/article/상품문의/6/글번호/`를 감지합니다.
- 이벤트/갤러리 게시판의 실제 링크 형식인 `/article/이벤트/39/글번호/categoryno/1/`를 감지합니다.
- 카테고리 링크, 상품목록 링크, 메뉴 링크는 제외합니다.
- GitHub Actions가 `state.json` 기준값 파일을 자동 커밋합니다.

## Secrets 설정

Streamlit Cloud Secrets와 GitHub Repository Secrets에 동일하게 입력하세요.

```toml
TELEGRAM_BOT_TOKEN = "BotFather가 준 봇 토큰"
TELEGRAM_CHAT_ID = "-5152305178"

BOARD_URLS = """
https://misharp.co.kr/board/review/photo.html?board_no=4
https://misharp.co.kr/board/product/list.html?board_no=6
https://misharp.co.kr/board/gallery/list.html?board_no=39&category_no=1
"""
```

## 최초 사용 순서

1. Streamlit Cloud에서 앱을 재부팅합니다.
2. `현재 게시판 글 확인`을 누릅니다.
3. 실제 후기/상품문의/이벤트 글이 보이면 정상입니다.
4. `기준값 저장`을 한 번 누릅니다.
5. 이후 새글부터 `새글 확인 후 알림 발송` 또는 GitHub Actions 자동 실행으로 텔레그램 알림이 갑니다.

## GitHub Actions

- 10분마다 자동 실행됩니다.
- 첫 실행 때 `state.json`이 없으면 기존 글은 알림하지 않고 기준값만 저장합니다.
- 이후 새글만 텔레그램으로 보냅니다.
