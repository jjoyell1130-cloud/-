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
    
    /* [메뉴 버튼] 사이드바 전체 너비 버튼 */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; border-radius: 6px; height: 2.2rem; font-size: 14px; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white; color: #444;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }

    /* [메모 저장 버튼 전용 스타일] 작고 슬림하게 */
    .memo-save-container div.stButton > button {
        width: auto !important; /* 너비를 글자에 맞춤 */
        min-width: 80px;
        height: 1.8rem !important; /* 높이를 더 낮춤 */
        font-size: 12px !important;
        padding: 0 10px !important;
        background-color: #f8f9fa !important;
        border: 1px solid #eee !important;
        margin-top: 5px;
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
        height=200, 
        placeholder="Enter your notes here...",
        label_visibility="collapsed"
    )
    
    # 메모 저장 버튼을 별도의 컨테이너로 감싸 스타일 적용
    st.markdown('<div class="memo-save-container">', unsafe_allow_html=True)
    if st.button("💾 Memo Save", key="memo_save_btn"):
        st.session_state.daily_memo = side_memo
        st.success("Saved")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [3. 메인 화면 출력 및 기능] ---
# (이후 코드는 이전과 동일)
current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("⌨️ 차변계정 단축키")
    # ... (생략)
