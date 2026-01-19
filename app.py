import streamlit as st
import pdfplumber
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import io
import urllib.request
import zipfile

# 1. 폰트 설정
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

# 2. 데이터 처리 보조 함수
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

def get_clean_date_range(df):
    """전표일자 컬럼에서 정확한 기간을 추출하는 함수"""
    try:
        # 전표일자 컬럼을 날짜 형식으로 변환 (에러나는 데이터는 NaT 처리)
        dates = pd.to_datetime(df['전표일자'], errors='coerce').dropna()
        if not dates.empty:
            start_date = dates.min().strftime('%Y-%m-%d')
            end_date = dates.max().strftime('%Y-%m-%d')
            return f"{start_date} ~ {end_date}"
        return "기간 정보 없음"
    except:
        return "기간 확인 불가"

# 3. PDF 생성 함수 (기존과 동일하되 f_name 적용)
def make_pdf_buffer(data, title, date_range, company_name):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    rows_per_page = 26
    actual_item_count = 0 
    
    for i in range(len(data)):
        if i % rows_per_page == 0:
            if i > 0: c.showPage()
            c.setFont(f_name, 20)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont(f_name, 10)
            c.drawString(50, height - 90, f"회사명 : {company_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            yh = 680 
            c.setLineWidth(1.5); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(f_name, 9)
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자"); c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        actual_item_count += 1
        c.setFont(f_name, 8.5)
        c.drawString(45, cur_y, str(actual_item_count))
        # 날짜가 Timestamp인 경우를 대비해 문자열 처리
        date_str = str(row['전표일자'])[:10] if pd.notna(row['전표일자']) else ""
        c.drawString(85, cur_y, date_str)
        c.drawString(170, cur_y, str(row['거래처'])[:25] if pd.notna(row['거래처']) else "")
        c.drawRightString(410, cur_y, f"{to_int(row['공급가액']):,}")
        c.drawRightString(485, cur_y, f"{to_int(row['부가세']):,}")
        c.drawRightString(550, cur_y, f"{to_int(row['합계']):,}")

    c.save()
    buffer.seek(0)
    return buffer

# 4. Streamlit UI
st.set_page_config(page_title="세무비서 자동화", layout="centered")

st.sidebar.title("📑 매출매입장 PDF 생성")
uploaded_excels = st.sidebar.file_uploader("엑셀 파일들을 선택하세요", type=['xlsx'], accept_multiple_files=True)

if uploaded_excels:
    all_pdfs = []
    for uploaded_excel in uploaded_excels:
        try:
            name_only = uploaded_excel.name.split('.')[0]
            df_excel = pd.read_excel(uploaded_excel)
            
            # --- 기간 추출 로직 개선 적용 ---
            date_range = get_clean_date_range(df_excel)
            
            clean_df = df_excel[df_excel['구분'].isin(['매입', '매출'])].copy()
            for g in ['매출', '매입']:
                target = clean_df[clean_df['구분'] == g].reset_index(drop=True)
                if not target.empty:
                    pdf_buf = make_pdf_buffer(target, f"{g[0]} {g[1]} 장", date_range, name_only)
                    all_pdfs.append({"name": f"{name_only}_{g}장.pdf", "data": pdf_buf})
        except Exception as e:
            st.sidebar.error(f"오류: {e}")

    if all_pdfs:
        st.sidebar.markdown("---")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for pdf in all_pdfs:
                zf.writestr(pdf["name"], pdf["data"].getvalue())
        zip_buffer.seek(0)
        st.sidebar.download_button(label="🎁 모든 PDF 한꺼번에 다운로드 (ZIP)", data=zip_buffer, file_name="모든_업체_장부.zip", mime="application/zip", use_container_width=True)
        for pdf in all_pdfs:
            st.sidebar.download_button(label=f"📥 {pdf['name']}", data=pdf['data'], file_name=pdf['name'], mime="application/pdf")

# 메인 화면 로직은 기존과 동일하므로 생략
st.title("📊 부가세 신고 안내문 생성기")
st.info("왼쪽 사이드바를 이용해 주세요.")
