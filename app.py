import streamlit as st
import pandas as pd

# --- [1. 데이터 및 세션 상태 복구] ---
# 차변계정 단축키 데이터 복구
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제"},
        {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제"},
        {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"},
        {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제"},
        {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"}
    ]

# 안내문 양식 복구
if 'prompt_template' not in st.session_state:
    st.session_state.prompt_template = """*{업체명} 부가세 신고현황☆★{결과}
감기 조심하시고 건강이 최고인거 아시죠? ^.<

부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {매출액}원
-매입장: {매입액}원
-접수증 > {결과}: {세액}원"""

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

# --- [2. 스타일 설정: 메뉴 복구 및 저장버튼 분리] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    /* 메인 컨테이너 정렬 */
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* 1. 업무 메뉴 버튼 스타일 (원래대로 크게) */
    div[data-testid="stSidebarNav"] {display: none;} /* 기본 네비게이션 숨김 */
    
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3.2rem !important; /* 이미지처럼 시원하게 높임 */
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding-left: 15px !important;
        margin-bottom: 8px !important;
        border: 1px solid #ddd !important;
        background-color: white !important;
    }
    
    /* 선택된 메뉴 강조 */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important;
        border: 2px solid #ff4b4b !important; /* 이미지의 붉은 테두리 스타일 반영 */
        color: #ff4b4b !important;
    }

    /* 2. 메모 저장 버튼만 아주 작게 (격리된 스타일) */
    .memo-container { margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }
    
    .mini-btn-area { display: flex; justify-content: flex-start; margin-top: 5px; }
    .mini-btn-area button {
        width: 50px !important; 
        height: 24px !important; 
        min-height: 24px !important;
        font-size: 11px !important;
        padding: 0 !important;
        background-color: #f8f9fa !important;
        color: #666 !important;
        border: 1px solid #ccc !important;
        border-radius: 3px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📂 업무 메뉴")
    st.caption("업무 선택")
    
    # 메뉴 박스 (이미지 형태 복구)
    menu_list = ["🏠 Home", "⚖️ 마감작업", "💳 카드매입 수기입력건 엑셀 변환"]
    for m in menu_list:
        is_selected = (st.session_state.selected_menu == m)
        if st.button(m, key=f"m_btn_{m}", type="primary" if is_selected else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()
    
    # Memo 섹션
    st.markdown('<div class="memo-container">', unsafe_allow_html=True)
    st.markdown("#### 📝 Memo")
    memo_text = st.text_area("memo_input", value=st.session_state.daily_memo, height=150, label_visibility="collapsed")
    
    # 저장 버튼 (작게)
    st.markdown('<div class="mini-btn-area">', unsafe_allow_html=True)
    if st.button("저장", key="memo_save_btn"):
        st.session_state.daily_memo = memo_text
        st.toast("메모 저장됨!")
    st.markdown('</div></div>', unsafe_allow_html=True)

# --- [4. 메인 화면: 날아간 내용 복구] ---
current = st.session_state.selected_menu
st.title(current)
st.divider()

if current == "🏠 Home":
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df = pd.DataFrame(st.session_state.account_data)
    new_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 데이터 저장"):
        st.session_state.account_data = new_df.to_dict('records')
        st.success("데이터가 안전하게 보관되었습니다.")

elif current == "⚖️ 마감작업":
    with st.expander("📝 카톡 안내문 양식 편집", expanded=False):
        template = st.text_area("양식 수정", value=st.session_state.prompt_template, height=200)
        if st.button("양식 저장"):
            st.session_state.prompt_template = template
            st.success("양식이 업데이트되었습니다.")
    st.file_uploader("📄 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)

elif current == "💳 카드매입 수기입력건 엑셀 변환":
    st.info("카드사별 엑셀 파일을 업로드하시면 전용 양식으로 변환됩니다.")
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
