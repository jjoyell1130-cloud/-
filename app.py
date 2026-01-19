import streamlit as st
import pandas as pd

# --- [1. 세션 상태 및 설정] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택",
        "menu_0": "🏠 Home", # 메뉴명 수정
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건 엑셀 변환", 
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
    }

# 데이터 초기화 (링크 및 단축키 데이터는 기존과 동일하게 유지됨)
# ... (생략)

# --- [2. 메인 설정 및 사이드바 레이아웃] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# 사이드바 제목
st.sidebar.title(st.session_state.config["sidebar_title"])

# [수정] 한 줄씩 나열되도록 리스트 구성
menu_list = [
    st.session_state.config["menu_0"],
    st.session_state.config["menu_1"],
    st.session_state.config["menu_2"]
]

# [중요] pills 대신 radio를 사용하거나 스타일을 지정하여 한 줄에 하나씩 배치
selected_menu = st.sidebar.radio(
    label=st.session_state.config["sidebar_label"],
    options=menu_list,
    index=0
)

# --- [3. 메인 화면 출력] ---
st.title(selected_menu)

# 메뉴별 부제목 매칭
if selected_menu == st.session_state.config["menu_0"]:
    subtitle = st.session_state.config["sub_home"]
elif selected_menu == st.session_state.config["menu_1"]:
    subtitle = st.session_state.config["sub_menu1"]
else:
    subtitle = st.session_state.config["sub_menu2"]

st.markdown(f"""<div style="font-size: 14px; line-height: 1.5; color: #555; text-align: left !important; white-space: pre-line;">{subtitle}</div>""", unsafe_allow_html=True)
st.divider()

# --- [4. 메뉴별 상세 기능 구현] ---

if selected_menu == st.session_state.config["menu_0"]:
    # 홈 대시보드 기능 (바로가기 링크, 단축키 관리 표 등)
    st.subheader("🔗 바로가기")
    # ... (기존 홈 코드 유지)

elif selected_menu == st.session_state.config["menu_1"]:
    # 마감작업 기능
    # ... (기존 마감작업 코드 유지)

elif selected_menu == st.session_state.config["menu_2"]:
    # 카드매입 수기입력건 엑셀 변환 기능
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
