import streamlit as st
import pandas as pd

# --- [1. 세션 데이터 초기화] ---
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제"},
        {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제"},
        {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"},
        {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제"},
        {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"}
    ]

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

# --- [2. 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    /* 메인 영역 정렬 */
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* 사이드바 메뉴 버튼 (원래 크기) */
    div[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        text-align: left !important;
        padding-left: 15px !important;
        margin-bottom: 8px !important;
        border: 1px solid #ddd !important;
        background-color: white !important;
    }
    
    /* 선택된 메뉴 강조 (빨간 테두리) */
    div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important;
        border: 2px solid #ff4b4b !important;
        color: #ff4b4b !important;
    }

    /* 메모 저장 버튼 (매우 작게 우측 정렬) */
    .memo-btn-wrapper { display: flex; justify-content: flex-end; margin-top: 5px; }
    .memo-btn-wrapper button {
        width: 55px !important;
        height: 28px !important;
        min-height: 28px !important;
        font-size: 12px !important;
        padding: 0 !important;
        background-color: #ffffff !important;
        color: #333 !important;
        border: 1px solid #ccc !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바: 메뉴 및 메모] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    
    # 메뉴 구성
    menu_options = ["🏠 Home", "⚖️ 마감작업", "💳 카드매입 수기입력건"]
    for m in menu_options:
        if st.button(m, key=f"menu_{m}", type="primary" if st.session_state.selected_menu == m else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()
    
    st.write("")
    st.divider()
    
    # 메모란 (제목: Memo)
    st.markdown("#### 📝 Memo")
    memo_input = st.text_area("memo_area", value=st.session_state.daily_memo, height=150, label_visibility="collapsed", placeholder="메모를 입력하세요...")
    
    # 저장 버튼 (작게 배치)
    st.markdown('<div class="memo-btn-wrapper">', unsafe_allow_html=True)
    if st.button("저장", key="memo_save"):
        st.session_state.daily_memo = memo_input
        st.toast("메모가 저장되었습니다!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [4. 메인 화면: 기능 복구] ---
current = st.session_state.selected_menu
st.title(current)
st.divider()

if current == "🏠 Home":
    st.markdown("##### ⌨️ 차변 계정 단축키 관리")
    df = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 단축키 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("데이터가 성공적으로 저장되었습니다.")

elif current == "⚖️ 마감작업":
    # 카톡 안내문 (항상 열림)
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        st.text_area("양식 내용", value="*{업체명} 부가세 신고현황... (내용 생략)", height=150)
        st.button("양식 저장")
    
    st.write("")
    # 업로드 칸 2개 복구
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("📄 **국세청 PDF 업로드**")
        st.file_uploader("pdf", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")
    with c2:
        st.markdown("📊 **매입매출장 엑셀 업로드**")
        st.file_uploader("excel", type=['xlsx'], accept_multiple_files=True, label_visibility="collapsed")

elif current == "💳 카드매입 수기입력건":
    st.markdown("##### 💳 카드사별 엑셀 파일 업로드")
    st.file_uploader("card", type=['xlsx'], accept_multiple_files=True, label_visibility="collapsed")
