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

# --- [추가된 부분: 계정과목 데이터 초기화] ---
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"항목": "유류대", "분류": "공제유무확인", "계정명": "차량유지비", "코드": "822"},
        {"항목": "편의점", "분류": "공제유무확인", "계정명": "여비교통비", "코드": "812"},
        {"항목": "다이소", "분류": "매입", "계정명": "소모품비", "코드": "830"},
        {"항목": "식당", "분류": "공제유무확인", "계정명": "복리후생비", "코드": "811"},
        {"항목": "거래처", "분류": "매입", "계정명": "상품", "코드": "146"},
        {"항목": "홈쇼핑/인터넷", "분류": "매입", "계정명": "소모품비", "코드": "830"},
        {"항목": "주차장/소액세금", "분류": "일반", "계정명": "차량유지비", "코드": "822"},
        {"항목": "휴게소", "분류": "공제유무확인", "계정명": "차량/여비", "코드": ""},
        {"항목": "전기요금", "분류": "매입", "계정명": "전력비", "코드": ""},
        {"항목": "수도요금", "분류": "일반", "계정명": "수도광열비", "코드": ""},
        {"항목": "통신비", "분류": "매입", "계정명": "통신비", "코드": "814"},
        {"항목": "금융결제원", "분류": "일반", "계정명": "세금공과/소모품", "코드": ""},
        {"항목": "약국", "분류": "일반", "계정명": "소모품비", "코드": "830"},
        {"항목": "모텔", "분류": "일반", "계정명": "여비교통비", "코드": "812"},
        {"항목": "캡스/보안", "분류": "매입", "계정명": "지급수수료", "코드": "831"},
        {"항목": "아울렛/작업복", "분류": "매입", "계정명": "소모품비", "코드": "830"},
        {"항목": "컴퓨터 AS", "분류": "매입", "계정명": "수선비", "코드": "820"},
        {"항목": "결제대행업체", "분류": "일반", "계정명": "소모품비", "코드": "830"},
        {"항목": "신용카드알림", "분류": "일반", "계정명": "지급수수료", "코드": "831"},
        {"항목": "휴대폰소액결제", "분류": "일반", "계정명": "소모품비", "코드": "830"},
        {"항목": "병원", "분류": "일반", "계정명": "복리후생비", "코드": "811"},
        {"항목": "로카모빌리티", "분류": "일반", "계정명": "소모품비", "코드": "830"},
        {"항목": "소프트웨어개발", "분류": "매입", "계정명": "지급수수료", "코드": "831"}
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = ""

# --- 기본 설정 ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# 유틸리티 함수 (기존과 동일)
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
st.sidebar.title(st.session_state.config["sidebar_title"])
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.radio(st.session_state.config["sidebar_label"], menu_options)

# --- [⚙️ 전체 설정창] ---
with st.expander("⚙️ 시스템 모든 명칭 및 링크 수정하기"):
    st.subheader("1. 사이드바 및 메인 제목")
    col_s1, col_s2 = st.columns(2)
    new_sidebar_title = col_s1.text_input("사이드바 상단 제목", value=st.session_state.config["sidebar_title"])
    new_sidebar_label = col_s2.text_input("사이드바 라디오 버튼 라벨", value=st.session_state.config["sidebar_label"])
    new_main_title = st.text_input("메인 화면 대시보드 제목", value=st.session_state.config["main_title"])
    
    col_m1, col_m2 = st.columns(2)
    new_menu1 = col_m1.text_input("업무 메뉴 1 이름", value=st.session_state.config["menu_1"])
    new_menu2 = col_m2.text_input("업무 메뉴 2 이름", value=st.session_state.config["menu_2"])
    
    st.divider()
    st.subheader("2. 바로가기 버튼 설정")
    new_link_data = []
    for i in range(len(st.session_state.link_data)):
        c_btn_n, c_btn_u = st.columns([1, 2])
        u_name = c_btn_n.text_input(f"버튼 {i+1} 이름", value=st.session_state.link_data[i]["name"], key=f"btn_edit_n_{i}")
        u_url = c_btn_u.text_input(f"버튼 {i+1} 주소", value=st.session_state.link_data[i]["url"], key=f"btn_edit_u_{i}")
        new_link_data.append({"name": u_name, "url": u_url})
        
    if st.button("💾 모든 설정 적용하기"):
        st.session_state.config["sidebar_title"] = new_sidebar_title
        st.session_state.config["sidebar_label"] = new_sidebar_label
        st.session_state.config["main_title"] = new_main_title
        st.session_state.config["menu_1"] = new_menu1
        st.session_state.config["menu_2"] = new_menu2
        st.session_state.link_data = new_link_data
        st.success("모든 명칭과 링크가 업데이트되었습니다!")
        st.rerun()

# --- [1. 홈 화면] ---
if selected_menu == "🏠 홈 (대시보드)":
    st.title(st.session_state.config["main_title"])
    st.markdown("---")
    
    st.subheader("🔗 바로가기")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()

    # --- [추가 및 수정된 부분: 계정과목 단축키 관리창] ---
    st.subheader("⌨️ 차변 계정 단축키 및 메모란")
    st.info("💡 표의 칸을 클릭하여 내용을 직접 수정할 수 있습니다. (행 추가/삭제 가능)")
    
    # 세션 상태의 데이터를 데이터프레임으로 변환
    df_accounts = pd.DataFrame(st.session_state.account_data)
    
    # 데이터 에디터 생성
    edited_df = st.data_editor(
        df_accounts,
        num_rows="dynamic", # 행 추가/삭제 가능
        use_container_width=True,
        key="account_editor"
    )
    
    # 변경사항 자동 저장 버튼 (또는 세션에 반영)
    if st.button("💾 계정 리스트 변경사항 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("단축키 리스트가 성공적으로 저장되었습니다!")

    st.divider()
    st.subheader("📝 일반 업무 메모")
    st.session_state.memo_content = st.text_area("그 외 기타 메모를 입력하세요 (자동 저장)", value=st.session_state.memo_content, height=150)

# --- [2. 업무 메뉴 1 및 2 로직은 기존과 동일함] ---
# (이하 기존 코드와 동일하여 생략...)
elif selected_menu == st.session_state.config["menu_1"]:
    st.title(st.session_state.config["menu_1"])
    # ... 기존 로직 ...
elif selected_menu == st.session_state.config["menu_2"]:
    st.title(st.session_state.config["menu_2"])
    # ... 기존 로직 ...
