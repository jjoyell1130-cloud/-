import streamlit as st
import pandas as pd

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건",
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
        "prompt_template": """*(내용 생략 - 기존과 동일)"""
    }

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

# (링크 및 단축키 데이터 초기화 로직은 기존과 동일하므로 생략)

# --- [2. 스타일 및 사이드바 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# CSS 고도화: 버튼 슬림화 및 선택 상태 강조
st.markdown("""
    <style>
    /* 전체 왼쪽 정렬 */
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* 버튼 슬림 디자인 및 공통 스타일 */
    div.stButton > button {
        width: 100%;
        border-radius: 6px;
        border: 1px solid #eee;
        background-color: #ffffff;
        color: #555;
        height: 2.4rem; /* 높이를 줄여 슬림하게 변경 */
        font-size: 14px;
        font-weight: 400;
        text-align: left !important;
        padding-left: 15px !important;
        margin-bottom: -5px;
        transition: all 0.2s ease;
    }

    /* 마우스 호버 효과 */
    div.stButton > button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }

    /* 선택된 버튼 강조 스타일 (강제 적용을 위한 id 활용 가능하지만, 
       Streamlit 특성상 로직에서 스타일 분기가 어려우므로 
       버튼 텍스트 앞에 특수문자를 활용하거나 하단에 후술할 로직 사용) */
    
    /* 텍스트 왼쪽 정렬 보강 */
    h1, h2, h3, p, span, div { text-align: left !important; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.markdown("### 📁 Menu")
st.sidebar.write("")

# --- [사이드바 메뉴 로직 수정] ---
menu_items = [
    st.session_state.config["menu_0"],
    st.session_state.config["menu_1"],
    st.session_state.config["menu_2"]
]

for m_name in menu_items:
    # 현재 선택된 메뉴인 경우 강조 표시 (색상 구분을 위해 아이콘 활용 권장)
    is_selected = (st.session_state.selected_menu == m_name)
    
    # [핵심] 선택된 메뉴는 배경색과 글자색을 다르게 표현하기 위해 
    # Streamlit의 type="primary" 속성을 활용하면 박스 색상이 입혀집니다.
    button_type = "primary" if is_selected else "secondary"
    
    if st.sidebar.button(m_name, key=f"btn_{m_name}", use_container_width=True, type=button_type):
        st.session_state.selected_menu = m_name
        st.rerun()

# --- [3. 메인 화면 출력] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# 부제목 (왼쪽 정렬)
sub_text = {
    st.session_state.config["menu_0"]: st.session_state.config["sub_home"],
    st.session_state.config["menu_1"]: st.session_state.config["sub_menu1"],
    st.session_state.config["menu_2"]: st.session_state.config["sub_menu2"]
}[current_menu]

st.markdown(f"<p style='color: #666; text-align: left;'>{sub_text}</p>", unsafe_allow_html=True)
st.divider()

# --- [4. 메뉴별 상세 기능] ---
# (기존 기능 로직 유지)
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    # ... (기존 코드와 동일)
    
elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카카오톡 전송용 안내문", expanded=True):
        # ... (기존 코드와 동일)
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)

elif current_menu == st.session_state.config["menu_2"]:
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
