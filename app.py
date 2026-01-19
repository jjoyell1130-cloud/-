import streamlit as st
import pandas as pd
import io

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}
감기 조심하시고 건강이 최고인거 아시죠? ^.<

부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {매출액}원
-매입장: {매입액}원
-접수증 > {결과}: {세액}원

☆★{결과}예정 8월 말 정도

혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!
25일 까지는 수정이 가능합니다!"""
    }

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

# 데이터 초기화 (신고리스트/단축키 데이터 유지)
if 'link_group_2' not in st.session_state:
    st.session_state.link_group_2 = [
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 상반기 자료", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 하반기 자료", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드매입자료", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}, {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제유무확인후 분류"}, {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"}, {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제유무확인후 분류"}]

# --- [2. 가공용 헬퍼 함수] ---
def get_processed_excel(file):
    df = pd.read_excel(file)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- [3. 스타일 설정 (원본 디자인 유지)] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { text-align: left !important; justify-content: flex-start !important; }
    
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; border-radius: 6px; height: 2.2rem; font-size: 14px; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white; color: #444;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    st.write("")
    menu_items = [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
    for m_name in menu_items:
        is_selected = (st.session_state.selected_menu == m_name)
        if st.button(m_name, key=f"m_btn_{m_name}", use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

    # 에러 방지를 위한 공백 처리 (st.text 대신 st.write 사용)
    for _ in range(15):
        st.write("") 
    
    st.divider()
    st.markdown("#### 📝 Memo")
    side_memo = st.text_area("Memo Content", value=st.session_state.daily_memo, height=200, label_visibility="collapsed", key="side_memo_input")
    if st.button("💾 저장", use_container_width=True, key="memo_save_btn"):
        st.session_state.daily_memo = side_memo
        st.success("저장되었습니다.")

# --- [5. 메인 화면] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

if current_menu != st.session_state.config["menu_0"]:
    sub_text = st.session_state.config["sub_menu1"] if current_menu == st.session_state.config["menu_1"] else st.session_state.config["sub_menu2"]
    st.markdown(f"<p style='color: #666; font-size: 15px;'>{sub_text}</p>", unsafe_allow_html=True)
st.divider()

if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    st.write("")
    c3, c4, c5, c6 = st.columns(4)
    links = st.session_state.link_group_2
    with c3: st.link_button(links[0]["name"], links[0]["url"], use_container_width=True)
    with c4: st.link_button(links[1]["name"], links[1]["url"], use_container_width=True)
    with c5: st.link_button(links[2]["name"], links[2]["url"], use_container_width=True)
    with c6: st.link_button(links[3]["name"], links[3]["url"], use_container_width=True)
    st.divider()
    st.subheader("⌨️ 차변계정 단축키")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_editor")
    if st.button("💾 리스트 저장", key="save_acc_list"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("데이터가 저장되었습니다.")

elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=200, key="tmpl_area")
        if st.button("💾 안내문 양식 저장", key="save_tmpl"):
            st.session_state.config["prompt_template"] = u_template
            st.success("저장되었습니다.")
    st.divider()
    pdf_up = st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True, key="pdf_up")
    if pdf_up:
        st.download_button("📥 가공된 PDF 다운로드", data=pdf_up[0].getvalue(), file_name="가공_국세청자료.pdf", use_container_width=True, key="pdf_down")
    
    excel_up = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], key="excel_up")
    if excel_up:
        st.download_button("📥 가공된 매출매입장 다운로드", data=get_processed_excel(excel_up), file_name=f"가공_{excel_up.name}", use_container_width=True, key="excel_down")

elif current_menu == st.session_state.config["menu_2"]:
    card_up = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], key="card_up")
    if card_up:
        st.download_button("📥 위하고 수기입력용 다운로드", data=get_processed_excel(card_up), file_name=f"위하고_{card_up.name}", use_container_width=True, key="card_down")
