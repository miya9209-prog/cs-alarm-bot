# 미샵 CS 게시판 새글 알림봇 v10

미샵 카페24 게시판 새글을 감지해 텔레그램으로 알림을 보내는 Streamlit + GitHub Actions 프로그램입니다.

## v10 수정사항

- `현재 게시판 글 확인`, `기준값 저장`, `새글 확인` 결과를 게시판별 묶음이 아니라 전체 최신순으로 정렬합니다.
- 포토후기: `/board/review/read_photo.html?board_no=4&no=...`
- 상품문의: `/article/상품문의/6/글번호/`
- 이벤트: `/article/이벤트/39/글번호/categoryno/1/`
- 공지글/답변글/상품 카테고리 링크 제외
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

## 중요한 사용 순서

자동 알림은 Streamlit의 기준값이 아니라 GitHub Actions의 `state.json`을 기준으로 작동합니다.

1. 새 레포 업로드 후 GitHub Actions에서 `Board Monitor`를 한 번 수동 실행합니다.
2. 이 첫 실행이 현재 글들을 `state.json`에 저장합니다.
3. 그 다음 새 문의/후기가 올라오면 GitHub Actions 다음 실행 때 텔레그램 알림이 갑니다.
4. Streamlit의 `기준값 저장`은 화면에서 수동 테스트할 때 쓰는 기능입니다.

## 테스트

1. Streamlit에서 `현재 게시판 글 확인` 클릭 → 포토후기/상품문의/이벤트가 섞여 최신순으로 나오는지 확인
2. GitHub Actions `Board Monitor` 수동 실행 → 초록 체크와 `state.json` 생성 확인
3. 그 이후 새 상품문의 작성
4. GitHub Actions `Board Monitor` 다시 수동 실행 → 텔레그램 알림 확인
