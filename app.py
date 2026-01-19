import streamlit as st
import pandas as pd
import io
import re
import zipfile
from datetime import datetime

# --- [관리자 설정] 링크 수정은 여기서 하세요 ---
QUICK_LINKS = {
    "WEHAGO (위하고)": "https://www.wehago.com/#/main",
    "홈택스 (Hometax)": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3",
    "📊 신고리스트 (구글시트)": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true",
    "📁 부가세 상반기 자료": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3",
    "📁 부가세 하반기 자료": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0",
    "💳 카드자료 보관함": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"
}

# --- 기본 설정 및 유틸리티 ---
st.set_page_config(page_title="세무비서 통합 대시보드", layout="wide")

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
st.sidebar.title("🗂️ 세무 업무 메뉴")
menu = st.sidebar.radio(
    "수행할 업무를 선택하세요:",
    ["🏠 홈 (업무 바로가기)", "⚖️ 매출매입장 PDF & 안내문", "💳 카드별 개별 엑셀 변환"]
)

# --- [홈 화면] 바로가기 링크 중심 ---
if menu == "🏠 홈 (업무 바로가기)":
    st.title("🚀 세무비서 통합 대시보드")
    st.markdown("---")
    
    # 1. 자주 쓰는 사이트 바로가기 (버튼 형태)
    st.subheader("🔗 주요 업무 바로가기")
    link_cols = st.columns(3)
    
    # 링크 리스트를 순회하며 버튼 생성
    for i, (name, url) in enumerate(QUICK_LINKS.items()):
        col_idx = i % 3
        with link_cols[col_idx]:
            st.link_button(name, url, use_container_width=True)
            
    st.markdown("---")
    
    # 2. 기능 설명
    st.subheader("🛠️ 제공 기능")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.info("#### ⚖️ 매출매입장 PDF & 안내문\n국세청 PDF와 엑셀 장부를 대조하여 대표님용 카톡 안내문을 만듭니다.")
    with col_f2:
        st.success("#### 💳 카드별 개별 엑셀 변환\n카드사 통합 엑셀을 번호별로 쪼개고 업로드용 파일명으로 자동 변환합니다.")

# --- [메뉴 1] 매출매입장 로직 (생략 - 기존 로직 유지) ---
elif menu == "⚖️ 매출매입장 PDF & 안내문":
    st.title("⚖️ 매출매입장 PDF & 안내문 생성")
    # ... (기존 코드와 동일)

# --- [메뉴 2] 카드별 개별 엑셀 변환 로직 (파일명/날짜 간소화 포함) ---
elif menu == "💳 카드별 개별 엑셀 변환":
    st.title("💳 카드매입 수기 입력건 (자동분리)")
    # ... (기존 코드와 동일하되 파일명 규칙 및 날짜 간소화 로직 적용)
    uploaded_cards = st.file_uploader("카드사 엑셀 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    
    if uploaded_cards:
        # (기존의 카드 분리 및 저장 로직 수행)
        st.success("파일 분석 및 변환 준비 완료!")
