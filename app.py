import streamlit as st
import pandas as pd

# --- [1. 세션 데이터 초기화 (내용 복구)] ---
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제"},
        {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제"},
        {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"},
        {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제"},
        {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"}
    ]

if 'prompt_template' not in st.session_state:
    st.session_state.prompt_template = """*{업체명} 부가세 신고현황☆★{결과}
부가세 신고 마무리되어 전체 자료 전달드립니다."""

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

# --- [2. 스타일 설정: 회색 왼쪽정렬 메뉴 및 레이아웃] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* 메뉴 박스: 회색 배경 + 왼쪽 정렬 + 원래 크기 */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: 8px !important;
        font-size: 15px !important;
        text-align: left !important; /* 왼쪽 정렬 */
        padding-left: 15px !important;
        margin-bottom: 8px !important;
        border: 1px solid #ddd !important;
        background-color: #f8f9fa !important; /* 회색 배경 */
        color: #444 !important;
    }
    
    /* 선택된 메뉴 강조 (약간 더 진한 회색 또는 포인트 컬러) */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #e9ecef !important;
        border: 2px solid #adb5bd !important;
        font-weight: bold !important;
        color: #212529 !important;
    }

    /* 메모 저장 버튼 (초소형 우측 정렬) */
    .mini-save-area { display: flex; justify-content: flex-end; margin-top: 5px; }
    .mini-save-area button {
        width: 55px !important; 
        height: 26px !important;
        min-height: 26px !important;
        font-size: 11px !important;
        padding: 0 !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📂 Menu")
    menu_list = ["🏠 Home", "⚖️ 마감작업", "💳 카드매입 수기입력건"]
    for m in menu_list:
        is_selected = (st.session_state.selected_menu == m)
        if st.button(m, key=f"m_btn_{m}", type="primary" if is_selected else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()
    
    st.divider()
    st.markdown("#### 📝 Memo")
    memo_text = st.text_area("memo_input", value=st.session_state.daily_memo, height=150, label_visibility="collapsed")
    
    st.markdown('<div class="mini-save-area">', unsafe_allow_html=True)
    if st.button("저장", key="memo_save_btn"):
        st.session_state.daily_memo = memo_text
        st.toast("저장완료!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [4. 메인 화면: 날아간 내용 전체 복구] ---
current = st.session_state.selected_menu
st.title(current)
st.divider()

if current == "🏠 Home":
    # 바로가기 링크 복구
    st.subheader("🔗 주요 링크 바로가기")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.link_button("📊 신고리스트", "https://docs.google.com/spreadsheets/...")
    with c2: st.link_button("📁 상반기 자료", "https://drive.google.com/...")
    with c3: st.link_button("📁 하반기 자료", "https://drive.google.com/...")
    with c4: st.link_button("💳 카드매입자료", "https://drive.google.com/...")
    
    st.write("")
    st.markdown("##### ⌨️ 차변 계정 단축키 관리")
    df = pd.DataFrame(st.session_state.account_data)
    new_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 데이터 저장"):
        st.session_state.account_data = new_df.to_dict('records')
        st.success("단축키 데이터가 저장되었습니다.")

elif current == "⚖️ 마감작업":
    with st.expander("📝 카톡 안내문 양식 편집", expanded=True):
        template = st.text_area("양식 내용", value=st.session_state.prompt_template, height=150)
        if st.button("양식 저장"):
            st.session_state.prompt_template = template
            st.toast("양식 업데이트 완료")
    
    st.write("")
    # 업로드 칸 2개 복구 (PDF + 엑셀)
    st.markdown("##### 📄 파일 업로드")
    col1, col2 = st.columns(2)
    with col1:
        st.file_uploader("📄 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    with col2:
        st.file_uploader("📊 매입매출장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)

elif current == "💳 카드매입 수기입력건":
    st.info("카드사별 엑셀 파일을 업로드하시면 위하고 수기입력 양식으로 변환됩니다.")
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
