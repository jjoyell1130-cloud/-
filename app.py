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

# --- [2. 스타일 설정: 왼쪽 정렬 및 박스 크기 최적화] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    /* 메인 컨테이너 정렬 */
    .main .block-container { padding-top: 2rem; max-width: 95%; }
    
    /* [바로가기/메뉴 버튼] 왼쪽 정렬 + 큰 박스 고정 */
    .stButton > button, .stLinkButton > a {
        width: 100% !important;
        height: 3.5rem !important; 
        border-radius: 8px !important;
        background-color: #ffffff !important;
        color: #333 !important;
        border: 1px solid #dcdcdc !important;
        
        /* 텍스트 왼쪽 정렬 설정 */
        display: flex !important;
        justify-content: flex-start !important; 
        align-items: center !important;
        padding-left: 20px !important;
        text-decoration: none !important;
    }

    /* 사이드바 메뉴 버튼 (회색 배경 유지) */
    div[data-testid="stSidebar"] .stButton > button {
        background-color: #f8f9fa !important;
    }

    /* 카테고리 제목 스타일 */
    .category-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 15px;
        padding-left: 5px;
        border-left: 5px solid #ff4b4b;
    }

    /* 메모 저장 버튼 (소형) */
    .mini-save-area button {
        width: 60px !important; 
        height: 30px !important;
        min-height: 30px !important;
        padding: 0 !important;
        justify-content: center !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📂 Menu")
    menus = ["🏠 Home", "⚖️ 마감작업", "💳 카드매입 수기입력건"]
    for m in menus:
        is_selected = (st.session_state.selected_menu == m)
        if st.button(m, key=f"side_{m}", type="primary" if is_selected else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()
    
    st.markdown('<div style="border-top: 1px solid #eee; margin-top: 25px; padding-top: 20px;"></div>', unsafe_allow_html=True)
    st.markdown("#### 📝 Memo")
    memo_val = st.text_area("memo", value=st.session_state.daily_memo, height=150, label_visibility="collapsed")
    
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
    
    # [새로운 카테고리: 바로가기]
    st.markdown('<div class="category-title">🔗 바로가기</div>', unsafe_allow_html=True)
    
    # 상단 2개
    t_col1, t_col2, _ = st.columns([1, 1, 2])
    with t_col1: st.link_button("위하고", "https://www.wehago.com")
    with t_col2: st.link_button("홈택스", "https://www.hometax.go.kr")
    
    st.write("") # 간격
    
    # 하단 4개
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    with b_col1: st.link_button("신고리스트", "https://docs.google.com/...")
    with b_col2: st.link_button("부가세 상반기자료", "https://drive.google.com/...")
    with b_col3: st.link_button("부가세 하반기자료", "https://drive.google.com/...")
    with b_col4: st.link_button("카드매입자료", "https://drive.google.com/...")
    
    st.divider()
    st.markdown('<div class="category-title">⌨️ 차변 계정 단축키 관리</div>', unsafe_allow_html=True)
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
