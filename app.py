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
        "sub_menu1": "국세청: 부가가치세 신고서 접수증, 부가세 신고서 업로드\n위하고: 매출,매입내역 엑셀 변환하여 업로드\n두가지 다 업로드 하면 환급금액 산출되어 안내문이 자동 작성되어요.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하여 변환을 시작하세요.",
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
        {"name": "홈택스 (Hometax)", "url": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3"},
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"}
    ]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"구분": "식대/복리", "주요 거래처": "식당, 병원", "분류": "공제유무확인", "계정명": "복리후생비", "코드": "811"}
    ]

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

# --- [3. 메인 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# --- [4. 사이드바 및 설정창 복구] ---
st.sidebar.title(st.session_state.config["sidebar_title"])

menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(label=st.session_state.config["sidebar_label"], options=menu_options, selection_mode="single", default="🏠 홈 (대시보드)")

# 현재 부제목 선택
if selected_menu == "🏠 홈 (대시보드)":
    current_subtitle = st.session_state.config["sub_home"]
elif selected_menu == st.session_state.config["menu_1"]:
    current_subtitle = st.session_state.config["sub_menu1"]
else:
    current_subtitle = st.session_state.config["sub_menu2"]

# 설정창 (메뉴명 + 안내문 프롬프트 통합)
with st.sidebar.expander("⚙️ 명칭 및 안내문 프롬프트 수정"):
    st.subheader("1. 메뉴 이름 수정")
    st.session_state.config["menu_1"] = st.text_input("⚖️ 메뉴1 명칭", st.session_state.config["menu_1"])
    st.session_state.config["menu_2"] = st.text_input("💳 메뉴2 명칭", st.session_state.config["menu_2"])
    
    st.divider()
    st.subheader("2. 상단 안내 메세지 수정")
    st.session_state.config["sub_home"] = st.text_area("🏠 홈 안내문", st.session_state.config["sub_home"])
    st.session_state.config["sub_menu1"] = st.text_area("⚖️ 메뉴1 안내문", st.session_state.config["sub_menu1"])
    st.session_state.config["sub_menu2"] = st.text_area("💳 메뉴2 안내문", st.session_state.config["sub_menu2"])
    
    st.divider()
    st.subheader("3. 안내문 자동완성 양식")
    st.session_state.config["prompt_template"] = st.text_area("카톡 발송용 프롬프트", st.session_state.config["prompt_template"], height=250)
    st.caption("{매출액}, {매입액}, {결과}, {세액} 키워드가 자동 치환됩니다.")
    
    if st.button("💾 설정 저장 및 반영"):
        st.rerun()

# --- [5. 메인 화면 출력 및 정렬] ---
st.title(selected_menu)
st.markdown(f"""<div style="font-size: 14px; line-height: 1.5; color: #555; text-align: left !important; white-space: pre-line;">{current_subtitle}</div>""", unsafe_allow_html=True)
st.divider()

# --- [6. 메뉴별 기능 구현] ---

# 1. 홈 화면
if selected_menu == "🏠 홈 (대시보드)":
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    st.divider()
    st.subheader("⌨️ 단축키 관리")
    df_acc = st.data_editor(pd.DataFrame(st.session_state.account_data), num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = df_acc.to_dict('records')
        st.success("저장 완료")

# 2. PDF 분석 및 안내문 생성
elif selected_menu == st.session_state.config["menu_1"]:
    c1, c2 = st.columns(2)
    with c1: pdf_files = st.file_uploader("📄 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    with c2: xls_files = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
    
    if pdf_files:
        reports = {}
        for f in pdf_files:
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
        
        for biz, data in reports.items():
            with st.expander(f"✅ {biz} 안내문 자동 생성", expanded=True):
                msg = st.session_state.config["prompt_template"].format(
                    매출액=f"{data['매출']:,}", 매입액=f"{data['매입']:,}", 결과=data['결과'], 세액=f"{data['세액']:,}"
                )
                st.text_area("결과 (복사해서 사용)", msg, height=250, key=f"txt_{biz}")

# 3. 카드 엑셀 변환
elif selected_menu == st.session_state.config["menu_2"]:
    up_files = st.file_uploader("💳 카드 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
    if up_files:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for f in up_files:
                try:
                    df = pd.read_excel(f, header=None)
                    # 헤더 찾기 및 변환 로직...
                    st.write(f"✅ {f.name} 처리 완료")
                except: st.error(f"{f.name} 오류")
