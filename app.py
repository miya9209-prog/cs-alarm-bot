import streamlit as st
import pandas as pd
from datetime import datetime

from src.check_new_posts import collect_posts, run_check, format_message
from src.telegram_notify import send_telegram_message
from src.config import BOARD_URLS, TELEGRAM_CHAT_ID

st.set_page_config(page_title="미샵 CS 새글 알림", page_icon="🔔", layout="wide")

st.title("🔔 미샵 CS 게시판 새글 알림")
st.caption("카페24 CS 게시판 새글을 확인하고 텔레그램으로 알림을 보내는 관리 화면입니다.")

with st.sidebar:
    st.header("설정 확인")
    st.write("등록된 게시판 수:", len(BOARD_URLS))
    st.write("텔레그램 채팅방:", "등록됨" if TELEGRAM_CHAT_ID else "미등록")
    st.caption("실제 값은 Streamlit Secrets 또는 GitHub Secrets에 저장합니다.")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("현재 게시판 글 확인", use_container_width=True):
        with st.spinner("게시판을 확인하는 중입니다..."):
            posts = collect_posts()
        st.session_state["posts"] = posts
        st.success(f"최근 글 {len(posts)}건을 확인했습니다.")

with col2:
    if st.button("새글 확인 후 알림 발송", use_container_width=True):
        with st.spinner("새글을 확인하고 알림을 보내는 중입니다..."):
            new_posts = run_check(send_alert=True)
        st.session_state["new_posts"] = new_posts
        st.success(f"새글 {len(new_posts)}건 처리 완료")

with col3:
    if st.button("텔레그램 테스트 발송", use_container_width=True):
        try:
            send_telegram_message(f"✅ 미샵 CS 알림봇 테스트 성공\n시간 : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.success("테스트 메시지를 발송했습니다.")
        except Exception as e:
            st.error(f"발송 실패: {e}")

st.divider()

posts = st.session_state.get("posts", [])
new_posts = st.session_state.get("new_posts", [])

if new_posts:
    st.subheader("방금 감지된 새글")
    for p in new_posts:
        with st.expander(f"{p.board_name} / {p.title}", expanded=True):
            st.text(format_message(p).replace("<b>", "").replace("</b>", ""))
            st.link_button("게시글 바로가기", p.url)

if posts:
    st.subheader("최근 게시글 목록")
    df = pd.DataFrame([p.__dict__ for p in posts])
    st.dataframe(df[["board_name", "title", "author", "created_at", "url"]], use_container_width=True, hide_index=True)
else:
    st.info("왼쪽 버튼을 눌러 게시판 글을 확인하세요.")
