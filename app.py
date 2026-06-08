import streamlit as st
from src.config import board_urls, telegram_bot_token, telegram_chat_id
from src.cafe24_board import fetch_all_boards
from src.monitor import run_monitor, initialize_current_posts
from src.telegram_alert import send_telegram_message
from src.state import reset_seen, state_exists

st.set_page_config(page_title="미샵 CS 게시판 새글 알림", page_icon="🔔", layout="wide")

urls = board_urls()
token = telegram_bot_token()
chat_id = telegram_chat_id()

with st.sidebar:
    st.header("설정 확인")
    st.write(f"등록된 게시판 수: **{len(urls)}**")
    st.write("텔레그램 채팅방: **등록됨**" if chat_id else "텔레그램 채팅방: **미등록**")
    st.write("기준값 파일: **있음**" if state_exists() else "기준값 파일: **없음**")
    st.caption("실제 값은 Streamlit Secrets 또는 GitHub Secrets에 저장합니다.")

st.title("🔔 미샵 CS 게시판 새글 알림")
st.caption("카페24 CS 게시판 새글을 확인하고 텔레그램으로 알림을 보내는 관리 화면입니다.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("현재 게시판 글 확인", use_container_width=True):
        if not urls:
            st.error("BOARD_URLS가 비어 있습니다.")
        else:
            with st.spinner("게시판 확인 중..."):
                posts = fetch_all_boards(urls, limit_per_board=10)
            st.success(f"{len(posts)}개 항목을 확인했습니다. 이 버튼은 기준값을 변경하지 않습니다.")
            for p in posts:
                st.markdown(f"**[{p.board_name}] {p.title}**")
                st.write(p.url)
                st.divider()

with col2:
    if st.button("기준값 저장", use_container_width=True):
        with st.spinner("현재 글을 기준값으로 저장 중..."):
            result = initialize_current_posts()
        if result.get("ok"):
            st.success(result.get("message"))
        else:
            st.error(result.get("message"))

with col3:
    if st.button("새글 확인 후 알림 발송", use_container_width=True):
        with st.spinner("새글 확인 중..."):
            # In the Streamlit screen, if there is no baseline yet, alert current posts for testing.
            result = run_monitor(send_alerts=True, first_run_send_current=True)
        if result.get("ok"):
            st.success(result.get("message"))
        else:
            st.error(result.get("message"))
        st.write(f"새글 수: {result.get('new_count', 0)}")
        if result.get("new_posts"):
            st.subheader("알림 대상 글")
            for p in result["new_posts"]:
                st.markdown(f"**[{p.board_name}] {p.title}**")
                st.write(p.url)

st.divider()
col4, col5 = st.columns(2)
with col4:
    if st.button("텔레그램 테스트 발송", use_container_width=True):
        ok, msg = send_telegram_message(token, chat_id, "🔔 미샵 CS 알림봇 테스트 메시지입니다.")
        if ok:
            st.success("텔레그램 테스트 발송 성공")
        else:
            st.error(msg)
with col5:
    if st.button("기준값 초기화", use_container_width=True):
        reset_seen()
        st.warning("기준값을 초기화했습니다. 다음 '새글 확인 후 알림 발송'을 누르면 현재 목록이 알림 대상이 될 수 있습니다.")

st.info("권장 순서: ① 현재 게시판 글 확인 → ② 기준값 저장 → ③ 그 이후 새글 작성 → ④ 새글 확인 후 알림 발송 또는 GitHub Actions 자동 실행")
