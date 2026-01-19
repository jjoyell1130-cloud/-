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

# --- [2. 스타일 설정: 텍스트 왼쪽 정렬 및 회색 메뉴] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    /* 메인 영역 정렬 */
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* 사이드바 메뉴 버튼: 왼쪽 정렬 + 회색 배경 + 고정 높이 */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        background-color: #f0f2f6 !important; /* 연한 회색 배경 */
        color: #31333f !important;
        border: 1px solid #d1d5db !important;
        
        /* 텍스트 왼쪽 정렬 핵심 설정 */
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        padding-left: 20px !important;
    }
    
    /* 선택된 메뉴 강조 */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #e2e8f0 !important;
        border: 2px solid #64748b !important;
        font-weight: bold !important;
    }

    /* 메모란 및 저장 버튼 스타일 */
    .memo-section { border-top: 1px solid #ddd; padding-top: 20px; margin-top: 20px; }
    
    /* 저장 버튼 전용 스타일: 절대 깨지지 않게 설정 */
    div[data-testid="stSidebar"] .mini-save-container .stButton > button {
        width: 60px !important;
        height: 30px !important;
        min-height: 30px !important;
        font-size: 13px !important;
        padding: 0 !important;
        justify-content: center !important; /* 저장 글자는 중앙 */
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
        margin-left: auto !important; /* 우측 정렬 */
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📂 Menu")
    
    menus = ["🏠 Home", "⚖️ 마감작업", "💳 카드매입 수기입력건"]
    for m in menus:
        is_selected = (st.session_state.selected_menu == m)
        if st.button(m, key=f"btn_{m}", type="primary" if is_selected else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()
    
    # Memo 섹션
    st.markdown('<div class="memo-section">', unsafe_allow_html=True)
    st.markdown("#### 📝 Memo")
    memo_val = st.text_area("memo_input", value=st.session_state.daily_memo, height=150, label_visibility="collapsed", placeholder="여기에 메모를 입력하세요...")
    
    # 저장 버튼 (전용 컨테이너로 감싸서 크기 고정)
    st.markdown('<div class="mini-save-container">', unsafe_allow_html=True)
    if st.button("저장", key="save_memo"):
        st.session_state.daily_memo = memo_val
        st.toast("메모가 저장되었습니다.")
    st.markdown('</div></div>', unsafe_allow_html=True)

# --- [4. 메인 화면 구성] ---
current = st.session_state.selected_menu
st.title(current)

if current == "🏠 Home":
    st.markdown("🏠 **홈: 단축키 관리 및 주요 링크 바로가기**")
    st.divider()
    
    # 링크 버튼 복구
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.link_button("📊 신고리스트", "https://example.com")
    with c2: st.link_button("📁 상반기 자료", "https://example.com")
    with c3: st.link_button("📁 하반기 자료", "https://example.com")
    with c4: st.link_button("💳 카드매입자료", "https://example.com")
    
    st.write("")
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df = pd.DataFrame(st.session_state.account_data)
    st.data_editor(df, num_rows="dynamic", use_container_width=True)

elif current == "⚖️ 마감작업":
    st.markdown("⚖️ **국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.**")
    st.divider()
    
    with st.expander("📝 카톡 안내문 양식 편집", expanded=True):
        st.text_area("양식 내용", value="부가세 신고 마무리되어 전체 자료 전달드립니다...", height=150)
        st.button("양식 저장")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📄 국세청 PDF 업로드")
        st.file_uploader("pdf", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")
    with col2:
        st.markdown("##### 📊 매입매출장 엑셀 업로드")
        st.file_uploader("excel", type=['xlsx'], accept_multiple_files=True, label_visibility="collapsed")

elif current == "💳 카드매입 수기입력건":
    st.markdown("💳 **카드사별 엑셀 파일을 업로드하시면, 위하고 전용 파일로 즉시 변환됩니다.**")
    st.divider()
    st.file_uploader("card", type=['xlsx'], accept_multiple_files=True)
