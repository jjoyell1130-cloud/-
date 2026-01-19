import streamlit as st
import pandas as pd

# --- [1. 세션 상태 초기화] ---
if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"
if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제"}]

# --- [2. 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    /* 전체 레이아웃 정렬 */
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    
    /* [메뉴 버튼] 사이드바 전체 너비 버튼 */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100%; border-radius: 6px; height: 2.2rem; font-size: 14px; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -5px; border: 1px solid #ddd; background-color: white; color: #444;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }

    /* [저장 버튼] 전용 스타일 - 메뉴 버튼과 확실히 다르게 설정 */
    div[data-testid="stSidebar"] .memo-save-area button {
        height: 1.6rem !important;
        min-height: 1.6rem !important;
        width: 60px !important;
        padding: 0px !important;
        font-size: 11px !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
        color: #333 !important;
        border-radius: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    
    # 메뉴 리스트
    menus = ["🏠 Home", "⚖️ 마감작업", "💳 카드매입 수기입력건"]
    for m in menus:
        is_selected = (st.session_state.selected_menu == m)
        if st.button(m, key=f"m_btn_{m}", type="primary" if is_selected else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()
    
    st.write("")
    st.divider()
    
    # Memo 섹션
    st.markdown("#### 📝 Memo")
    side_memo = st.text_area(
        "Memo Content", 
        value=st.session_state.daily_memo, 
        height=180, 
        placeholder="메모를 입력하세요...",
        label_visibility="collapsed"
    )
    
    # 저장 버튼 - st.columns를 사용하여 버튼 자체의 가로 점유율을 강제로 줄임
    col1, col2 = st.columns([1, 3]) # 버튼을 왼쪽 1/4 칸에 배치
    with col1:
        st.markdown('<div class="memo-save-area">', unsafe_allow_html=True)
        if st.button("저장", key="memo_save_btn"):
            st.session_state.daily_memo = side_memo
            st.toast("저장완료")
        st.markdown('</div>', unsafe_allow_html=True)

# --- [4. 메인 화면] ---
st.title(st.session_state.selected_menu)
st.divider()

if st.session_state.selected_menu == "🏠 Home":
    st.subheader("⌨️ 차변계정 단축키")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장되었습니다.")
        
elif st.session_state.selected_menu == "⚖️ 마감작업":
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    
elif st.session_state.selected_menu == "💳 카드매입 수기입력건":
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
