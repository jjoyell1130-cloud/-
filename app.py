import streamlit as st
import pandas as pd
import io
import os
import zipfile  # 압축 기능을 위한 라이브러리 추가
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. PDF 변환 로직 (기존 성공 양식 유지)] ---
try:
    font_path = "malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        FONT_NAME = 'MalgunGothic'
    else:
        FONT_NAME = 'Helvetica'
except:
    FONT_NAME = 'Helvetica'

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

def make_pdf_stream(data, title, biz_name, date_range):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    rows_per_page = 26
    actual_item_count = 0 
    summary_keywords = ['합계', '월계', '분기', '반기', '누계']

    for i in range(len(data)):
        if i % rows_per_page == 0:
            if i > 0: c.showPage()
            p_num = (i // rows_per_page) + 1
            c.setFont(FONT_NAME, 20)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont(FONT_NAME, 10)
            c.drawString(50, height - 90, f"회사명 : {biz_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            
            yh = 680 
            c.setLineWidth(1.5); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(FONT_NAME, 9)
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자")
            c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세")
            c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        def check_summary(r):
            txt = (str(r.get('번호', '')) + str(r.get('거래처', ''))).replace(" ", "")
            return any(k in txt for k in summary_keywords)

        is_curr_summary = check_summary(row)
        c.setFont(FONT_NAME, 8.5)
        
        if is_curr_summary:
            c.setFont(FONT_NAME, 9)
            c.drawString(90, cur_y, str(row.get('거래처', row.get('번호', ''))))
            c.setLineWidth(1.2); c.line(40, cur_y + 16, 555, cur_y + 16)
            c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.drawString(45, cur_y, str(actual_item_count))
            raw_date = row.get('전표일자', '')
            date_str = str(raw_date)[:10] if pd.notna(raw_date) else ""
            c.drawString(85, cur_y, date_str)
            c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
            c.setLineWidth(0.3); c.setStrokeColor(colors.lightgrey)
            c.line(40, cur_y - 7, 555, cur_y - 7)
        
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
        c.setStrokeColor(colors.black)

    c.save()
    buffer.seek(0)
    return buffer

# --- [2. 메뉴 및 사이드바 설정] ---
M0, M1, M2, M3 = "🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = M0

st.set_page_config(page_title="세무 통합 시스템", layout="wide")
with st.sidebar:
    st.markdown("### 📁 Menu")
    for m in [M0, M1, M2, M3]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.selected_menu == m else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()

# --- [3. 메인 화면 - ZIP 일괄 다운로드 구현] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M2:
    f = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'])
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        
        # 날짜 범위 추출 (에러 방지 강화)
        try:
            temp_dates = pd.to_datetime(df['전표일자'], errors='coerce').dropna()
            date_range = f"{temp_dates.min().strftime('%Y-%m-%d')} ~ {temp_dates.max().strftime('%Y-%m-%d')}" if not temp_dates.empty else "기간 없음"
        except:
            date_range = "기간 정보 없음"

        type_col = next((c for c in ['구분', '유형'] if c in df.columns), None)
        if type_col:
            st.success(f"업체명: {biz_name} / 분석 완료")
            
            # 매출/매입 데이터 분리
            sales_df = df[df[type_col].astype(str).str.contains('매출', na=False)].reset_index(drop=True)
            purchase_df = df[df[type_col].astype(str).str.contains('매입', na=False)].reset_index(drop=True)

            # 화면 표시
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📈 매출장")
                st.dataframe(sales_df, height=250)
            with c2:
                st.subheader("📉 매입장")
                st.dataframe(purchase_df, height=250)

            st.divider()

            # --- [ZIP 생성 핵심 로직] ---
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                # 1. 매출장 PDF 생성 및 추가
                if not sales_df.empty:
                    s_pdf = make_pdf_stream(sales_df, "매출 장", biz_name, date_range)
                    zip_file.writestr(f"{biz_name}_매출장.pdf", s_pdf.getvalue())
                
                # 2. 매입장 PDF 생성 및 추가
                if not purchase_df.empty:
                    p_pdf = make_pdf_stream(purchase_df, "매입 장", biz_name, date_range)
                    zip_file.writestr(f"{biz_name}_매입장.pdf", p_pdf.getvalue())

            # 다운로드 버튼
            st.download_button(
                label="🎁 매출/매입장 PDF 한 번에 다운로드 (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"{biz_name}_매출매입장_일괄.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.error("'구분' 또는 '유형' 컬럼을 찾을 수 없습니다.")

elif curr == M0:
    st.info("Home 화면입니다. 사이드바 메뉴를 이용해 주세요.")
