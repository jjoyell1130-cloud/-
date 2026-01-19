import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber
from datetime import datetime

# --- [세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택:",
        "main_title": "🚀 세무 업무 통합 대시보드",
        "menu_1": "⚖️ 매출매입장 PDF & 안내문",
        "menu_2": "💳 카드별 개별 엑셀 변환"
    }

if 'link_data' not in st.session_state:
    st.session_state.link_data = [
        {"name": "WEHAGO (위하고)", "url": "https://www.wehago.com/#/main"},
        {"name": "홈택스 (Hometax)", "url": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3"},
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 부가세 상반기", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 부가세 하반기", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드자료 보관함", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

# [중요] 계정 데이터 초기화 (분류 옵션 포함)
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"항목": "유류대", "분류": "공제유무확인", "계정명": "차량유지비", "코드": "822"},
        {"항목": "편의점", "분류": "공제유무확인", "계정명": "여비교통비", "코드": "812"},
        {"항목": "다이소", "분류": "매입", "계정명": "소모품비", "코드": "830"},
        {"항목": "식당", "분류": "공제유무확인", "계정명": "복리후생비", "코드": "811"},
        {"항목": "거래처", "분류": "매입", "계정명": "상품", "코드": "146"},
        {"항목": "캡스/보안", "분류": "매입", "계정명": "지급수수료", "코드": "831"}
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = ""

# --- 기본 설정 ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# 유틸리티 함수
def to_int(val):
    try:
        if pd.isna(val) or val == "": return 0
        return int(float(re.sub(r'[^0-9.-]', '', str(val))))
    except: return 0

def format_date(val):
    try:
        if isinstance(val, (int, float)):
            return pd.to_datetime(val, unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
        dt = pd.to_datetime(str(val), errors='coerce')
        return dt.strftime('%Y-%m-%d') if not pd.isna(dt) else str(val)
    except: return str(val)

# --- 사이드바 메뉴 ---
st.sidebar.title(st.session_state.config["sidebar_title"])
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.radio(st.session_state.config["sidebar_label"], menu_options)

# --- [⚙️ 전체 설정창] ---
with st.expander("⚙️ 시스템 모든 명칭 및 링크 수정하기"):
    st.subheader("1. 제목 및 메뉴명 수정")
    c1, c2 = st.columns(2)
    st.session_state.config["sidebar_title"] = c1.text_input("사이드바 제목", st.session_state.config["sidebar_title"])
    st.session_state.config["main_title"] = c2.text_input("메인 화면 제목", st.session_state.config["main_title"])
    
    st.divider()
    st.subheader("2. 바로가기 버튼 수정")
    for i in range(len(st.session_state.link_data)):
        cb1, cb2 = st.columns([1, 2])
        st.session_state.link_data[i]["name"] = cb1.text_input(f"버튼{i+1} 이름", st.session_state.link_data[i]["name"], key=f"n_{i}")
        st.session_state.link_data[i]["url"] = cb2.text_input(f"버튼{i+1} URL", st.session_state.link_data[i]["url"], key=f"u_{i}")
    
    if st.button("💾 설정 저장 및 새로고침"):
        st.rerun()

# --- [1. 홈 화면] ---
if selected_menu == "🏠 홈 (대시보드)":
    st.title(st.session_state.config["main_title"])
    
    # 바로가기 버튼
    st.subheader("🔗 바로가기")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()

    # --- [여기가 핵심: 분류 선택 기능이 포함된 데이터 에디터] ---
    st.subheader("⌨️ 차변 계정 단축키 및 메모란")
    st.info("💡 '분류' 칸을 클릭하여 [매입, 일반, 공제유무확인] 중 하나를 선택하세요.")
    
    df_accounts = pd.DataFrame(st.session_state.account_data)
    
    # 셀렉트박스 설정
    edited_df = st.data_editor(
        df_accounts,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "분류": st.column_config.SelectboxColumn(
                "분류",
                options=["매입", "일반", "공제유무확인"],
                required=True
            ),
            "코드": st.column_config.TextColumn("코드")
        },
        key="main_account_editor"
    )
    
    if st.button("💾 계정 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장되었습니다!")

    st.divider()
    st.subheader("📝 일반 메모")
    st.session_state.memo_content = st.text_area("메모 입력", value=st.session_state.memo_content, height=100)

# --- [2. 업무 메뉴 1 및 2] (기존 로직 유지) ---
elif selected_menu == st.session_state.config["menu_1"]:
    st.title(st.session_state.config["menu_1"])
    # ... 기존 PDF/엑셀 로직 ...
    st.write("매출매입장 관련 기능을 여기에 구현하세요.")

elif selected_menu == st.session_state.config["menu_2"]:
    st.title(st.session_state.config["menu_2"])
    # ... 기존 카드 변환 로직 ...
    st.write("카드자료 변환 기능을 여기에 구현하세요.")
