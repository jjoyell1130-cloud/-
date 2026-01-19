import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber
from datetime import datetime

# --- [1. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택",
        "main_title": "🚀 세무 업무 통합 대시보드",
        "menu_1": "⚖️ 매출매입장 PDF & 안내문",
        "menu_2": "💳 카드별 개별 엑셀 변환",
        # 기본 안내 메세지 초기값
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청: 부가가치세 신고서 접수증, 부가세 신고서 업로드\n위하고: 매출,매입내역 엑셀 변환하여 업로드\n두가지 다 업로드 하면 환급금액 산출되어 안내문이 자동 작성되어요.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하여 변환을 시작하세요."
    }

if 'link_data' not in st.session_state:
    st.session_state.link_data = [
        {"name": "WEHAGO (위하고)", "url": "https://www.wehago.com/#/main"},
        {"name": "홈택스 (Hometax)", "url": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3"},
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"}
    ]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"구분": "차량/교통", "주요 거래처": "유류대, 주차장, 하이패스", "분류": "공제유무확인", "계정명": "차량유지비", "코드": "822"},
        {"구분": "여비/출장", "주요 거래처": "편의점, 모텔, 휴게소", "분류": "공제유무확인", "계정명": "여비교통비", "코드": "812"},
        {"구분": "식대/복리", "주요 거래처": "식당, 병원", "분류": "공제유무확인", "계정명": "복리후생비", "코드": "811"}
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = ""

# --- [2. 유틸리티 함수] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(re.sub(r'[^0-9.-]', '', str(val))))
    except: return 0

def format_date(val):
    try:
        if isinstance(val, (int, float)):
            return pd.to_datetime(val, unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
        dt = pd.to_datetime(str(val), errors='coerce')
        return dt.strftime('%Y-%m-%d') if not pd.isna(dt) else str(val)
    except: return str(val)

# --- [3. 기본 페이지 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# --- [4. 사이드바 설정 및 수정창] ---
st.sidebar.title(st.session_state.config["sidebar_title"])

menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(
    label=st.session_state.config["sidebar_label"], 
    options=menu_options, 
    selection_mode="single", 
    default="🏠 홈 (대시보드)"
)

# 현재 메뉴 부제목 결정
if selected_menu == "🏠 홈 (대시보드)":
    current_subtitle = st.session_state.config["sub_home"]
elif selected_menu == st.session_state.config["menu_1"]:
    current_subtitle = st.session_state.config["sub_menu1"]
else:
    current_subtitle = st.session_state.config["sub_menu2"]

st.sidebar.markdown("---")
st.sidebar.info(current_subtitle)
st.sidebar.markdown("---")

# ⚙️ 명칭 및 안내문 수정창 (여기에 입력창이 모두 있습니다!)
with st.sidebar.expander("⚙️ 명칭 및 안내문 수정"):
    st.markdown("#### 🏠 홈 설정")
    st.session_state.config["sub_home"] = st.text_area("홈 안내 메세지", st.session_state.config["sub_home"], height=80)
    
    st.divider()
    st.markdown("#### ⚖️ 메뉴 1 설정")
    st.session_state.config["menu_1"] = st.text_input("메뉴 1 이름 수정", st.session_state.config["menu_1"])
    # [핵심] 안내 메세지 입력창 확실히 노출
    st.session_state.config["sub_menu1"] = st.text_area("메뉴 1 안내 메세지 입력", st.session_state.config["sub_menu1"], height=150)
    
    st.divider()
    st.markdown("#### 💳 메뉴 2 설정")
    st.session_state.config["menu_2"] = st.text_input("메뉴 2 이름 수정", st.session_state.config["menu_2"])
    st.session_state.config["sub_menu2"] = st.text_area("메뉴 2 안내 메세지 입력", st.session_state.config["sub_menu2"], height=100)
    
    if st.button("💾 모든 설정 즉시 반영"):
        st.rerun()

# --- [5. 메인 화면 출력] ---

st.title(selected_menu)

# 폰트 정렬 및 사이즈 (14px, 왼쪽 정렬) 적용
st.markdown(
    f"""
    <div style="
        font-size: 14px; 
        line-height: 1.5; 
        color: #555; 
        text-align: left !important; 
        width: 100%; 
        padding: 0px !important;
        margin: 0px !important;
        white-space: pre-line;
    ">
        {current_subtitle}
    </div>
    """, 
    unsafe_allow_html=True
)
st.divider()

# --- [6. 메뉴별 로직] ---

if selected_menu == "🏠 홈 (대시보드)":
    st.subheader("🔗 바로가기")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df_accounts = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_accounts, num_rows="dynamic", use_container_width=True, key="home_editor")
    if st.button("💾 계정 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장됨")

elif selected_menu == st.session_state.config["menu_1"]:
    # 매출매입장 PDF 분석 기능
    tax_pdfs = st.file_uploader("📄 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    if tax_pdfs:
        st.write("분석 중...")

elif selected_menu == st.session_state.config["menu_2"]:
    # 카드 엑셀 변환 기능
    uploaded_files = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
    if uploaded_files:
        st.write("변환 준비 중...")
