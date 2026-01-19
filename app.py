import streamlit as st
import pandas as pd

# --- [1. 세션 데이터 초기화] ---
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제"},
        {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제"}
    ]
if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

# --- [2. 스타일 설정: 너비 100% 및 왼쪽 정렬 강제] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    /* 메인 여백 최소화 */
    .main .block-container { padding-top: 1.5rem; max-width: 98%; }
    
    /* 모든 버튼(메뉴, 링크)을 창 너비에 꽉 차게 + 왼쪽 정렬 */
    .stButton > button, .stLinkButton > a {
        width: 100% !important;
        height: 3.8rem !important; /* 높이도 더 시원하게 키움 */
        border-radius: 8px !important;
        background-color: #f8f9fa !important;
        color: #333 !important;
        border: 1px solid #d1d5db !important;
        
        /* 텍스트 왼쪽 정렬 및 여유 있는 패딩 */
        display: flex !important;
        justify-content: flex-start !important; 
        align-items: center !important;
        padding-left: 25px !important;
        font-size: 17px !important;
        font-weight: 500 !important;
        text-decoration: none !important;
    }

    /* 사이드바 메뉴 전용 (선택 시 빨간 테두리) */
    div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        border: 2px solid #ff4b4b !important;
        background-color: #ffffff !important;
    }

    /* 메모 저장 버튼만 예외적으로 작게 (우측 정렬) */
    .mini-save-area button {
        width: 65px !important; 
        height: 32px !important;
        min-height: 32px !important;
        font-size: 14px !important;
        padding: 0 !important;
        justify-content: center !important; 
        background-color: white !important;
    }

    /* 카테고리 타이틀 스타일 */
    .cat-header {
        font-size: 1.3rem;
        font-weight: 700;
        margin: 25px 0 15px 0;
        color: #1f2937;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📂 Menu")
    menus = ["🏠 Home", "⚖️ 마감작업", "💳 카드매입 수기입력건"]
    for m in menus:
        is_selected = (st.session_state.selected_menu == m)
        if st.button(m, key=f"side_{m}", type="primary" if is_selected else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()
    
    st.markdown('<div style="border-top: 1px solid #eee; margin-top: 30px; padding-top: 20px;"></div>', unsafe_allow_html=True)
    st.markdown("#### 📝 Memo")
    memo_val = st.text_area("memo", value=st.session_state.daily_memo, height=180, label_visibility="collapsed")
    
    st.markdown('<div class="mini-save-area" style="display:flex; justify-content:flex-end;">', unsafe_allow_html=True)
    if st.button("저장", key="memo_save"):
        st.session_state.daily_memo = memo_val
        st.toast("저장완료")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [4. 메인 화면 구성] ---
current = st.session_state.selected_menu

if current == "🏠 Home":
    st.title("🏠 Home")
    st.divider()
    
    # [바로가기 카테고리]
    st.markdown('<p class="cat-header">🔗 바로가기</p>', unsafe_allow_html=True)
    
    # 상단 2개 (위하고, 홈택스) - 너비를 꽉 채우기 위해 2분할
    col_t1, col_t2 = st.columns(2)
    with col_t1: st.link_button("위하고", "https://www.wehago.com")
    with col_t2: st.link_button("홈택스", "https://www.hometax.go.kr")
    
    st.write("") # 간격
    
    # 하단 4개 - 너비를 위해 2개씩 두 줄로 배치하거나 4분할
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    with col_b1: st.link_button("신고리스트", "https://docs.google.com/...")
    with col_b2: st.link_button("부가세 상반기자료", "https://drive.google.com/...")
    with col_b3: st.link_button("부가세 하반기자료", "https://drive.google.com/...")
    with col_b4: st.link_button("카드매입자료", "https://drive.google.com/...")
    
    st.divider()
    st.markdown('<p class="cat-header">⌨️ 차변 계정 단축키 관리</p>', unsafe_allow_html=True)
    df = pd.DataFrame(st.session_state.account_data)
    st.data_editor(df, num_rows="dynamic", use_container_width=True)

elif current == "⚖️ 마감작업":
    st.title("⚖️ 마감작업")
    st.divider()
    # 마감작업 내용...

elif current == "💳 카드매입 수기입력건":
    st.title("💳 카드매입 수기입력건")
    st.divider()
    # 카드매입 내용...
