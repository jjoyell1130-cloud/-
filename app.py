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
        "menu_2": "💳 카드별 개별 엑셀 변환"
    }

# 기본 데이터 및 메모 초기화 (생략 방지)
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
if 'link_data' not in st.session_state:
    st.session_state.link_data = [
        {"name": "WEHAGO (위하고)", "url": "https://www.wehago.com/#/main"},
        {"name": "홈택스 (Hometax)", "url": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3"},
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"}
    ]

# --- 기본 설정 ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

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

# --- [사이드바 메뉴 디자인 개선] ---
st.sidebar.title(st.session_state.config["sidebar_title"])

# 업무 선택 레이블
st.sidebar.caption(st.session_state.config["sidebar_label"])

# 버튼 스타일의 메뉴 선택 (pills 사용)
menu_options = ["🏠 홈", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
# st.sidebar.pills는 최신 Streamlit 버전에서 지원하는 깔끔한 버튼 메뉴입니다.
selected_menu = st.sidebar.pills(
    label="Menu Navigation", 
    options=menu_options, 
    selection_mode="single", 
    default="🏠 홈",
    label_visibility="collapsed"
)

st.sidebar.divider()

# --- [⚙️ 시스템 설정창] ---
with st.sidebar.expander("⚙️ 명칭/링크 수정"):
    st.session_state.config["main_title"] = st.text_input("메인 제목", st.session_state.config["main_title"])
    st.session_state.config["menu_1"] = st.text_input("메뉴1 명칭", st.session_state.config["menu_1"])
    st.session_state.config["menu_2"] = st.text_input("메뉴2 명칭", st.session_state.config["menu_2"])
    if st.button("설정 반영"):
        st.rerun()

# --- [1. 홈 화면] ---
if selected_menu == "🏠 홈":
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
    if st.button("💾 변경사항 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("단축키 정보가 저장되었습니다.")

    st.divider()
    st.subheader("📝 업무 메모")
    st.session_state.memo_content = st.text_area("내용 입력", value=st.session_state.memo_content, height=150)

# --- [2. 매출매입장 PDF 분석] ---
elif selected_menu == st.session_state.config["menu_1"]:
    st.title(st.session_state.config["menu_1"])
    tax_pdfs = st.file_uploader("1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    excel_ledgers = st.file_uploader("2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
    
    if tax_pdfs:
        final_reports = {}
        for f in tax_pdfs:
            with pdfplumber.open(f) as pdf:
                text = "".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                name_match = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", text)
                biz_name = name_match.group(1).strip() if name_match else f.name.split('_')[0]
                if biz_name not in final_reports: final_reports[biz_name] = {"vat": 0}
                vat_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", text)
                if vat_match:
                    val = to_int(vat_match.group(1))
                    final_reports[biz_name]["vat"] = -val if "환급" in text else val
        
        for name, info in final_reports.items():
            with st.expander(f"📌 {name} 분석 결과"):
                st.metric("예상 세액", f"{info.get('vat', 0):,} 원")

# --- [3. 카드별 엑셀 변환] ---
elif selected_menu == st.session_state.config["menu_2"]:
    st.title(st.session_state.config["menu_2"])
    uploaded_files = st.file_uploader("카드사 엑셀 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    
    if uploaded_files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_files:
                df_raw = pd.read_excel(file, header=None)
                h_idx = 0
                for i in range(min(40, len(df_raw))):
                    row_s = "".join([str(v) for v in df_raw.iloc[i].values])
                    if any(k in row_s for k in ['카드번호', '이용일', '매출일']):
                        h_idx = i; break
                
                file.seek(0)
                df = pd.read_excel(file, header=h_idx)
                df.columns = [str(c).strip() for c in df.columns]
                
                # ... (데이터 가공 로직 동일) ...
                buf = io.BytesIO()
                df.to_excel(buf, index=False)
                zf.writestr(f"converted_{file.name}", buf.getvalue())
        
        st.download_button("📥 변환 완료 파일 다운로드", zip_buffer.getvalue(), "카드데이터.zip")
