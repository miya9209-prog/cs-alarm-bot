# 미샵 CS 게시판 새글 알림봇 v5

## 핵심 사용법

1. Streamlit에서 `현재 게시판 글 확인`을 눌러 글이 읽히는지 확인합니다.
2. 처음 세팅 후에는 `기준값 저장`을 한 번 누릅니다.
   - 이때 현재 보이는 글들은 “이미 본 글”로 저장됩니다.
3. 그 이후 새글이 작성되면 `새글 확인 후 알림 발송` 또는 GitHub Actions 자동 실행 시 텔레그램 알림이 갑니다.
4. 테스트 중 꼬이면 `기준값 초기화`를 누른 뒤 다시 테스트할 수 있습니다.

## GitHub Actions 필수 파일

저장소 첫 화면에 아래 구조가 있어야 합니다.

```text
.github/workflows/board_monitor.yml
src
app.py
requirements.txt
runtime.txt
README.md
```

## GitHub Secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `BOARD_URLS`

## Streamlit Secrets

```toml
TELEGRAM_BOT_TOKEN = "BotFather가 준 봇토큰"
TELEGRAM_CHAT_ID = "-5152305178"
BOARD_URLS = """
https://misharp.co.kr/board/review/photo.html?board_no=4
https://misharp.co.kr/board/product/list.html?board_no=6
https://misharp.co.kr/board/gallery/list.html?board_no=39&category_no=1
"""
```

## 이번 v5 수정사항

- `현재 게시판 글 확인` 버튼은 기준값을 변경하지 않습니다.
- `기준값 저장` 버튼을 별도로 분리했습니다.
- `기준값 초기화` 버튼을 추가했습니다.
- GitHub Actions가 `state.json`을 실제로 저장하도록 수정했습니다.
