import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import urllib.request

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
        if pd.isna(val): return 0
        clean = re.sub(r'[^0-9-]', '', str(val))
        return int(float(clean)) if clean else 0
    except: return 0

def find_header_and_read(file):
    """헤더 행을 자동으로 찾아 읽는 강화된 로직 (xls, xlsx 공통)"""
    try:
        df_temp = pd.read_excel(file, header=None)
        keywords = ['일자', '가맹점', '금액', '사업자', '구분', '승인']
        header_row = 0
        for i in range(min(30, len(df_temp))):
            row_vals = [str(v) for v in df_temp.iloc[i].values]
            if any(k in v for k in keywords for v in row_vals):
                header_row = i
                break
        file.seek(0)
        df = pd.read_excel(file, header=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"⚠️ '{file.name}' 읽기 실패: {e}")
        return None

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

# --- 3. 메뉴 구성 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")
MENU_1 = "⚖️ 매출매입장 PDF & 안내문"
MENU_2 = "💳 카드매입 수기 입력건 엑셀 변환"
menu = st.sidebar.selectbox("📂 업무 선택", [MENU_1, MENU_2])

# --- [메뉴 1] 매출매입장 로직 ---
if menu == MENU_1:
    st.title(MENU_1)
    with st.sidebar:
        st.header("파일 업로드")
        tax_pdfs = st.file_uploader("1. 국세청 PDF", type=['pdf'], accept_multiple_files=True)
        excel_files = st.file_uploader("2. 매출매입장 엑셀", type=['xlsx'], accept_multiple_files=True)

    final_reports = {}
    all_pdfs = []

    if tax_pdfs:
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

    if excel_files:
        for ex in excel_files:
            df = find_header_and_read(ex)
            if df is not None:
                name_only = ex.name.split('_')[0]
                target_name = next((k for k in final_reports.keys() if k in name_only or name_only in k), name_only)
                if target_name not in final_reports: final_reports[target_name] = {"vat": 0}
                s_sum = to_int(df[df['구분'].astype(str).str.contains('매출', na=False)]['합계'].sum())
                b_sum = to_int(df[df['구분'].astype(str).str.contains('매입', na=False)]['합계'].sum())
                final_reports[target_name].update({"sales": s_sum, "buys": b_sum})
                dates = pd.to_datetime(df['전표일자'], errors='coerce').dropna()
                date_range = f"{dates.min().strftime('%Y-%m-%d')} ~ {dates.max().strftime('%Y-%m-%d')}" if not dates.empty else "기간미상"
                for g in ['매출', '매입']:
                    target_df = df[df['구분'].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not target_df.empty:
                        all_pdfs.append({"name": f"{target_name}_{g}장.pdf", "data": make_pdf_buffer(target_df, f"{g} 장", date_range, target_name)})

    if final_reports:
        st.subheader("✉️ 카톡 안내문구")
        for name, info in final_reports.items():
            with st.expander(f"📌 {name} 안내문", expanded=True):
                vat = info.get("vat", 0); status = "납부하실 세액" if vat >= 0 else "환급받으실 세액"
                msg = f"안녕하세요, {name} 대표님! 😊\n\n✅ 매출 합계: {info.get('sales', 0):,}원\n✅ 매입 합계: {info.get('buys', 0):,}원\n💰 최종 {status}: {abs(vat):,}원"
                if vat < 0: msg += "\n☆★ 환급은 8월 말경 입금될 예정입니다."
                st.text_area("카톡 복사용", msg, height=140)
        if all_pdfs:
            z_buf = io.BytesIO()
            with zipfile.ZipFile(z_buf, "w") as zf:
                for p in all_pdfs: zf.writestr(p["name"], p["data"].getvalue())
            st.sidebar.download_button("📥 모든 PDF 장부 다운로드(ZIP)", z_buf.getvalue(), "장부전체.zip", use_container_width=True)

# --- [메뉴 2] 카드 정제 로직 (개별 저장형) ---
elif menu == MENU_2:
    st.title(MENU_2)
    st.write("카드사 엑셀들을 각각 정제하여 ZIP 파일로 내려받습니다.")
    uploaded_cards = st.file_uploader("카드사 엑셀들을 선택하세요", type=['xlsx', 'xls'], accept_multiple_files=True)
    
    if uploaded_cards:
        processed_items = []
        for file in uploaded_cards:
            df = find_header_and_read(file)
            if df is not None:
                card_id = file.name.split('(')[-1].split(')')[0] if '(' in file.name else file.name.split('.')[0]
                col_map = {'매출일자': ['일자', '승인일', '이용일', '매출일'], '가맹점명': ['가맹점', '이용처', '상호'],
                           '사업자번호': ['사업자', '등록번호'], '매출금액': ['금액', '합계', '승인금액', '이용금액']}
                res_df = pd.DataFrame()
                res_df['카드번호/구분'] = [card_id] * len(df)
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    res_df[std] = df[actual] if actual else ""
                res_df['매출금액'] = res_df['매출금액'].apply(to_int)
                res_df = res_df[res_df['매출금액'] > 0].copy()
                res_df['공급가액'] = (res_df['매출금액'] / 1.1).round(0).astype(int)
                res_df['부가세'] = res_df['매출금액'] - res_df['공급가액']
                final_df = res_df[['카드번호/구분', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                processed_items.append({"name": f"정제_{card_id}.xlsx", "df": final_df})

        if processed_items:
            st.success(f"✅ {len(processed_items)}개 파일 변환 성공!")
            zip_out = io.BytesIO()
            with zipfile.ZipFile(zip_out, "w") as zf:
                for item in processed_items:
                    excel_buf = io.BytesIO()
                    item["df"].to_excel(excel_buf, index=False)
                    zf.writestr(item["name"], excel_buffer.getvalue() if 'excel_buffer' in locals() else excel_buf.getvalue())
            st.download_button("📥 변환된 카드별 엑셀(ZIP) 다운로드", zip_out.getvalue(), "카드매입_개별파일.zip", use_container_width=True)
            for item in processed_items:
                with st.expander(f"👀 {item['name']} 미리보기"): st.dataframe(item["df"])
