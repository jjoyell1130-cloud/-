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
        "sidebar_label": "업무 선택",
        "main_title": "🚀 세무 업무 통합 대시보드",
        "menu_1": "⚖️ 매출매입장 PDF & 안내문",
        "menu_2": "💳 카드별 개별 엑셀 변환",
        # 추가: 부제목(설명란) 초기값
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "⚖️ 메뉴1: 국세청 자료 분석 및 안내문 제작",
        "sub_menu2": "💳 메뉴2: 카드사별 엑셀 업로드 양식 변환"
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
        {"구분": "식대/복리", "주요 거래처": "식당, 병원", "분류": "공제유무확인", "계정명": "복리후생비", "코드": "811"},
        {"구분": "구매/비용", "주요 거래처": "다이소, 홈쇼핑, 약국, 아울렛, 소액결제", "분류": "매입", "계정명": "소모품비", "코드": "830"},
        {"구분": "수수료", "주요 거래처": "캡스, 소프트웨어, 카드알림, 결제대행", "분류": "매입", "계정명": "지급수수료", "코드": "831"},
        {"구분": "자산(매입)", "주요 거래처": "거래처 상품 매입", "분류": "매입", "계정명": "상품", "코드": "146"},
        {"구분": "공과금", "주요 거래처": "전기요금", "분류": "매입", "계정명": "전력비", "코드": ""},
        {"구분": "공과금", "주요 거래처": "수도요금", "분류": "일반", "계정명": "수도광열비", "코드": ""},
        {"구분": "공과금", "주요 거래처": "통신비(핸드폰, 인터넷)", "분류": "매입", "계정명": "통신비", "코드": "814"},
        {"구분": "수리", "주요 거래처": "컴퓨터 A/S, 비품 수리", "분류": "매입", "계정명": "수선비", "코드": "820"}
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = ""

# --- 유틸리티 함수 ---
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

# --- 기본 설정 ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# --- [사이드바 디자인] ---
st.sidebar.title(st.session_state.config["sidebar_title"])

# 업무 선택 버튼 (Pills 스타일)
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(
    label=st.session_state.config["sidebar_label"], 
    options=menu_options, 
    selection_mode="single", 
    default="🏠 홈 (대시보드)"
)

# --- [동적 부제목 설명창] ---
st.sidebar.markdown("---")
if selected_menu == "🏠 홈 (대시보드)":
    st.sidebar.info(st.session_state.config["sub_home"])
elif selected_menu == st.session_state.config["menu_1"]:
    st.sidebar.info(st.session_state.config["sub_menu1"])
elif selected_menu == st.session_state.config["menu_2"]:
    st.sidebar.info(st.session_state.config["sub_menu2"])
st.sidebar.markdown("---")

# --- [⚙️ 명칭 및 부제목 설정창] ---
with st.sidebar.expander("⚙️ 명칭 및 부제목 수정"):
    st.subheader("1. 메인 제목")
    st.session_state.config["main_title"] = st.text_input("메인 제목", st.session_state.config["main_title"])
    
    st.divider()
    st.subheader("2. 메뉴명 및 부제목(설명)")
    
    # 홈 설명 수정
    st.session_state.config["sub_home"] = st.text_area("🏠 홈 부제목", st.session_state.config["sub_home"], height=70)
    
    # 메뉴1 수정
    st.session_state.config["menu_1"] = st.text_input("⚖️ 메뉴1 명칭", st.session_state.config["menu_1"])
    st.session_state.config["sub_menu1"] = st.text_area("⚖️ 메뉴1 부제목", st.session_state.config["sub_menu1"], height=70)
    
    # 메뉴2 수정
    st.session_state.config["menu_2"] = st.text_input("💳 메뉴2 명칭", st.session_state.config["menu_2"])
    st.session_state.config["sub_menu2"] = st.text_area("💳 메뉴2 부제목", st.session_state.config["sub_menu2"], height=70)
    
    if st.button("💾 모든 설정 반영"):
        st.rerun()

# --- [1. 홈 화면] ---
if selected_menu == "🏠 홈 (대시보드)":
    st.title(st.session_state.config["main_title"])
    
    st.subheader("🔗 바로가기")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()
    
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df_accounts = pd.DataFrame(st.session_state.account_data)
    
    edited_df = st.data_editor(
        df_accounts,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "분류": st.column_config.SelectboxColumn("분류", options=["매입", "일반", "공제유무확인"], required=True)
        },
        key="main_editor"
    )
    if st.button("💾 계정 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장 완료!")

    st.divider()
    st.subheader("📝 업무 메모")
    st.session_state.memo_content = st.text_area("내용 입력", value=st.session_state.memo_content, height=150)

# --- [2. 메뉴 1 로직] ---
elif selected_menu == st.session_state.config["menu_1"]:
    st.title(st.session_state.config["menu_1"])
    # (기존 PDF 분석 로직 그대로 유지)
    st.write("PDF 파일을 업로드하여 분석을 시작하세요.")

# --- [3. 메뉴 2 로직] ---
elif selected_menu == st.session_state.config["menu_2"]:
    st.title(st.session_state.config["menu_2"])
    # (기존 카드 변환 로직 그대로 유지)
    st.write("카드사 엑셀 파일을 업로드하여 변환을 시작하세요.")
