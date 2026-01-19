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
        "menu_1": "⚖️ 매출매입장 PDF & 안내문",
        "menu_2": "💳 카드별 개별 엑셀 변환",
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청: 부가가치세 신고서 접수증, 부가세 신고서 업로드\n위하고: 매출,매입내역 엑셀 변환하여 업로드\n두가지 다 업로드 하면 환급금액 산출되어 안내문이 자동 작성되어요.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하여 변환을 시작하세요.",
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

# [복구] 제공해주신 링크 5개 반영
if 'link_data' not in st.session_state:
    st.session_state.link_data = [
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 상반기 자료", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 하반기 자료", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드자료", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"},
        {"name": "🏠 홈택스", "url": "https://hometax.go.kr/"} 
    ]

# [복구] 차변 계정 단축키 전체 리스트
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"구분": "차량/교통", "주요 거래처": "유류대, 주차장, 하이패스", "분류": "공제유무확인", "계정명": "차량유지비", "코드": "822"},
        {"구분": "여비/출장", "주요 거래처": "편의점, 모텔, 휴게소, 택시", "분류": "공제유무확인", "계정명": "여비교통비", "코드": "812"},
        {"구분": "식대/복리", "주요 거래처": "식당, 카페, 병원, 약국", "분류": "공제유무확인", "계정명": "복리후생비", "코드": "811"},
        {"구분": "구매/비용", "주요 거래처": "다이소, 홈쇼핑, 마트, 아울렛", "분류": "공제유무확인", "계정명": "소모품비", "코드": "830"},
        {"구분": "수수료", "주요 거래처": "캡스, 소프트웨어, 카드알림, 이체수수료", "분류": "공제유무확인", "계정명": "지급수수료", "코드": "831"},
        {"구분": "광고/홍보", "주요 거래처": "네이버광고, 인스타광고", "분류": "공제유무확인", "계정명": "광고선전비", "코드": "833"}
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = ""

# --- [2. 유틸리티 함수] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(re.sub(r'[^0-9.-]', '', str(val))))
    except: return 0

# --- [3. 메인 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# --- [4. 사이드바 및 설정창] ---
st.sidebar.title(st.session_state.config["sidebar_title"])
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(label=st.session_state.config["sidebar_label"], options=menu_options, selection_mode="single", default="🏠 홈 (대시보드)")

with st.sidebar.expander("⚙️ 명칭 수정"):
    st.session_state.config["menu_1"] = st.text_input("메뉴1 명칭", st.session_state.config["menu_1"])
    st.session_state.config["menu_2"] = st.text_input("메뉴2 명칭", st.session_state.config["menu_2"])
    if st.button("설정 저장"): st.rerun()

# --- [5. 메인 화면 레이아웃] ---
st.title(selected_menu)
current_subtitle = st.session_state.config["sub_home"] if selected_menu == "🏠 홈 (대시보드)" else (st.session_state.config["sub_menu1"] if selected_menu == st.session_state.config["menu_1"] else st.session_state.config["sub_menu2"])
st.markdown(f"""<div style="font-size: 14px; line-height: 1.5; color: #555; text-align: left !important; white-space: pre-line;">{current_subtitle}</div>""", unsafe_allow_html=True)
st.divider()

# --- [6. 메뉴별 기능 구현] ---

if selected_menu == "🏠 홈 (대시보드)":
    st.subheader("🔗 바로가기")
    link_cols = st.columns(5)
    for i, item in enumerate(st.session_state.link_data):
        link_cols[i].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()
    
    st.subheader("⌨️ 차변 계정 단축키 관리")
    edited_df = st.data_editor(pd.DataFrame(st.session_state.account_data), num_rows="dynamic", use_container_width=True, key="main_acc_editor")
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("리스트가 저장되었습니다.")
    
    st.divider()
    
    st.subheader("📝 업무 메모")
    st.session_state.memo_content = st.text_area("메모를 입력하세요", value=st.session_state.memo_content, height=200)

elif selected_menu == st.session_state.config["menu_1"]:
    with st.expander("📝 카톡 안내문 양식 편집 (치환 변수 포함)", expanded=True):
        st.session_state.config["prompt_template"] = st.text_area("양식 수정", st.session_state.config["prompt_template"], height=250)
        st.caption("변수: {업체명}, {매출액}, {매입액}, {결과}, {세액}")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1: pdf_files = st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    with c2: xls_files = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
    
    if pdf_files:
        reports = {}
        for f in pdf_files:
            try:
                with pdfplumber.open(f) as pdf:
                    txt = "".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                    name_match = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", txt)
                    biz = name_match.group(1).strip() if name_match else f.name.replace(".pdf","")
                    if biz not in reports: reports[biz] = {"업체명": biz, "매출":0, "매입":0, "세액":0, "결과":"납부"}
                    v_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", txt)
                    if v_match:
                        val = to_int(v_match.group(1))
                        reports[biz]["세액"] = abs(val)
                        reports[biz]["결과"] = "환급" if "환급" in txt or val < 0 else "납부"
            except: pass
        
        if reports:
            st.subheader("📩 생성된 안내문")
            for biz, data in reports.items():
                msg = st.session_state.config["prompt_template"].format(
                    업체명=data['업체명'], 매출액=f"{data['매출']:,}", 매입액=f"{data['매입']:,}", 
                    결과=data['결과'], 세액=f"{data['세액']:,}"
                )
                st.text_area(f"🏢 {biz} 안내문", msg, height=250, key=f"res_{biz}")
                st.divider()

elif selected_menu == st.session_state.config["menu_2"]:
    st.info("카드 변환 메뉴입니다. 엑셀 파일을 업로드해주세요.")
    st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
