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
        "menu_1": "⚖️ 매출매입장 PDF & 안내문",
        "menu_2": "💳 카드별 개별 엑셀 변환",
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하세요.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하여 변환을 시작하세요.",
        # 본문 상단에 표시될 안내문 양식
        "prompt_template": """*2025 리베르떼-하반기 부가세 신고현황☆★{결과}
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

if 'link_data' not in st.session_state:
    st.session_state.link_data = [
        {"name": "WEHAGO (위하고)", "url": "https://www.wehago.com/#/main"},
        {"name": "홈택스 (Hometax)", "url": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3"}
    ]

# --- [2. 유틸리티 함수] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(re.sub(r'[^0-9.-]', '', str(val))))
    except: return 0

# --- [3. 메인 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# --- [4. 사이드바: 메뉴명 및 기본 안내문 수정] ---
st.sidebar.title(st.session_state.config["sidebar_title"])

menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(label=st.session_state.config["sidebar_label"], options=menu_options, selection_mode="single", default="🏠 홈 (대시보드)")

with st.sidebar.expander("⚙️ 메뉴 명칭 수정"):
    st.session_state.config["menu_1"] = st.text_input("메뉴1 이름", st.session_state.config["menu_1"])
    st.session_state.config["menu_2"] = st.text_input("메뉴2 이름", st.session_state.config["menu_2"])
    st.session_state.config["sub_home"] = st.text_area("홈 상단 문구", st.session_state.config["sub_home"])
    st.session_state.config["sub_menu1"] = st.text_area("메뉴1 상단 문구", st.session_state.config["sub_menu1"])
    if st.button("💾 이름 저장"):
        st.rerun()

# --- [5. 메인 화면 출력 및 정렬] ---
st.title(selected_menu)

# 현재 메뉴에 따른 상단 서브타이틀
current_subtitle = st.session_state.config["sub_home"] if selected_menu == "🏠 홈 (대시보드)" else (st.session_state.config["sub_menu1"] if selected_menu == st.session_state.config["menu_1"] else st.session_state.config["sub_menu2"])

st.markdown(f"""<div style="font-size: 14px; line-height: 1.5; color: #555; text-align: left !important; white-space: pre-line;">{current_subtitle}</div>""", unsafe_allow_html=True)
st.divider()

# --- [6. 메뉴별 로직] ---

if selected_menu == "🏠 홈 (대시보드)":
    st.subheader("🔗 바로가기")
    cols = st.columns(2)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 2].link_button(item["name"], item["url"], use_container_width=True)

elif selected_menu == st.session_state.config["menu_1"]:
    # [수정] 안내문 프롬프트 수정란을 본문 상단으로 이동
    with st.expander("📝 카톡 안내문 양식 편집 (치환 변수 포함)", expanded=False):
        st.session_state.config["prompt_template"] = st.text_area(
            "이곳에서 수정하면 아래 결과에 즉시 반영됩니다.", 
            st.session_state.config["prompt_template"], 
            height=250
        )
        st.caption("변수 안내: {매출액}, {매입액}, {결과}, {세액}")
    
    st.divider()
    
    # 파일 업로드 섹션
    c1, c2 = st.columns(2)
    with c1: pdf_files = st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    with c2: xls_files = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
    
    if pdf_files:
        reports = {}
        for f in pdf_files:
            try:
                with pdfplumber.open(f) as pdf:
                    txt = "".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                    name = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", txt)
                    biz = name.group(1).strip() if name else f.name.replace(".pdf","")
                    
                    if biz not in reports: reports[biz] = {"매출":0, "매입":0, "세액":0, "결과":"납부"}
                    
                    v_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", txt)
                    if v_match:
                        val = to_int(v_match.group(1))
                        reports[biz]["세액"] = abs(val)
                        reports[biz]["결과"] = "환급" if "환급" in txt or val < 0 else "납부"
            except: pass
        
        # 분석 결과 및 프롬프트 적용 텍스트 생성
        if reports:
            st.subheader("📩 생성된 안내문")
            for biz, data in reports.items():
                with st.container():
                    st.markdown(f"### 🏢 {biz}")
                    # 본문 상단에서 수정한 템플릿을 사용하여 텍스트 생성
                    generated_msg = st.session_state.config["prompt_template"].format(
                        매출액=f"{data['매출']:,}", 
                        매입액=f"{data['매입']:,}", 
                        결과=data['결과'], 
                        세액=f"{data['세액']:,}"
                    )
                    st.text_area(f"{biz} 전용 안내문 (복사용)", generated_msg, height=250, key=f"res_{biz}")
                    st.divider()

elif selected_menu == st.session_state.config["menu_2"]:
    st.info("카드 변환 메뉴입니다. 엑셀 파일을 업로드해주세요.")
    up_files = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
