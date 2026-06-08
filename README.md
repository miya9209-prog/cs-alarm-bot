# 미샵 CS 게시판 새글 알림봇

카페24 게시판 새글을 확인해서 텔레그램 단체방으로 알림을 보내는 프로그램입니다.

## 포함 기능

- Streamlit 관리자 화면
- 텔레그램 테스트 발송
- 게시판 현재 글 확인
- 새글 확인 후 알림 발송
- GitHub Actions 10분마다 자동 감시
- 중복 알림 방지용 `state.json` 자동 저장

## GitHub 저장소 최상단에 있어야 하는 파일

반드시 저장소 첫 화면에 아래가 바로 보여야 합니다.

```text
.github
src
app.py
requirements.txt
runtime.txt
README.md
```

`.github` 폴더가 없으면 Actions 자동감시가 동작하지 않습니다.

## Streamlit Secrets

Streamlit Cloud > Manage app > Settings > Secrets 에 입력:

```toml
TELEGRAM_BOT_TOKEN = "BotFather가 준 봇토큰"
TELEGRAM_CHAT_ID = "-5152305178"
BOARD_URLS = """
https://misharp.co.kr/board/review/photo.html?board_no=4
https://misharp.co.kr/board/product/list.html?board_no=6
https://misharp.co.kr/board/gallery/list.html?board_no=39&category_no=1
"""
```

## GitHub Secrets

GitHub 저장소 > Settings > Secrets and variables > Actions > New repository secret 에 아래 3개 추가:

1. `TELEGRAM_BOT_TOKEN`
2. `TELEGRAM_CHAT_ID`
3. `BOARD_URLS`

`BOARD_URLS` 값:

```text
https://misharp.co.kr/board/review/photo.html?board_no=4
https://misharp.co.kr/board/product/list.html?board_no=6
https://misharp.co.kr/board/gallery/list.html?board_no=39&category_no=1
```

## 자동 알림 테스트

1. GitHub 저장소 > Actions 클릭
2. 왼쪽 `Misharp CS Board Monitor` 선택
3. `Run workflow` 클릭
4. 첫 실행은 현재 글을 기준값으로 저장합니다.
5. 이후 새 게시글이 생기면 텔레그램으로 알림이 갑니다.

## 주의

- 첫 실행 때는 기존 게시글을 모두 새글로 보내지 않기 위해 기준값만 저장합니다.
- 새글 테스트는 첫 실행 이후에 게시판에 새 글을 작성한 다음 다시 실행해야 확인됩니다.
- 카페24 스킨 구조가 바뀌면 `src/cafe24_board.py`의 추출 로직을 조정해야 할 수 있습니다.
