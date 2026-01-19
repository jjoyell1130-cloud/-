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

# --- [2. 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* 메뉴 버튼: 회색 배경 + 왼쪽 정렬 */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        background-color: #f0f2f6 !important;
        color: #31333f !important;
        border: 1px solid #d1d5db !important;
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        padding-left: 20px !important;
    }
    
    /* 메모 저장 버튼: 소형화 및 우측 정렬 */
    div[data-testid="stSidebar"] .mini-save-container .stButton > button {
        width: 55px !important;
        height: 28px !important;
        min-height: 28px !important;
        font-size: 12px !important;
        padding: 0 !important;
        justify-content: center !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
        margin-left: auto !important;
    }

    /* 링크 버튼 텍스트 왼쪽 정렬 */
    .stLinkButton > a {
        display: flex !important;
        justify-content: flex-start !important;
        padding-left: 15px !important;
        background-color: #ffffff !important;
        border: 1px solid #ddd !important;
    }
    
    .sub-title { color: #666; font-size: 15px; margin-top: -10px; margin-bottom: 20px; }
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
    
    st.markdown('<div style="border-top: 1px solid #ddd; margin-top: 20px; padding-top: 20px;"></div>', unsafe_allow_html=True)
    st.markdown("#### 📝 Memo")
    memo_val = st.text_area("memo_input", value=st.session_state.daily_memo, height=150, label_visibility="collapsed")
    
    st.markdown('<div class="mini-save-container">', unsafe_allow_html=True)
    if st.button("저장", key="save_memo"):
        st.session_state.daily_memo = memo_val
        st.toast("저장완료")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [4. 메인 화면 구성] ---
current = st.session_state.selected_menu

if current == "🏠 Home":
    st.title("🏠 Home")
    st.divider()
    
    # [상단 링크 2개]
    t_col1, t_col2, _ = st.columns([1, 1, 2])
    with t_col1: st.link_button("위하고", "https://www.wehago.com")
    with t_col2: st.link_button("홈택스", "https://www.hometax.go.kr")
    
    st.write("") 
    
    # [하단 링크 4개]
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    with b_col1: st.link_button("신고리스트", "https://docs.google.com/...")
    with b_col2: st.link_button("부가세 상반기자료", "https://drive.google.com/...")
    with b_col3: st.link_button("부가세 하반기자료", "https://drive.google.com/...")
    with b_col4: st.link_button("카드매입자료", "https://drive.google.com/...")
    
    st.divider()
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df = pd.DataFrame(st.session_state.account_data)
    st.data_editor(df, num_rows="dynamic", use_container_width=True)

elif current == "⚖️ 마감작업":
    st.title("⚖️ 마감작업")
    st.markdown('<p class="sub-title">국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.</p>', unsafe_allow_html=True)
    st.divider()
    with st.expander("📝 카톡 안내문 양식 편집", expanded=True):
        st.text_area("양식 내용", value="부가세 신고 마무리되어 전체 자료 전달드립니다...", height=150)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📄 국세청 PDF 업로드")
        st.file_uploader("pdf_up", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")
    with col2:
        st.markdown("##### 📊 매입매출장 엑셀 업로드")
        st.file_uploader("excel_up", type=['xlsx'], accept_multiple_files=True, label_visibility="collapsed")

elif current == "💳 카드매입 수기입력건":
    st.title("💳 카드매입 수기입력건")
    st.markdown('<p class="sub-title">카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.</p>', unsafe_allow_html=True)
    st.divider()
    st.file_uploader("card_up", type=['xlsx'], accept_multiple_files=True)
