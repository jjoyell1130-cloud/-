import streamlit as st
import pandas as pd

# --- [1. 세션 상태 및 설정 통합 관리] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택",
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건 엑셀 변환", 
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
        # 카카오톡 안내문 기본 양식
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

# (데이터 초기화 부분 생략 - 이전과 동일)

# --- [2. 메인 설정 및 사이드바 레이아웃] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.sidebar.title(st.session_state.config["sidebar_title"])

menu_options = [
    st.session_state.config["menu_0"],
    st.session_state.config["menu_1"],
    st.session_state.config["menu_2"]
]

selected_menu = st.sidebar.radio(
    label=st.session_state.config["sidebar_label"],
    options=menu_options,
    index=0
)

# --- [3. 메인 화면 제목 및 부제목] ---
st.title(selected_menu)

if selected_menu == st.session_state.config["menu_0"]:
    subtitle = st.session_state.config["sub_home"]
elif selected_menu == st.session_state.config["menu_1"]:
    subtitle = st.session_state.config["sub_menu1"]
else:
    subtitle = st.session_state.config["sub_menu2"]

st.markdown(f"""<div style="font-size: 14px; line-height: 1.5; color: #555; text-align: left !important; white-space: pre-line;">{subtitle}</div>""", unsafe_allow_html=True)
st.divider()

# --- [4. 메뉴별 기능 상세 구현] ---

if selected_menu == st.session_state.config["menu_1"]:
    # [수정 사항 반영] 제목 수정 및 저장 기능 추가
    with st.expander("💬 카카오톡 전송용 안내문", expanded=True):
        # 텍스트 에리어의 입력값을 변수에 담음
        updated_template = st.text_area(
            "양식 수정", 
            value=st.session_state.config["prompt_template"], 
            height=250
        )
        
        # 저장 버튼 추가
        if st.button("💾 안내문 양식 저장"):
            st.session_state.config["prompt_template"] = updated_template
            st.success("카카오톡 안내문 양식이 성공적으로 저장되었습니다.")
            st.rerun() # 변경사항 즉시 반영을 위해 페이지 재실행

    st.divider()
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)

# (Home 및 카드매입 변환 코드 부분 생략)
