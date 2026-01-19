import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# --- [관리자 설정] 링크 ---
QUICK_LINKS = {
    "WEHAGO (위하고)": "https://www.wehago.com/#/main",
    "홈택스 (Hometax)": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3",
    "📊 신고리스트 (구글시트)": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true",
    "📁 부가세 상반기 자료": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3",
    "📁 부가세 하반기 자료": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0",
    "💳 카드자료 보관함": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"
}

# --- 기본 설정 ---
st.set_page_config(page_title="세무비서 통합 시스템", layout="wide")

# 폰트 로드 (PDF 생성용)
def get_font():
    # 기본 폰트 설정 (시스템 환경에 따라 조정)
    return "Helvetica"

# 유틸리티 함수
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
st.sidebar.title("🗂️ 업무 메뉴")
menu = st.sidebar.radio("원하는 업무를 선택하세요:", ["🏠 홈 (대시보드)", "⚖️ 매출매입장 PDF & 안내문", "💳 카드별 개별 엑셀 변환"])

# --- [1. 홈 화면] ---
if menu == "🏠 홈 (대시보드)":
    st.title("🚀 세무 업무 통합 대시보드")
    st.subheader("🔗 바로가기")
    cols = st.columns(3)
    for i, (name, url) in enumerate(QUICK_LINKS.items()):
        cols[i % 3].link_button(name, url, use_container_width=True)
    st.divider()
    st.info("왼쪽 메뉴에서 업무를 선택하면 자동화 도구가 실행됩니다.")

# --- [2. 매출매입장 & 안내문] ---
elif menu == "⚖️ 매출매입장 PDF & 안내문":
    st.title("⚖️ 매출매입장 PDF 분석 및 안내문")
    
    c1, c2 = st.columns(2)
    with c1:
        tax_pdfs = st.file_uploader("1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    with c2:
        excel_ledgers = st.file_uploader("2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)

    final_reports = {}
    
    if tax_pdfs:
        for f in tax_pdfs:
            with pdfplumber.open(f) as pdf:
                text = "".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                # 상호 및 세액 추출 로직
                name_match = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", text)
                biz_name = name_match.group(1).strip() if name_match else f.name.split('_')[0]
                if biz_name not in final_reports: final_reports[biz_name] = {"vat": 0}
                vat_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", text)
                if vat_match:
                    val = to_int(vat_match.group(1))
                    final_reports[biz_name]["vat"] = -val if "환급" in text else val

    if excel_ledgers:
        for ex in excel_ledgers:
            df = pd.read_excel(ex)
            biz_name = ex.name.split('_')[0]
            if biz_name not in final_reports: final_reports[biz_name] = {"vat": 0}
            # 매출/매입 합계 (간이 로직)
            try:
                s_sum = to_int(df[df['구분'].astype(str).str.contains('매출', na=False)]['합계'].sum())
                b_sum = to_int(df[df['구분'].astype(str).str.contains('매입', na=False)]['합계'].sum())
                final_reports[biz_name].update({"sales": s_sum, "buys": b_sum})
            except: pass

    if final_reports:
        for name, info in final_reports.items():
            with st.expander(f"📌 {name} 안내문구 보기", expanded=True):
                vat = info.get('vat', 0)
                status = "납부하실 세액" if vat >= 0 else "환급받으실 세액"
                msg = f"안녕하세요, {name} 대표님! 😊\n\n✅ 매출 합계: {info.get('sales', 0):,}원\n✅ 매입 합계: {info.get('buys', 0):,}원\n💰 최종 {status}: {abs(vat):,}원"
                st.text_area("카톡 복사용", msg, height=150)

# --- [3. 카드별 개별 엑셀 변환] ---
elif menu == "💳 카드별 개별 엑셀 변환":
    st.title("💳 카드매입 개별 분리 변환")
    uploaded_files = st.file_uploader("파일 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    
    if uploaded_files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_files:
                # 메타정보 (연도, 업체명, 카드사)
                fname = file.name
                year = datetime.now().strftime('%Y')
                company = "업체명"
                brand = "카드"
                
                m = re.search(r'(\d{4})\s*([가-힣\w\s]+?)-', fname)
                if m: year, company = m.group(1), m.group(2).strip()
                if '국민' in fname: brand = "국민"
                elif '비씨' in fname or 'BC' in fname: brand = "비씨"
                
                # 데이터 처리
                df_raw = pd.read_excel(file, header=None)
                h_idx = 0
                for i in range(min(40, len(df_raw))):
                    row_s = "".join([str(v) for v in df_raw.iloc[i].values])
                    if any(k in row_s for k in ['카드번호', '이용일', '매출일']):
                        h_idx = i; break
                
                file.seek(0)
                df = pd.read_excel(file, header=h_idx)
                df.columns = [str(c).strip() for c in df.columns]
                
                # 컬럼 매핑
                col_map = {'매출일자': ['이용일', '승인일', '매출일'], '카드번호': ['카드번호', '카드명'], 
                           '가맹점명': ['가맹점', '이용처'], '사업자번호': ['사업자', '등록번호'], '매출금액': ['금액', '합계', '이용금액']}
                
                tmp = pd.DataFrame()
                for std, aliases in col_map.items():
                    act = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    tmp[std] = df[act] if act else ""
                
                tmp['매출일자'] = tmp['매출일자'].apply(format_date)
                tmp['매출금액'] = tmp['매출금액'].apply(to_int)
                tmp = tmp[tmp['매출금액'] > 0].copy()
                tmp['공급가액'] = (tmp['매출금액'] / 1.1).round(0).astype(int)
                tmp['부가세'] = tmp['매출금액'] - tmp['공급가액']
                
                # 카드별 분리 저장
                tmp['C_ID'] = tmp['카드번호'].astype(str).apply(lambda x: re.sub(r'\D', '', x)[-4:] if len(re.sub(r'\D', '', x)) >= 4 else "0000")
                for cid in tmp['C_ID'].unique():
                    f_df = tmp[tmp['C_ID'] == cid][['카드번호', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                    new_name = f"{year} {company}-카드사용내역({brand}{cid})(업로드용).xlsx"
                    buf = io.BytesIO()
                    f_df.to_excel(buf, index=False)
                    zf.writestr(new_name, buf.getvalue())
        
        st.download_button("📥 카드별 분리 파일(ZIP) 다운로드", zip_buffer.getvalue(), "카드정제.zip", use_container_width=True)
