import streamlit as st
import pandas as pd

# --- [1. 세션 상태 및 설정] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택",
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건 엑셀 변환", 
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
        "prompt_template": """...""" 
    }

# (데이터 초기화 및 링크 설정 부분 생략 - 이전과 동일)

# --- [2. 메인 설정 및 레이아웃] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.sidebar.title(st.session_state.config["sidebar_title"])
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(label=st.session_state.config["sidebar_label"], options=menu_options, selection_mode="single", default="🏠 홈 (대시보드)")

st.title(selected_menu)

# 이 코드가 상단에 부제목을 출력합니다.
current_subtitle = st.session_state.config["sub_home"] if selected_menu == "🏠 홈 (대시보드)" else (st.session_state.config["sub_menu1"] if selected_menu == st.session_state.config["menu_1"] else st.session_state.config["sub_menu2"])
st.markdown(f"""<div style="font-size: 14px; line-height: 1.5; color: #555; text-align: left !important; white-space: pre-line;">{current_subtitle}</div>""", unsafe_allow_html=True)
st.divider()

# --- [3. 메뉴별 기능 구현] ---

if selected_menu == "🏠 홈 (대시보드)":
    # (홈 대시보드 내용 생략)
    pass

elif selected_menu == st.session_state.config["menu_1"]:
    # (마감작업 내용 생략)
    pass

elif selected_menu == st.session_state.config["menu_2"]:
    # [수정 완료] 중복되는 st.info를 삭제하여 상단 부제목만 남겼습니다.
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
