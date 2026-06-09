import streamlit as st

from src.config import get_board_urls, get_telegram_chat_id, get_telegram_token
from src.monitor import check_new_posts, get_current_posts, initialize_current_posts, reset_state
from src.state import seen_count, state_exists
from src.telegram_alert import send_telegram_message

st.set_page_config(page_title="미샵 CS 게시판 새글 알림", page_icon="🔔", layout="wide")

board_urls = get_board_urls()
token = get_telegram_token()
chat_id = get_telegram_chat_id()

with st.sidebar:
    st.header("설정 확인")
    st.write(f"등록된 게시판 수: **{len(board_urls)}**")
    st.write(f"텔레그램 채팅방: **{'등록됨' if chat_id else '미등록'}**")
    st.write(f"기준값 파일: **{'있음' if state_exists() else '없음'}**")
    st.write(f"기준값 개수: **{seen_count()}**")
    st.caption("기준값 저장은 '현재까지 보이는 글은 이미 확인한 글'로 등록하는 버튼입니다.")

st.title("🔔 미샵 CS 게시판 새글 알림")
st.caption("카페24 CS 게시판 새글을 확인하고 텔레그램으로 알림을 보내는 관리 화면입니다.")

col1, col2, col3, col4 = st.columns(4)


def render_posts(posts):
    for p in posts:
        st.markdown(f"**[{p.board_name}] {p.title}**")
        st.write(p.url)
        st.caption(f"ID: {getattr(p, 'post_id', '')}")
        st.divider()


with col1:
    if st.button("현재 게시판 글 확인", use_container_width=True):
        posts = get_current_posts()
        st.success(f"{len(posts)}개 항목을 확인했습니다. 이 버튼은 기준값을 변경하지 않습니다.")
        render_posts(posts)

with col2:
    if st.button("기준값 저장", use_container_width=True):
        result = initialize_current_posts()
        st.success(
            f"기준값 저장 완료: {result.get('saved', 0)}개 저장 / 총 {result.get('total', 0)}개 확인"
        )
        st.info("이후 새로 작성되는 글부터 알림 대상입니다. 기준값 저장 직후 바로 확인하면 새글 0개가 정상입니다.")
        render_posts(result.get("posts", []))

with col3:
    if st.button("새글 확인 후 알림 발송", use_container_width=True):
        result = check_new_posts(send_alert=True, initialize_if_missing=False)
        st.success(f"새글 수: {result.get('new_count', 0)}개")
        if result.get("new_posts"):
            render_posts(result.get("new_posts", []))
        else:
            st.caption("기준값 저장 이후 새로 올라온 글이 없거나, 새 글이 아직 공개 게시판에 노출되지 않은 상태입니다.")

with col4:
    if st.button("텔레그램 테스트 발송", use_container_width=True):
        send_telegram_message(token, chat_id, "🔔 미샵 CS 알림 테스트입니다.")
        st.success("텔레그램 테스트 메시지를 발송했습니다.")

st.divider()

left, right = st.columns(2)
with left:
    if st.button("기준값 초기화"):
        reset_state()
        st.warning("기준값을 초기화했습니다. 먼저 '기준값 저장'을 한 번 눌러주세요.")

with right:
    st.markdown("### 사용 순서")
    st.write("1. 현재 게시판 글 확인 → 글이 정상적으로 보이는지 확인")
    st.write("2. 기준값 저장 → 현재 글들을 이미 확인한 글로 등록")
    st.write("3. 그 이후 새 글 작성/노출")
    st.write("4. 새글 확인 후 알림 발송 또는 GitHub Actions 자동 실행")
