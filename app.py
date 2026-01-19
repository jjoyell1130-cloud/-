import streamlit as st
import pandas as pd

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건", # 제목 수정
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
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

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

# 데이터 복구 (링크 및 단축키)
if 'link_group_2' not in st.session_state:
    st.session_state.link_group_2 = [
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 상반기 자료", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 하반기 자료", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드매입자료", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}, {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제유무확인후 분류"}, {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"}, {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제유무확인후 분류"}, {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"}, {"단축키": "830", "거래처": "홈쇼핑, 인터넷구매", "계정명": "소모품비", "분류": "매입"}, {"단축키": "822", "거래처": "주차장, 적은금액세금", "계정명": "차량유지비", "분류": "일반"}, {"단축키": "-", "거래처": "휴게소", "계정명": "차량/여비교통비", "분류": "공제유무확인후 분류"}, {"단축키": "-", "거래처": "전기요금", "계정명": "전력비", "분류": "매입"}, {"단축키": "-", "거래처": "수도요금", "계정명": "수도광열비", "분류": "일반"}, {"단축키": "814", "거래처": "통신비", "계정명": "통신비", "분류": "매입"}, {"단축키": "-", "거래처": "금융결제원", "계정명": "세금과공과", "분류": "일반"}, {"단축키": "830", "거래처": "약국", "계정명": "소모품비", "분류": "일반"}, {"단축키": "-", "거래처": "모텔", "계정명": "출장비/여비교통비", "분류": "일반"}, {"단축키": "831", "거래처": "캡스, 보안, 홈페이지", "계정명": "지급수수료", "분류": "매입"}, {"단축키": "-", "거래처": "아울렛(작업복)", "계정명": "소모품비", "분류": "매입"}, {"단축키": "820", "거래처": "컴퓨터 AS", "계정명": "수선비", "분류": "매입"}, {"단축키": "830", "거래처": "결제대행업체", "계정명": "소모품비", "분류": "일반"}, {"단축키": "-", "거래처": "신용카드 알림", "계정명": "지급수수료", "분류": "일반"}, {"단축키": "-", "거래처": "휴대폰 소액결제", "계정명": "소모품비", "분류": "일반"}, {"단축키": "146", "거래처": "매입 항목", "계정명": "상품", "분류": "매입"}, {"단축키": "-", "거래처": "병원", "계정명": "복리후생비", "분류": "일반"}, {"단축키": "-", "거래처": "금융결제원", "계정명": "소모품비", "분류": "일반"}, {"단축키": "-", "거래처": "로카모빌리티", "계정명": "소모품비", "분류": "일반"}, {"단축키": "831", "거래처": "소프트웨어 개발/공급", "계정명": "지급수수료", "분류": "지급수수료"}]

# --- [2. 스타일 및 사이드바 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# 왼쪽 정렬 및 버튼 디자인 커스텀 CSS
st.markdown("""
    <style>
    /* 전체 왼쪽 정렬 */
    .main .block-container { padding-top: 2rem; max-width: 95%; margin-left: 0 !important; margin-right: auto !important; text-align: left !important; }
    h1, h2, h3, p, div { text-align: left !important; }
    
    /* 버튼 디자인 (더 세련된 탭 스타일) */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        background-color: white;
        color: #333;
        height: 3.5rem;
        font-weight: 500;
        text-align: left !important;
        padding-left: 20px !important;
        transition: all 0.3s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    div.stButton > button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
        background-color: #fffafa;
    }
    /* 선택된 메뉴 강조 (현재 메뉴와 버튼 텍스트가 같을 때 색상 변경) */
    </style>
    """, unsafe_allow_html=True)

st.sidebar.markdown("### 📁 Menu")
st.sidebar.caption("원하시는 업무를 선택하세요")
st.sidebar.write("")

# 버튼형 메뉴 (선택된 메뉴는 화살표 표시)
for m_id, m_name in [("0", st.session_state.config["menu_0"]), ("1", st.session_state.config["menu_1"]), ("2", st.session_state.config["menu_2"])]:
    display_name = f"➔ {m_name}" if st.session_state.selected_menu == m_name else m_name
    if st.sidebar.button(display_name, key=f"btn_{m_id}", use_container_width=True):
        st.session_state.selected_menu = m_name
        st.rerun()

# --- [3. 메인 화면 출력] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# 부제목 설정 (왼쪽 정렬 보강)
subtitles = {
    st.session_state.config["menu_0"]: st.session_state.config["sub_home"],
    st.session_state.config["menu_1"]: st.session_state.config["sub_menu1"],
    st.session_state.config["menu_2"]: st.session_state.config["sub_menu2"]
}
st.markdown(f"<p style='font-size: 15px; color: #666; margin-bottom: 25px;'>{subtitles[current_menu]}</p>", unsafe_allow_html=True)
st.divider()

# --- [4. 메뉴별 상세 기능] ---

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
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="editor_v3")
    if st.button("💾 리스트 저장", key="save_acc"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("단축키가 저장되었습니다.")

elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카카오톡 전송용 안내문", expanded=True):
        updated_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=280)
        if st.button("💾 안내문 양식 저장", key="save_msg"):
            st.session_state.config["prompt_template"] = updated_template
            st.success("양식이 저장되었습니다.")
    st.divider()
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)

elif current_menu == st.session_state.config["menu_2"]:
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
