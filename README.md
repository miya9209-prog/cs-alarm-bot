# 미샵 CS 게시판 새글 알림봇

카페24 CS 게시판의 새글을 확인하고 텔레그램 단체방으로 알림을 보내는 프로그램입니다.

## 핵심 구조

- `Streamlit` : 관리자 확인 화면
- `GitHub Actions` : 10분마다 자동 실행
- `Telegram Bot` : 새글 알림 발송
- `data/notified_posts.json` : 이미 알림 보낸 게시글 중복 방지 파일

## 폴더 구조

```text
misharp-cs-alert-bot/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .env.example
├─ .streamlit/
│  └─ secrets.toml.example
├─ .github/
│  └─ workflows/
│     └─ cs-alert.yml
├─ data/
└─ src/
   ├─ cafe24_board.py
   ├─ check_new_posts.py
   ├─ config.py
   ├─ state.py
   └─ telegram_notify.py
```

## 1. 텔레그램 봇 만들기

1. 텔레그램에서 `BotFather` 검색
2. `/newbot` 입력
3. 봇 이름 입력 예: `Misharp CS Alert Bot`
4. 봇 username 입력 예: `misharp_cs_alert_bot`
5. 발급된 토큰을 복사합니다.
   - 예: `123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## 2. 텔레그램 단체방 만들기

1. 텔레그램에서 CS팀 단체방 생성
2. 방 이름 예: `미샵 CS 알림방`
3. 방에 방금 만든 봇을 초대
4. 아무 메시지나 하나 보냅니다. 예: `테스트`

## 3. TELEGRAM_CHAT_ID 확인

브라우저에서 아래 주소를 엽니다.

```text
https://api.telegram.org/bot여기에_봇토큰/getUpdates
```

예:

```text
https://api.telegram.org/bot123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxx/getUpdates
```

화면에서 `chat` 안의 `id` 값을 찾습니다.
단체방이면 보통 `-100`으로 시작합니다.

예:

```json
"chat":{"id":-1001234567890,"title":"미샵 CS 알림방"}
```

이 경우 `TELEGRAM_CHAT_ID`는 아래 값입니다.

```text
-1001234567890
```

## 4. GitHub 저장소 만들기

1. GitHub 접속
2. New repository 클릭
3. 저장소 이름 예: `misharp-cs-alert-bot`
4. Private 권장
5. ZIP 파일 압축 해제 후 전체 파일 업로드

## 5. GitHub Secrets 설정

GitHub 저장소에서 아래 경로로 이동합니다.

```text
Settings > Secrets and variables > Actions > New repository secret
```

아래 값을 각각 추가합니다.

### TELEGRAM_BOT_TOKEN

```text
BotFather에서 받은 봇 토큰
```

### TELEGRAM_CHAT_ID

```text
-100으로 시작하는 텔레그램 단체방 ID
```

### BOARD_URLS

카페24에서 확인할 게시판 목록 URL을 콤마로 연결합니다.

예:

```text
https://misharp.co.kr/board/product/list.html?board_no=6,https://misharp.co.kr/board/free/list.html?board_no=5
```

실제 미샵 게시판 번호에 맞게 수정해야 합니다.

### CHECK_LIMIT

```text
20
```

## 6. GitHub Actions 실행 확인

1. GitHub 저장소 상단 `Actions` 클릭
2. `Misharp CS Board Alert` 선택
3. `Run workflow` 클릭
4. 텔레그램 방에 테스트 알림이 오는지 확인

정상 작동하면 이후 10분마다 자동으로 새글을 확인합니다.

## 7. Streamlit Cloud 배포

1. Streamlit Cloud 접속
2. `New app` 클릭
3. GitHub 저장소 선택
4. Main file path에 아래 입력

```text
app.py
```

5. Advanced settings > Secrets에 아래 형식으로 입력

```toml
TELEGRAM_BOT_TOKEN = "봇토큰"
TELEGRAM_CHAT_ID = "채팅방ID"
BOARD_URLS = "게시판URL1,게시판URL2"
CHECK_LIMIT = "20"
```

6. Deploy 클릭

## 8. 운영 방식

- 자동 알림은 GitHub Actions가 담당합니다.
- Streamlit은 사람이 확인하는 관리자 화면입니다.
- 새글이 감지되면 텔레그램 단체방으로 아래 형태의 알림이 갑니다.

```text
🔔 미샵 새 CS 문의
게시판 : 상품 Q&A
제목 : 교환 문의드립니다
작성자 : 김OO
시간 : 2026-06-09

바로가기
https://misharp.co.kr/...
```

## 9. 중요한 주의사항

카페24 쇼핑몰 스킨마다 게시판 HTML 구조가 다를 수 있습니다.
처음 실행했을 때 글 목록이 잘 안 잡히면 `src/cafe24_board.py`의 selector를 미샵 게시판 구조에 맞게 한 번 조정해야 합니다.

이 버전은 비용을 최소화하기 위해 카페24 게시판 페이지를 확인하는 방식입니다.
향후 더 안정적으로 운영하려면 카페24 Admin API 방식으로 확장할 수 있습니다.

## 10. 추천 개선 기능

- 30분 이상 미처리 글 재알림
- 답변 완료 여부 확인
- 담당자 배정
- 하루 CS 처리 건수 리포트
- 교환/반품/배송/상품문의 자동 분류


## 설치 오류 대응 v3 안내

Streamlit Cloud에서 `Error installing requirements`가 나올 때를 줄이기 위해 v3에서는 다음처럼 단순화했습니다.

- `pandas` 제거
- 패키지 버전 고정 제거
- `runtime.txt` = `python-3.11.9` 추가
- `.python-version` = `3.11` 추가

GitHub에 업로드할 때는 ZIP 안의 폴더 자체가 아니라 폴더 안의 파일들이 저장소 최상단에 있어야 합니다. 저장소 최상단에 반드시 `app.py`, `requirements.txt`, `runtime.txt`가 보여야 합니다.
