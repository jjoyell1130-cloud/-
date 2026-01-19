import streamlit as st
import pandas as pd

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
        "prompt_template": """...""" # 이전과 동일
    }

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

# --- [2. 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { text-align: left !important; justify-content: flex-start !important; }
    
    /* [메뉴 버튼] */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; border-radius: 6px; height: 2.2rem; font-size: 14px; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white; color: #444;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }

    /* [저장 버튼 전용] 훨씬 작고 슬림하게 수정 */
    .memo-save-container div.stButton > button {
        width: auto !important;
        min-width: 50px !important; /* 너비 최소화 */
        max-width: 60px !important;
        height: 1.5rem !important;  /* 높이 최소화 */
        line-height: 1.5rem !important;
        padding: 0px 8px !important;
        font-size: 11px !important; /* 폰트 크기 축소 */
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        margin-top: 2px !important;
        color: #666 !important;
    }
    .memo-save-container div.stButton > button:hover {
        border-color: #9ca3af !important;
        color: #111 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    st.write("")
    
    menu_items = [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
    
    for m_name in menu_items:
        is_selected = (st.session_state.selected_menu == m_name)
        if st.button(m_name, key=f"m_btn_{m_name}", use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()
    
    st.write("")
    st.write("")
    st.divider()
    
    st.markdown("#### 📝 Memo")
    side_memo = st.text_area(
        "Memo Content", 
        value=st.session_state.daily_memo, 
        height=180, 
        placeholder="메모를 입력하세요...",
        label_visibility="collapsed"
    )
    
    # 저장 버튼 컨테이너
    st.markdown('<div class="memo-save-container">', unsafe_allow_html=True)
    if st.button("저장", key="memo_save_btn"):
        st.session_state.daily_memo = side_memo
        st.toast("메모가 저장되었습니다.") # success 대신 toast를 써서 화면을 덜 가리게 할 수 있습니다.
    st.markdown('</div>', unsafe_allow_html=True)

# --- [3. 메인 화면] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()

# (이하 메인 콘텐츠 코드는 이전과 동일)
