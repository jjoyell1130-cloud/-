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
        # 부제목 초기값 설정
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "⚖️ PDF 파일을 업로드하여 분석을 시작하세요.",
        "sub_menu2": "💳 카드사별 엑셀 파일을 업로드하여 변환을 시작하세요."
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
        {"구분": "수수료", "주요 거래처": "캡스, 소프트웨어, 카드알림, 결제대행", "분류": "매입", "계정명": "지급수수료", "코드": "831"}
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

# --- [4. 사이드바 디자인 및 메뉴] ---
st.sidebar.title(st.session_state.config["sidebar_title"])

# 업무 선택 버튼 (Pills 스타일)
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(
    label=st.session_state.config["sidebar_label"], 
    options=menu_options, 
    selection_mode="single", 
    default="🏠 홈 (대시보드)"
)

# 현재 선택된 메뉴에 따른 부제목 결정
current_subtitle = ""
if selected_menu == "🏠 홈 (대시보드)":
    current_subtitle = st.session_state.config["sub_home"]
elif selected_menu == st.session_state.config["menu_1"]:
    current_subtitle = st.session_state.config["sub_menu1"]
elif selected_menu == st.session_state.config["menu_2"]:
    current_subtitle = st.session_state.config["sub_menu2"]

# 사이드바에 부제목 표시
st.sidebar.markdown("---")
st.sidebar.info(current_subtitle)
st.sidebar.markdown("---")

# 설정창 (명칭 및 부제목 수정)
with st.sidebar.expander("⚙️ 명칭 및 부제목 수정"):
    st.session_state.config["main_title"] = st.text_input("메인 화면 제목", st.session_state.config["main_title"])
    st.divider()
    st.session_state.config["sub_home"] = st.text_area("🏠 홈 부제목", st.session_state.config["sub_home"])
    st.divider()
    st.session_state.config["menu_1"] = st.text_input("⚖️ 메뉴1 이름", st.session_state.config["menu_1"])
    st.session_state.config["sub_menu1"] = st.text_area("⚖️ 메뉴1 부제목", st.session_state.config["sub_menu1"])
    st.divider()
    st.session_state.config["menu_2"] = st.text_input("💳 메뉴2 이름", st.session_state.config["menu_2"])
    st.session_state.config["sub_menu2"] = st.text_area("💳 메뉴2 부제목", st.session_state.config["sub_menu2"])
    
    if st.button("💾 설정 반영"):
        st.rerun()

# --- [5. 메인 화면 로직] ---

# 메인 제목 및 연동된 부제목 표시
st.title(selected_menu)
st.markdown(f"#### {current_subtitle}") # 부제목 표시 부분
st.divider()

# --- [메뉴별 기능 구현] ---

if selected_menu == "🏠 홈 (대시보드)":
    # 바로가기 버튼
    st.subheader("🔗 바로가기")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()
    # 단축키 관리 테이블
    st.subheader("⌨️ 차변 계정 단축키 관리")
    df_accounts = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(
        df_accounts, num_rows="dynamic", use_container_width=True,
        column_config={"분류": st.column_config.SelectboxColumn("분류", options=["매입", "일반", "공제유무확인"], required=True)},
        key="main_editor"
    )
    if st.button("💾 계정 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장 완료!")
    
    st.divider()
    st.subheader("📝 업무 메모")
    st.session_state.memo_content = st.text_area("내용 입력", value=st.session_state.memo_content, height=150)

elif selected_menu == st.session_state.config["menu_1"]:
    # --- 매출매입장 PDF 분석 로직 복구 ---
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
        
        if final_reports:
            for name, info in final_reports.items():
                with st.expander(f"📌 {name} 분석 결과"):
                    st.metric("예상 세액", f"{info.get('vat', 0):,} 원")

elif selected_menu == st.session_state.config["menu_2"]:
    # --- 카드별 엑셀 변환 로직 복구 ---
    uploaded_files = st.file_uploader("카드사 엑셀 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    
    if uploaded_files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_files:
                try:
                    df_raw = pd.read_excel(file, header=None)
                    h_idx = 0
                    for i in range(min(40, len(df_raw))):
                        row_s = "".join([str(v) for v in df_raw.iloc[i].values])
                        if any(k in row_s for k in ['카드번호', '이용일', '매출일']):
                            h_idx = i; break
                    
                    file.seek(0)
                    df = pd.read_excel(file, header=h_idx)
                    df.columns = [str(c).strip() for c in df.columns]
                    
                    col_map = {'매출일자': ['이용일', '승인일', '매출일'], '가맹점명': ['가맹점', '이용처'], 
                               '사업자번호': ['사업자', '등록번호'], '매출금액': ['금액', '합계', '이용금액']}
                    
                    tmp = pd.DataFrame()
                    for std, aliases in col_map.items():
                        act = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                        if act: tmp[std] = df[act]
                    
                    if not tmp.empty:
                        tmp['매출일자'] = tmp['매출일자'].apply(format_date)
                        tmp['매출금액'] = tmp['매출금액'].apply(to_int)
                        # 결과 저장
                        buf = io.BytesIO()
                        tmp.to_excel(buf, index=False)
                        zf.writestr(f"converted_{file.name}", buf.getvalue())
                except Exception as e:
                    st.error(f"{file.name} 처리 중 오류 발생: {e}")
        
        if zip_buffer.getvalue():
            st.download_button("📥 변환 완료 파일(ZIP) 다운로드", zip_buffer.getvalue(), "카드자료변환.zip")
