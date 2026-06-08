import streamlit as st

from src.config import get_board_urls, get_telegram_chat_id, get_telegram_token
from src.monitor import check_new_posts, get_current_posts, initialize_current_posts, reset_state
from src.telegram_alert import send_telegram_message
from src.state import STATE_FILE

st.set_page_config(page_title="미샵 CS 게시판 새글 알림", page_icon="🔔", layout="wide")

board_urls = get_board_urls()
chat_id = get_telegram_chat_id()
token = get_telegram_token()

with st.sidebar:
    st.header("설정 확인")
    st.write(f"등록된 게시판 수: **{len(board_urls)}**")
    st.write(f"텔레그램 채팅방: **{'등록됨' if chat_id else '미등록'}**")
    st.write(f"봇 토큰: **{'등록됨' if token else '미등록'}**")
    st.write(f"기준값 파일: **{'있음' if STATE_FILE.exists() else '없음'}**")
    st.caption("실제 값은 Streamlit Secrets 또는 GitHub Secrets에 저장합니다.")

st.title("🔔 미샵 CS 게시판 새글 알림")
st.caption("카페24 CS 게시판 새글을 확인하고 텔레그램으로 알림을 보내는 관리 화면입니다.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("현재 게시판 글 확인", use_container_width=True):
        posts = get_current_posts()
        st.success(f"{len(posts)}개 항목을 확인했습니다. 이 버튼은 기준값을 변경하지 않습니다.")
        for p in posts:
            st.markdown(f"**[{p.board_name}] {p.title}**")
            st.write(p.url)
            st.divider()

with col2:
    if st.button("기준값 저장", use_container_width=True):
        result = initialize_current_posts()
        st.success(f"현재 글 {result['saved']}개를 기준값으로 저장했습니다. 이후 새글부터 알림이 갑니다.")

with col3:
    if st.button("새글 확인 후 알림 발송", use_container_width=True):
        result = check_new_posts(send_alert=True)
        if result.get("initialized"):
            st.info("기준값 파일이 없어 현재 글을 기준값으로 저장했습니다. 새글 알림은 다음 실행부터 발송됩니다.")
        else:
            st.success(f"새글 수: {result['new_count']}개")
            for p in result["posts"]:
                st.markdown(f"**[{p.board_name}] {p.title}**")
                st.write(p.url)
                st.divider()

with col4:
    if st.button("텔레그램 테스트 발송", use_container_width=True):
        send_telegram_message(token, chat_id, "🔔 미샵 CS 알림봇 테스트 메시지입니다.")
        st.success("텔레그램 테스트 메시지를 발송했습니다.")

st.divider()

if st.button("기준값 초기화", type="secondary"):
    reset_state()
    st.warning("기준값을 초기화했습니다. 다음 새글 확인 시 현재 글을 기준값으로 다시 저장합니다.")

st.info("운영 순서: 1) 현재 게시판 글 확인 → 2) 기준값 저장 1회 → 3) 이후 GitHub Actions가 자동으로 새글을 감지합니다.")
