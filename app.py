import streamlit as st
from src.config import board_urls, telegram_bot_token, telegram_chat_id
from src.cafe24_board import fetch_all_boards
from src.monitor import run_monitor
from src.telegram_alert import send_telegram_message

st.set_page_config(page_title="미샵 CS 게시판 새글 알림", page_icon="🔔", layout="wide")

urls = board_urls()
token = telegram_bot_token()
chat_id = telegram_chat_id()

with st.sidebar:
    st.header("설정 확인")
    st.write(f"등록된 게시판 수: **{len(urls)}**")
    st.write("텔레그램 채팅방: **등록됨**" if chat_id else "텔레그램 채팅방: **미등록**")
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
            st.success(f"{len(posts)}개 항목을 확인했습니다.")
            for p in posts:
                st.markdown(f"**[{p.board_name}] {p.title}**")
                st.write(p.url)
                st.divider()

with col2:
    if st.button("새글 확인 후 알림 발송", use_container_width=True):
        with st.spinner("새글 확인 중..."):
            result = run_monitor(send_alerts=True)
        if result.get("ok"):
            st.success(result.get("message"))
        else:
            st.error(result.get("message"))
        st.write(f"새글 수: {result.get('new_count', 0)}")

with col3:
    if st.button("텔레그램 테스트 발송", use_container_width=True):
        ok, msg = send_telegram_message(token, chat_id, "🔔 미샵 CS 알림봇 테스트 메시지입니다.")
        if ok:
            st.success("텔레그램 테스트 발송 성공")
        else:
            st.error(msg)

st.info("처음 자동 실행 시에는 현재 게시글을 기준값으로 저장하고, 그 다음 새글부터 알림을 보냅니다.")
