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

# 1. 폰트 설정 (더 안전한 방식으로 변경)
def load_font():
    font_path = "malgun.ttf"
    if os.path.exists(font_path):
        try:
            # 폰트 등록 시도
            pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
            return True
        except Exception as e:
            # 폰트 파일이 깨졌을 경우 에러 메시지 출력
            st.error(f"폰트 파일 해석 오류 (struct.error 가능성): {e}")
            return False
    return False

# @st.cache_resource 를 제거하고 직접 호출하여 에러를 즉시 확인합니다.
font_status = load_font()

# --- 이하 코드 동일 (PDF 생성 및 UI 로직) ---

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

def make_pdf_buffer(data, title, date_range, company_name):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # 폰트 등록이 성공했을 때만 해당 폰트 사용, 아니면 기본 Helvetica(한글 깨짐) 사용
    f_name = 'MalgunGothic' if font_status else 'Helvetica'
    
    rows_per_page = 26
    actual_item_count = 0 
    summary_keywords = ['합계', '월계', '분기', '반기', '누계']

    for i in range(len(data)):
        if i % rows_per_page == 0:
            if i > 0: c.showPage()
            p_num = (i // rows_per_page) + 1
            c.setFont(f_name, 20)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont(f_name, 10)
            c.drawString(50, height - 90, f"회사명 : {company_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            yh = 680 
            c.setLineWidth(1.5); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(f_name, 9)
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자"); c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        # ... (생략: 기존 데이터 처리 로직 동일하게 적용)
        
        c.drawRightString(410, cur_y, f"{to_int(row['공급가액']):,}")
        c.drawRightString(485, cur_y, f"{to_int(row['부가세']):,}")
        c.drawRightString(550, cur_y, f"{to_int(row['합계']):,}")

    c.save()
    buffer.seek(0)
    return buffer

# --- Streamlit UI 부분 ---
st.set_page_config(page_title="세무비서 자동화", layout="centered")

if not font_status:
    st.warning("⚠️ 맑은고딕 폰트를 불러오지 못했습니다. PDF 내 한글이 깨질 수 있습니다. malgun.ttf 파일이 올바른 형식인지 확인해주세요.")

# ... (이하 생략)
