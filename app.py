import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber

# --- [1. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택",
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드내역서 엑셀 변환",
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        # [최종 수정] 문장을 더 매끄럽게 다듬어 반영했습니다.
        "sub_menu2": "카드내역 엑셀파일을 업로드하시면 위하고(WEHAGO) 전용 업로드 양식으로 변환됩니다.",
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

# 바로가기 링크 및 단축키 데이터 설정 (이전과 동일)
if 'link_group_1' not in st.session_state:
    st.session_state.link_group_1 = [
        {"name": "WEHAGO (위하고)", "url": "https://www.wehago.com/#/main"},
        {"name": "🏠 홈택스", "url": "https://hometax.go.kr/"}
    ]
if 'link_group_2' not in st.session_state:
    st.session_state.link_group_2 = [
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 상반기 자료", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 하반기 자료", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드매입자료", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"},
        {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제유무확인후 분류"},
        {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"},
        {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제유무확인후 분류"},
        {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"},
        {"단축키": "830", "거래처": "홈쇼핑, 인터넷구매", "계정명": "소모품비", "분류": "매입"},
        {"단축키": "822", "거래처": "주차장, 적은금액세금", "계정명": "차량유지비", "분류": "일반"},
        {"단축키": "-", "거래처": "휴게소", "계정명": "차량/여비교통비", "분류": "공제유무확인후 분류"},
        {"단축키": "-", "거래처": "전기요금", "계정명": "전력비", "분류": "매입"},
        {"단축키": "-", "거래처": "수도요금", "계정명": "수도광열비", "분류": "일반"},
        {"단축키": "814", "거래처": "통신비", "계정명": "통신비", "분류": "매입"},
        {"단축키": "-", "거래처": "금융결제원", "계정명": "세금과공과", "분류": "일반"},
        {"단축키": "830", "거래처": "약국", "계정명": "소모품비", "분류": "일반"},
        {"단축키": "-", "거래처": "모텔", "계정명": "출장비/여비교통비", "분류": "일반"},
        {"단축키": "831", "거래처": "캡스, 보안, 홈페이지", "계정명": "지급수수료", "분류": "매입"},
        {"단축키": "-", "거래처": "아울렛(작업복)", "계정명": "소모품비", "분류": "매입"},
        {"단축키": "820", "거래처": "컴퓨터 AS", "계정명": "수선비", "분류": "매입"},
        {"단축키": "830", "거래처": "결제대행업체", "계정명": "소모품비", "분류": "일반"},
        {"단축키": "-", "거래처": "신용카드 알림", "계정명": "지급수수료", "분류": "일반"},
        {"단축키": "-", "거래처": "휴대폰 소액결제", "계정명": "소모품비", "분류": "일반"},
        {"단축키": "146", "거래처": "매입 항목", "계정명": "상품", "분류": "매입"},
        {"단축키": "-", "거래처": "병원", "계정명": "복리후생비", "분류": "일반"},
        {"단축키": "-", "거래처": "금융결제원", "계정명": "소모품비", "분류": "일반"},
        {"단축키": "-", "거래처": "로카모빌리티", "계정명": "소모품비", "분류": "일반"},
        {"단축키": "831", "거래처": "소프트웨어 개발/공급", "계정명": "지급수수료", "분류": "지급수수료"}
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = ""

# --- [2. 메인 설정 및 레이아웃] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

st.sidebar.title(st.session_state.config["sidebar_title"])
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(label=st.session_state.config["sidebar_label"], options=menu_options, selection_mode="single", default="🏠 홈 (대시보드)")

st.title(selected_menu)
current_subtitle = st.session_state.config["sub_home"] if selected_menu == "🏠 홈 (대시보드)" else (st.session_state.config["sub_menu1"] if selected_menu == st.session_state.config["menu_1"] else st.session_state.config["sub_menu2"])
st.markdown(f"""<div style="font-size: 14px; line-height: 1.5; color: #555; text-align: left !important; white-space: pre-line;">{current_subtitle}</div>""", unsafe_allow_html=True)
st.divider()

# --- [3. 메뉴별 기능 구현] ---

if selected_menu == "🏠 홈 (대시보드)":
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    for i, item in enumerate(st.session_state.link_group_1):
        [c1, c2][i].link_button(item["name"], item["url"], use_container_width=True)
    st.write("")
    c3, c4, c5, c6 = st.columns(4)
    for i, item in enumerate(st.session_state.link_group_2):
        [c3, c4, c5, c6][i].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()
    
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df_acc = pd.DataFrame(st.session_state.account_data)
    df_acc = df_acc[["단축키", "거래처", "계정명", "분류"]]
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_editor_v5")
    
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("단축키 리스트가 성공적으로 업데이트되었습니다.")
    
    st.divider()
    st.subheader("📝 업무 메모")
    st.session_state.memo_content = st.text_area("내용을 입력하세요", value=st.session_state.memo_content, height=200)

elif selected_menu == st.session_state.config["menu_1"]:
    with st.expander("📝 카톡 안내문 양식 편집 (치환 변수 포함)", expanded=True):
        st.session_state.config["prompt_template"] = st.text_area("양식 수정", st.session_state.config["prompt_template"], height=250)
    st.divider()
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)

elif selected_menu == st.session_state.config["menu_2"]:
    # 정정된 안내 문구가 표시되는 구역
    st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
