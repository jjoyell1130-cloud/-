import streamlit as st
import pdfplumber
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import io
import urllib.request
import zipfile
import re

# --- 1. 환경 설정 및 폰트 로드 ---
def load_font():
    font_path = "nanum.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except: return False
    try:
        pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        return True
    except: return False

font_status = load_font()
f_name = 'NanumGothic' if font_status else 'Helvetica'

# --- 2. 공통 유틸리티 함수 ---
def to_int(val):
    try:
        if not val: return 0
        clean_val = re.sub(r'[^0-9-]', '', str(val))
        return int(clean_val) if clean_val else 0
    except: return 0

def find_header_and_read(file):
    keywords = ['일자', '가맹점', '금액', '사업자', '승인', '구분']
    df_temp = pd.read_excel(file, header=None)
    header_row = 0
    max_matches = 0
    for i in range(min(20, len(df_temp))):
        row_values = [str(val) for val in df_temp.iloc[i].values]
        matches = sum(1 for word in keywords if any(word in val for val in row_values))
        if matches > max_matches:
            max_matches = matches
            header_row = i
    file.seek(0)
    df = pd.read_excel(file, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def make_pdf_buffer(data, title, date_range, company_name):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    rows_per_page = 26
    actual_item_count = 0 
    for i in range(len(data)):
        if i % rows_per_page == 0:
            if i > 0: c.showPage()
            c.setFont(f_name, 20); c.drawCentredString(width/2, height - 60, title)
            c.setFont(f_name, 10); c.drawString(50, height - 90, f"회사명 : {company_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            yh = 680; c.setLineWidth(1.5); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(f_name, 9); c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자"); c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        row = data.iloc[i]; cur_y = y_start - ((i % rows_per_page) * 23); actual_item_count += 1
        c.setFont(f_name, 8.5)
        c.drawString(45, cur_y, str(actual_item_count))
        c.drawString(85, cur_y, str(row.get('전표일자', ''))[:10])
        c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
    c.save(); buffer.seek(0)
    return buffer

# --- 3. 메뉴 구성 및 화면 로직 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")
menu = st.sidebar.selectbox("📂 업무 선택", ["매출매입장 PDF & 안내문", "카드매입 수기 입력건 엑셀 변환"])

# --- [메뉴 1] 매출매입장 PDF & 안내문 ---
if menu == "매출매입장 PDF & 안내문":
    st.title("⚖️ 부가세 신고 안내 및 장부 생성")
    with st.sidebar:
        st.header("📁 서류 업로드")
        tax_pdfs = st.file_uploader("1. 국세청 PDF (신고서/접수증)", type=['pdf'], accept_multiple_files=True)
        excel_files = st.file_uploader("2. 매출매입장 엑셀", type=['xlsx'], accept_multiple_files=True)

    final_reports = {}
    all_pdfs = []

    # 1. 국세청 PDF 분석
    if tax_pdfs:
        for file in tax_pdfs:
            with pdfplumber.open(file) as pdf:
                text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
                name_match = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", text)
                biz_name = name_match.group(1).strip() if name_match else file.name.split('_')[0]
                if biz_name not in final_reports: final_reports[biz_name] = {"vat": 0}
                vat_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", text)
                if vat_match:
                    val = to_int(vat_match.group(1))
                    final_reports[biz_name]["vat"] = -val if "환급" in text else val

    # 2. 엑셀 장부 분석 및 PDF 생성
    if excel_files:
        for ex in excel_files:
            df = find_header_and_read(ex)
            name_only = ex.name.split('_')[0]
            target_name = next((k for k in final_reports.keys() if k in name_only or name_only in k), name_only)
            if target_name not in final_reports: final_reports[target_name] = {"vat": 0}
            
            s_sum = to_int(df[df['구분'].str.contains('매출', na=False)]['합계'].sum())
            b_sum = to_int(df[df['구분'].str.contains('매입', na=False)]['합계'].sum())
            final_reports[target_name].update({"sales": s_sum, "buys": b_sum})

            # PDF 장부 생성
            dates = pd.to_datetime(df['전표일자'], errors='coerce').dropna()
            date_range = f"{dates.min().strftime('%Y-%m-%d')} ~ {dates.max().strftime('%Y-%m-%d')}" if not dates.empty else "기간미상"
            for g in ['매출', '매입']:
                target_df = df[df['구분'].str.contains(g, na=False)].reset_index(drop=True)
                if not target_df.empty:
                    pdf_buf = make_pdf_buffer(target_df, f"{g[0]} {g[1]} 장", date_range, target_name)
                    all_pdfs.append({"name": f"{target_name}_{g}장.pdf", "data": pdf_buf})

    # 화면 표시 및 다운로드
    if final_reports:
        st.subheader("✉️ 최종 발송용 안내문구")
        for name, info in final_reports.items():
            with st.expander(f"📌 {name} 안내문 보기", expanded=True):
                vat = info.get("vat", 0)
                status = "납부하실 세액" if vat >= 0 else "환급받으실 세액"
                msg = f"안녕하세요, {name} 대표님! 😊\n\n✅ 매출 합계: {info.get('sales', 0):,}원\n✅ 매입 합계: {info.get('buys', 0):,}원\n💰 최종 {status}: {abs(vat):,}원"
                if vat < 0: msg += "\n☆★ 환급은 8월 말경 입금될 예정입니다."
                st.text_area("카톡 복사용", msg, height=180, key=f"msg_{name}")
        
        if all_pdfs:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for p in all_pdfs: zf.writestr(p["name"], p["data"].getvalue())
            st.sidebar.download_button("🎁 모든 PDF 장부 다운로드(ZIP)", zip_buffer.getvalue(), "장부전체.zip", "application/zip", use_container_width=True)

# --- [메뉴 2] 카드매입 수기 입력건 엑셀 변환 ---
elif menu == "카드매입 수기 입력건 엑셀 변환":
    st.title("💳 카드매입 수기 입력건 엑셀 변환")
    uploaded_cards = st.file_uploader("카드사 엑셀 파일들을 선택하세요", type=['xlsx', 'xls'], accept_multiple_files=True)
    
    if uploaded_cards:
        all_rows = []
        for file in uploaded_cards:
            try:
                card_id = file.name.split('(')[-1].split(')')[0] if '(' in file.name else file.name.split('.')[0]
                df = find_header_and_read(file)
                col_map = {'매출일자': ['이용일자', '매출일자', '승인일자', '거래일자', '일자'],
                           '가맹점명': ['가맹점명', '가맹점명칭', '이용처', '상호'],
                           '사업자번호': ['사업자번호', '사업자등록번호', '가맹점사업자번호'],
                           '매출금액': ['이용금액', '매출금액', '승인금액', '결제금액', '합계']}
                res_df = pd.DataFrame()
                res_df['카드번호/구분'] = [card_id] * len(df)
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    res_df[std] = df[actual] if actual else ""
                res_df['매출금액'] = res_df['매출금액'].apply(to_int)
                res_df = res_df[res_df['매출금액'] > 0].copy()
                res_df['공급가액'] = (res_df['매출금액'] / 1.1).round(0).astype(int)
                res_df['부가세'] = res_df['매출금액'] - res_df['공급가액']
                res_df = res_df[['카드번호/구분', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                all_rows.append(res_df)
            except Exception as e: st.error(f"⚠️ {file.name} 변환 오류: {e}")

        if all_rows:
            final_df = pd.concat(all_rows, ignore_index=True)
            st.success("✅ 통합 변환 완료!"); st.dataframe(final_df, use_container_width=True)
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr: final_df.to_excel(wr, index=False)
            st.download_button("📥 변환된 엑셀 다운로드", out.getvalue(), "카드매입_수기입력용.xlsx", use_container_width=True)
