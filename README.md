# 미샵 CS 게시판 새글 알림봇 v11

## 핵심 수정
- 전체 게시판 리스팅을 `post_no` 기준 최신순으로 정렬합니다.
- 포토후기, 상품문의, 이벤트가 게시판별 묶음으로 나오지 않고 전체 최신순으로 섞여 나옵니다.
- 이벤트처럼 날짜는 있지만 오래된 글번호인 게시글이 최신 문의보다 위로 올라오는 문제를 줄였습니다.
- GitHub Actions 실행 로그에 현재 감지 글 목록과 새글 목록을 출력합니다.

## 등록 URL 예시
```toml
BOARD_URLS = """
https://misharp.co.kr/board/review/photo.html?board_no=4
https://misharp.co.kr/board/product/list.html?board_no=6
https://misharp.co.kr/board/gallery/list.html?board_no=39&category_no=1
"""
```

## 자동 알림 테스트 순서
1. GitHub Actions > Board Monitor > Run workflow 1회 실행
2. 레포 최상단에 `state.json`이 생성/업데이트되는지 확인
3. 그 다음 미샵에 새 상품문의 또는 후기 작성
4. GitHub Actions > Board Monitor > Run workflow 다시 실행
5. 텔레그램 알림 확인

주의: Streamlit의 `기준값 저장`은 Streamlit 서버 안의 수동 테스트 기준값입니다. 자동 알림은 GitHub Actions가 레포의 `state.json`으로 관리합니다.
