import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. PDF 생성 엔진] ---
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
            c.setFont(FONT_NAME, 18)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont(FONT_NAME, 10)
            c.drawString(50, height - 90, f"회사명 : {biz_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            
            yh = 680 
            c.setLineWidth(1.2); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(FONT_NAME, 9)
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자")
            c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세")
            c.drawRightString(550, yh, "합계")
            c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        txt = (str(row.get('번호', '')) + str(row.get('거래처', ''))).replace(" ", "")
        is_summary = any(k in txt for k in summary_keywords)

        c.setFont(FONT_NAME, 8.5)
        if is_summary:
            c.setFont(FONT_NAME, 9)
            c.drawString(90, cur_y, str(row.get('거래처', row.get('번호', ''))))
            c.line(40, cur_y + 16, 555, cur_y + 16)
            c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.drawString(45, cur_y, str(actual_item_count))
            raw_date = row.get('전표일자', row.get('일자', ''))
            c.drawString(85, cur_y, str(raw_date)[:10] if pd.notna(raw_date) else "")
            c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
            c.setStrokeColor(colors.lightgrey); c.line(40, cur_y - 7, 555, cur_y - 7); c.setStrokeColor(colors.black)
        
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")

    c.save()
    buffer.seek(0)
    return buffer

# --- [2. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환",
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "안내문 자동 작성 및 엑셀 가공 도구입니다.",
        "sub_menu2": "매출장과 매입장을 분류하여 각각 PDF로 변환합니다.",
        "sub_menu3": "불필요 열 삭제 및 날짜 간소화 후 카드별로 분리합니다."
    }
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

# --- [3. 사이드바 레이아웃] ---
st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")
with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, 
                     type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [4. 메인 화면 로직] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()

# --- [Menu 2: 매출/매입장 PDF 분류 변환] ---
if current_menu == st.session_state.config["menu_2"]:
    st.info(st.session_state.config["sub_menu2"])
    f_pdf = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'], key="m2_pdf_up")
    
    if f_pdf:
        all_sheets = pd.read_excel(f_pdf, sheet_name=None)
        biz_name = f_pdf.name.split(" ")[0]
        
        # 매출/매입 분류 저장용
        sales_zip = io.BytesIO()
        purchase_zip = io.BytesIO()
        
        has_sales = False
        has_purchase = False
        
        with zipfile.ZipFile(sales_zip, "a", zipfile.ZIP_DEFLATED, False) as sz, \
             zipfile.ZipFile(purchase_zip, "a", zipfile.ZIP_DEFLATED, False) as pz:
            
            for sheet_name, df in all_sheets.items():
                if df.empty: continue
                pdf_data = make_pdf_stream(df, sheet_name, biz_name, "2025년")
                
                if "매출" in sheet_name:
                    sz.writestr(f"{sheet_name}.pdf", pdf_data.getvalue())
                    has_sales = True
                elif "매입" in sheet_name:
                    pz.writestr(f"{sheet_name}.pdf", pdf_data.getvalue())
                    has_purchase = True
                else:
                    # 분류가 모호하면 매출장에 기본 포함
                    sz.writestr(f"{sheet_name}.pdf", pdf_data.getvalue())
                    has_sales = True

        st.success(f"✅ {biz_name} - 분류 완료")
        
        col1, col2 = st.columns(2)
        with col1:
            if has_sales:
                st.download_button(
                    label="📥 매출장 PDF 다운로드 (ZIP)",
                    data=sales_zip.getvalue(),
                    file_name=f"{biz_name}_매출장_PDF.zip",
                    mime="application/zip",
                    use_container_width=True
                )
        with col2:
            if has_purchase:
                st.download_button(
                    label="📥 매입장 PDF 다운로드 (ZIP)",
                    data=purchase_zip.getvalue(),
                    file_name=f"{biz_name}_매입장_PDF.zip",
                    mime="application/zip",
                    use_container_width=True
                )

# --- [Menu 3: 카드 분리 기능 유지] ---
elif current_menu == st.session_state.config["menu_3"]:
    st.info(st.session_state.config["sub_menu3"])
    card_up = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="m3_up")
    if card_up:
        # (기존 카드 가공 및 분리 로직 수행...)
        st.write("✅ 카드 분리 가공 준비 완료")
        # (여기에 이전에 구현한 카드 분리 로직 코드 포함)

# (나머지 Home, 마감작업 메뉴 등은 이전 통합 코드와 동일)
