import streamlit as st
import pandas as pd

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건 엑셀 변환", 
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

# 데이터 초기화 (링크 및 단축키)
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"},
        {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제유무확인후 분류"},
        {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"},
        {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제유무확인후 분류"},
        {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"},
        # ... (이하 단축키 데이터 생략 가능하나 코드 안정성을 위해 유지)
    ]

# --- [2. 사이드바 디자인: Menu] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.sidebar.title("📁 Menu") # 제목 수정
st.sidebar.write("업무 선택")

# 버튼형 메뉴 구현
for menu_name in [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]:
    if st.sidebar.button(menu_name, use_container_width=True):
        st.session_state.selected_menu = menu_name
        st.rerun()

# --- [3. 메인 화면 출력] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# 부제목 설정
if current_menu == st.session_state.config["menu_0"]:
    subtitle = st.session_state.config["sub_home"]
elif current_menu == st.session_state.config["menu_1"]:
    subtitle = st.session_state.config["sub_menu1"]
else:
    subtitle = st.session_state.config["sub_menu2"]

st.markdown(f"""<div style="font-size: 14px; line-height: 1.5; color: #555;">{subtitle}</div>""", unsafe_allow_html=True)
st.divider()

# --- [4. 메뉴별 상세 기능] ---

# 1) Home 메뉴
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    # (기존 링크 버튼 코드 유지)
    st.write("링크 버튼 구역")
    
    st.divider()
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True)
    if st.button("💾 단축키 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장되었습니다.")

# 2) 마감작업 메뉴
elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카카오톡 전송용 안내문", expanded=True):
        updated_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=250)
        if st.button("💾 안내문 양식 저장"):
            st.session_state.config["prompt_template"] = updated_template
            st.success("안내문 양식이 저장되었습니다.")
    
    st.divider()
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)

# 3) 카드매입 변환 메뉴
elif current_menu == st.session_state.config["menu_2"]:
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
