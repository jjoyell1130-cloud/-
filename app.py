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

# --- [2. CSS 스타일: 왼쪽 정렬 및 박스 크기 강제 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    /* 메인 컨테이너 여백 조정 */
    .main .block-container { padding-top: 2rem; max-width: 95%; }
    
    /* 사이드바 메뉴 버튼 스타일: 왼쪽 정렬 + 큰 박스 + 회색 배경 */
    div[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3.5rem !important; /* 박스 높이 키움 */
        border-radius: 10px !important;
        background-color: #f8f9fa !important; /* 회색 배경 */
        color: #333 !important;
        border: 1px solid #dcdcdc !important;
        
        /* 왼쪽 정렬을 위한 핵심 설정 */
        display: flex !important;
        justify-content: flex-start !important; 
        align-items: center !important;
        padding-left: 20px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }
    
    /* 버튼 호버 및 클릭 시 효과 */
    div[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #ff4b4b !important;
        background-color: #f0f2f6 !important;
    }
    
    /* 선택된 메뉴 강조 */
    div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #edf2f7 !important;
        border: 2px solid #ff4b4b !important; /* 이미지의 붉은 테두리 복구 */
    }

    /* 메모 저장 버튼: 소형화 유지 (우측 하단 배치) */
    .mini-save-area { display: flex; justify-content: flex-end; margin-top: 8px; }
    .mini-save-area button {
        width: 60px !important; 
        height: 30px !important;
        min-height: 30px !important;
        font-size: 13px !important;
        padding: 0 !important;
        justify-content: center !important; /* 저장 글자만 중앙 */
        background-color: white !important;
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
    
    st.markdown('<div class="mini-save-area">', unsafe_allow_html=True)
    if st.button("저장", key="memo_save"):
        st.session_state.daily_memo = memo_val
        st.toast("메모 저장됨!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [4. 메인 화면 구성] ---
current = st.session_state.selected_menu

if current == "🏠 Home":
    st.title("🏠 Home")
    st.divider()
    
    # [상단 링크 2개]
    t_col1, t_col2, _ = st.columns([1, 1, 2])
    with t_col1: st.link_button("위하고", "https://www.wehago.com", use_container_width=True)
    with t_col2: st.link_button("홈택스", "https://www.hometax.go.kr", use_container_width=True)
    
    st.write("") 
    
    # [하단 링크 4개]
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    with b_col1: st.link_button("신고리스트", "https://docs.google.com/...", use_container_width=True)
    with b_col2: st.link_button("부가세 상반기자료", "https://drive.google.com/...", use_container_width=True)
    with b_col3: st.link_button("부가세 하반기자료", "https://drive.google.com/...", use_container_width=True)
    with b_col4: st.link_button("카드매입자료", "https://drive.google.com/...", use_container_width=True)
    
    st.divider()
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df = pd.DataFrame(st.session_state.account_data)
    st.data_editor(df, num_rows="dynamic", use_container_width=True)

elif current == "⚖️ 마감작업":
    st.title("⚖️ 마감작업")
    st.markdown('<p style="color: #666;">국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.</p>', unsafe_allow_html=True)
    st.divider()
    with st.expander("📝 카톡 안내문 양식 편집", expanded=True):
        st.text_area("양식 내용", value="부가세 신고 마무리되어 전체 자료 전달드립니다...", height=150)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📄 국세청 PDF 업로드")
        st.file_uploader("pdf", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")
    with col2:
        st.markdown("##### 📊 매입매출장 엑셀 업로드")
        st.file_uploader("excel", type=['xlsx'], accept_multiple_files=True, label_visibility="collapsed")
