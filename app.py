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

# [데이터 입력] 요청하신 모든 계정과목 데이터 포함
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
        {"구분": "수리", "주요 거래처": "컴퓨터 A/S, 비품 수리", "분류": "매입", "계정명": "수선비", "코드": "820"},
        {"구분": "기타", "주요 거래처": "금융결제원", "분류": "일반", "계정명": "세금공과금", "코드": ""},
        {"구분": "기타", "주요 거래처": "로카모빌리티", "분류": "일반", "계정명": "소모품비", "코드": "830"},
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = ""

# --- 기본 설정 ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# --- 사이드바 메뉴 ---
st.sidebar.title(st.session_state.config["sidebar_title"])
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.radio(st.session_state.config["sidebar_label"], menu_options)

# --- [1. 홈 화면] ---
if selected_menu == "🏠 홈 (대시보드)":
    st.title(st.session_state.config["main_title"])
    
    # 바로가기 버튼 섹션
    st.subheader("🔗 바로가기")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()

    # --- [계정과목 단축키 관리창] ---
    st.subheader("⌨️ 차변 계정 단축키 관리")
    st.info("💡 '분류' 열을 클릭하여 매입/일반/공제유무확인을 선택할 수 있습니다.")
    
    df_accounts = pd.DataFrame(st.session_state.account_data)
    
    # 데이터 에디터 설정
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
            "코드": st.column_config.TextColumn("코드", width="small"),
            "구분": st.column_config.TextColumn("구분", width="medium"),
            "주요 거래처": st.column_config.TextColumn("주요 거래처", width="large")
        },
        key="main_account_editor"
    )
    
    if st.button("💾 계정 리스트 변경사항 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("단축키 리스트가 안전하게 저장되었습니다!")

    st.divider()
    st.subheader("📝 업무 메모")
    st.session_state.memo_content = st.text_area("내용을 입력하세요", value=st.session_state.memo_content, height=150)

# --- [2. 업무 메뉴 1 & 2] ---
# (이하 기존의 PDF 분석 및 엑셀 변환 로직을 그대로 유지하시면 됩니다.)
elif selected_menu == st.session_state.config["menu_1"]:
    st.title(st.session_state.config["menu_1"])
    st.info("매출매입장 분석 기능을 실행합니다.")
    # ... 기존 코드 ...

elif selected_menu == st.session_state.config["menu_2"]:
    st.title(st.session_state.config["menu_2"])
    st.info("카드자료 변환 기능을 실행합니다.")
    # ... 기존 코드 ...
