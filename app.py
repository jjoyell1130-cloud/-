import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber
from datetime import datetime

# --- [세션 상태 초기화] 데이터 유지 ---
if 'menu_names' not in st.session_state:
    st.session_state.menu_names = {"menu_1": "⚖️ 매출매입장 PDF & 안내문", "menu_2": "💳 카드별 개별 엑셀 변환"}

if 'link_data' not in st.session_state:
    st.session_state.link_data = [
        {"name": "WEHAGO (위하고)", "url": "https://www.wehago.com/#/main"},
        {"name": "홈택스 (Hometax)", "url": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3"},
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 부가세 상반기", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 부가세 하반기", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드자료 보관함", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = "여기에 업무 메모를 입력하세요 (예: 소울인테리어 9014 카드 누락 확인 필요)"

# --- 기본 설정 ---
st.set_page_config(page_title="세무비서 통합 시스템", layout="wide")

# 유틸리티 함수들 (to_int, format_date 생략 - 이전과 동일)
def to_int(val):
    try:
        if pd.isna(val): return 0
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
st.sidebar.title("🗂️ 업무 메뉴")
menu_options = ["🏠 홈 (대시보드)", st.session_state.menu_names["menu_1"], st.session_state.menu_names["menu_2"]]
selected_menu = st.sidebar.radio("업무 선택:", menu_options)

# --- [설정창] ---
with st.expander("⚙️ 전체 이름 및 링크 주소 수정하기"):
    new_m1 = st.text_input("메뉴 1 이름", value=st.session_state.menu_names["menu_1"])
    new_m2 = st.text_input("메뉴 2 이름", value=st.session_state.menu_names["menu_2"])
    st.divider()
    new_link_data = []
    for i in range(len(st.session_state.link_data)):
        col_n, col_u = st.columns([1, 2])
        u_name = col_n.text_input(f"버튼 {i+1} 이름", value=st.session_state.link_data[i]["name"], key=f"n_{i}")
        u_url = col_u.text_input(f"버튼 {i+1} 주소", value=st.session_state.link_data[i]["url"], key=f"u_{i}")
        new_link_data.append({"name": u_name, "url": u_url})
    if st.button("💾 모든 설정 저장"):
        st.session_state.menu_names["menu_1"], st.session_state.menu_names["menu_2"] = new_m1, new_m2
        st.session_state.link_data = new_link_data
        st.rerun()

# --- [1. 홈 화면] ---
if selected_menu == "🏠 홈 (대시보드)":
    st.title("🚀 세무 업무 통합 대시보드")
    
    # 🔗 바로가기 섹션
    st.subheader("🔗 업무 바로가기")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()

    # 📝 메모 섹션 (추가됨)
    st.subheader("📝 오늘 업무 메모")
    memo_input = st.text_area("중요한 사항이나 To-Do 리스트를 기록하세요.", 
                              value=st.session_state.memo_content, 
                              height=200, 
                              help="입력한 내용은 다른 메뉴로 이동해도 유지됩니다.")
    st.session_state.memo_content = memo_input # 실시간 저장
    
    st.caption("※ 메모는 브라우저를 완전히 닫으면 초기화될 수 있습니다. 중요한 내용은 별도로 저장하세요.")

# --- [2. 메뉴 1 로직] ---
elif selected_menu == st.session_state.menu_names["menu_1"]:
    st.title(st.session_state.menu_names["menu_1"])
    # (매출매입장 파일 업로드 및 분석 로직...)
    tax_pdfs = st.file_uploader("1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    excel_ledgers = st.file_uploader("2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
    # [이전과 동일한 분석 로직...]

# --- [3. 메뉴 2 로직] ---
elif selected_menu == st.session_state.menu_names["menu_2"]:
    st.title(st.session_state.menu_names["menu_2"])
    # (카드 분리 로직...)
    uploaded_files = st.file_uploader("카드 엑셀 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    # [이전과 동일한 분리 로직...]
