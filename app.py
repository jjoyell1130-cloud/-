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

# --- [2. 스타일 설정: 텍스트 왼쪽 정렬 및 버튼 최적화] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    /* 메인 컨테이너 정렬 */
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* [메뉴 버튼] 왼쪽 정렬 + 회색 배경 */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3.2rem !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        background-color: #f0f2f6 !important;
        color: #31333f !important;
        border: 1px solid #d1d5db !important;
        display: flex !important;
        justify-content: flex-start !important; /* 왼쪽 정렬 */
        align-items: center !important;
        padding-left: 20px !important;
    }
    
    /* [메모 저장 버튼] 글자 깨짐 방지 및 우측 정렬 */
    div[data-testid="stSidebar"] .mini-save-container .stButton > button {
        width: 70px !important;
        height: 32px !important;
        min-height: 32px !important;
        font-size: 14px !important;
        padding: 0 !important;
        justify-content: center !important; /* 저장 글자는 가운데 */
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
        margin-left: auto !important;
    }

    /* 링크 버튼(st.link_button) 텍스트 왼쪽 정렬 */
    .stLinkButton > a {
        display: flex !important;
        justify-content: flex-start !important;
        padding-left: 15px !important;
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
        st.toast("메모가 저장되었습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [4. 메인 화면 구성] ---
current = st.session_state.selected_menu
st.title(current)

if current == "🏠 Home":
    st.markdown('<p class="sub-title">🏠 홈: 단축키 관리 및 주요 링크 바로가기</p>', unsafe_allow_html=True)
    st.divider()
    
    # [링크 상단] 2개 배치
    top_c1, top_c2, _ = st.columns([1, 1, 2])
    with top_c1: st.link_button("🌐 WEHAGO 바로가기", "https://www.wehago.com")
    with top_c2: st.link_button("🏛️ 국세청 홈택스", "https://www.hometax.go.kr")
    
    st.write("") # 간격
    
    # [링크 하단] 4개 배치
    bot_c1, bot_c2, bot_c3, bot_c4 = st.columns(4)
    with bot_c1: st.link_button("📊 신고리스트", "https://docs.google.com/...")
    with bot_c2: st.link_button("📂 상반기 자료", "https://drive.google.com/...")
    with bot_c3: st.link_button("📂 하반기 자료", "https://drive.google.com/...")
    with bot_c4: st.link_button("💳 카드매입자료", "https://drive.google.com/...")
    
    st.divider()
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df = pd.DataFrame(st.session_state.account_data)
    st.data_editor(df, num_rows="dynamic", use_container_width=True)

elif current == "⚖️ 마감작업":
    st.markdown('<p class="sub-title">⚖️ 국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.</p>', unsafe_allow_html=True)
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

elif current == "💳 카드매입 수기입력건":
    st.markdown('<p class="sub-title">💳 카드사별 엑셀 파일을 업로드하시면 전용 양식으로 즉시 변환됩니다.</p>', unsafe_allow_html=True)
    st.divider()
    st.file_uploader("card", type=['xlsx'], accept_multiple_files=True)
