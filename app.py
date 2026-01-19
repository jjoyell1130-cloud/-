import streamlit as st
import pandas as pd

# --- [1. 세션 데이터 및 설정 복구] ---
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제"},
        {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제"},
        {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"},
        {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제"},
        {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"}
    ]

# 메뉴별 부제목 설정
sub_titles = {
    "🏠 Home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
    "⚖️ 마감작업": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
    "💳 카드매입 수기입력건": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다."
}

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

# --- [2. 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* 메뉴 박스: 회색 배경 + 왼쪽 정렬 */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: 8px !important;
        font-size: 15px !important;
        text-align: left !important;
        padding-left: 15px !important;
        margin-bottom: 8px !important;
        border: 1px solid #ddd !important;
        background-color: #f8f9fa !important;
        color: #444 !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #e9ecef !important;
        border: 2px solid #adb5bd !important;
        font-weight: bold !important;
        color: #212529 !important;
    }

    /* 메모 저장 버튼: 최소 사이즈 우측 정렬 */
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
    
    /* 부제목 스타일 */
    .sub-title { color: #666; font-size: 14px; margin-bottom: 20px; margin-top: -10px; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
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

# --- [4. 메인 화면 구성] ---
current = st.session_state.selected_menu
st.title(current)

# 부제목 표시
st.markdown(f'<p class="sub-title">{sub_titles[current]}</p>', unsafe_allow_html=True)
st.divider()

if current == "🏠 Home":
    # 바로가기 링크 복구
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
        st.success("데이터가 저장되었습니다.")

elif current == "⚖️ 마감작업":
    # 카톡 안내문 (항상 열림)
    with st.expander("📝 카톡 안내문 양식 편집", expanded=True):
        st.text_area("양식 내용", value="부가세 신고 마무리되어 전체 자료 전달드립니다...", height=150)
        st.button("양식 저장")
    
    st.write("")
    # 업로드 칸 복구
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📄 국세청 PDF 업로드")
        st.file_uploader("pdf_up", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")
    with col2:
        st.markdown("##### 📊 매입매출장 엑셀 업로드")
        st.file_uploader("excel_up", type=['xlsx'], accept_multiple_files=True, label_visibility="collapsed")

elif current == "💳 카드매입 수기입력건":
    st.markdown("##### 💳 카드사 엑셀 파일 업로드")
    st.file_uploader("card_up", type=['xlsx'], accept_multiple_files=True, label_visibility="collapsed")
