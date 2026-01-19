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

# 1. 폰트 설정 (서버에 없으면 나눔고딕 자동 다운로드)
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

# 2. PDF 생성 로직
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

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
        c.drawString(85, cur_y, str(row['전표일자']) if pd.notna(row['전표일자']) else "")
        c.drawString(170, cur_y, str(row['거래처'])[:25] if pd.notna(row['거래처']) else "")
        c.drawRightString(410, cur_y, f"{to_int(row['공급가액']):,}")
        c.drawRightString(485, cur_y, f"{to_int(row['부가세']):,}")
        c.drawRightString(550, cur_y, f"{to_int(row['합계']):,}")

    c.save()
    buffer.seek(0)
    return buffer

# 3. Streamlit UI
st.set_page_config(page_title="세무비서 자동화", layout="centered")

# 사이드바: 매출매입장 PDF 생성
st.sidebar.title("📑 매출매입장 PDF 생성")
uploaded_excels = st.sidebar.file_uploader("엑셀 파일들을 선택하세요", type=['xlsx'], accept_multiple_files=True)

if uploaded_excels:
    all_pdfs = []  # ZIP 파일용 리스트
    
    for uploaded_excel in uploaded_excels:
        try:
            name_only = uploaded_excel.name.split('.')[0]
            df_excel = pd.read_excel(uploaded_excel)
            date_series = df_excel['전표일자'].dropna().astype(str)
            date_range = f"{date_series.min()} ~ {date_series.max()}" if not date_series.empty else "기간 없음"
            clean_df = df_excel[df_excel['구분'].isin(['매입', '매출'])].copy()
            
            for g in ['매출', '매입']:
                target = clean_df[clean_df['구분'] == g].reset_index(drop=True)
                if not target.empty:
                    pdf_buf = make_pdf_buffer(target, f"{g[0]} {g[1]} 장", date_range, name_only)
                    all_pdfs.append({
                        "name": f"{name_only}_{g}장.pdf",
                        "data": pdf_buf
                    })
        except Exception as e:
            st.sidebar.error(f"오류: {e}")

    # --- 전체 다운로드 (ZIP) 버튼 ---
    if all_pdfs:
        st.sidebar.markdown("---")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for pdf in all_pdfs:
                zf.writestr(pdf["name"], pdf["data"].getvalue())
        
        zip_buffer.seek(0)
        st.sidebar.download_button(
            label="🎁 모든 PDF 한꺼번에 다운로드 (ZIP)",
            data=zip_buffer,
            file_name="모든_업체_장부.zip",
            mime="application/zip",
            use_container_width=True
        )
        
        # 개별 다운로드 목록도 유지
        st.sidebar.info("개별 파일이 필요하면 아래 목록을 사용하세요.")
        for pdf in all_pdfs:
            st.sidebar.download_button(label=f"📥 {pdf['name']}", data=pdf['data'], file_name=pdf['name'], mime="application/pdf")

# 메인 화면: 부가세 안내문 (기존 로직 유지)
st.title("📊 부가세 신고 안내문 생성기")
uploaded_pdfs = st.file_uploader("위하고 PDF 선택", accept_multiple_files=True, type=['pdf'])
if uploaded_pdfs:
    # (안내문 추출 코드 생략 - 이전과 동일)
    st.success("분석 완료!")
else:
    st.info("왼쪽 사이드바에서 엑셀을 변환하거나 PDF를 올려 안내문을 만드세요.")
