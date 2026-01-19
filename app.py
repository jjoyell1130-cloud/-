import streamlit as st
import pandas as pd
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. 한글 폰트 등록] ---
# Streamlit Cloud 환경에서도 동작하도록 malgun.ttf를 등록합니다.
try:
    pdfmetrics.registerFont(TTFont('MalgunGothic', "malgun.ttf"))
    FONT_NAME = 'MalgunGothic'
except:
    FONT_NAME = 'Helvetica'

# --- [2. 성공했던 PDF 생성 로직 (pdf_convert.py 기반)] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except:
        return 0

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
            c.setLineWidth(1.5)
            c.line(40, yh + 15, 555, yh + 15)
            c.setFont(FONT_NAME, 9)
            c.drawString(45, yh, "번호")
            c.drawString(90, yh, "일자")
            c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액")
            c.drawRightString(485, yh, "부가가치세")
            c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0)
            c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        # 요약 행 여부 확인
        def check_summary(r):
            if r is None: return False
            t_no = str(r['번호']) if pd.notna(r['번호']) else ""
            t_vendor = str(r['거래처']) if pd.notna(r['거래처']) else ""
            txt = (t_no + t_vendor).replace(" ", "").replace("[", "").replace("]", "")
            return any(k in txt for k in summary_keywords)

        is_curr_summary = check_summary(row)
        next_row = data.iloc[i+1] if i+1 < len(data) else None
        is_next_summary = check_summary(next_row)
        
        c.setFont(FONT_NAME, 8.5)
        
        if is_curr_summary:
            c.setFont(FONT_NAME, 9)
            c.drawString(90, cur_y, str(row['거래처']) if pd.notna(row['거래처']) else str(row['번호']))
            prev_row = data.iloc[i-1] if i > 0 else None
            if not check_summary(prev_row):
                c.setLineWidth(1.2)
                c.line(40, cur_y + 16, 555, cur_y + 16)
            if not is_next_summary:
                c.setLineWidth(1.2)
                c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.drawString(45, cur_y, str(actual_item_count))
            c.drawString(85, cur_y, str(row['전표일자']) if pd.notna(row['전표일자']) else "")
            c.drawString(170, cur_y, str(row['거래처'])[:25] if pd.notna(row['거래처']) else "")
            c.setLineWidth(0.3)
            c.setStrokeColor(colors.lightgrey)
            c.line(40, cur_y - 7, 555, cur_y - 7)
        
        c.drawRightString(410, cur_y, f"{to_int(row['공급가액']):,}")
        c.drawRightString(485, cur_y, f"{to_int(row['부가세']):,}")
        c.drawRightString(550, cur_y, f"{to_int(row['합계']):,}")
        c.setStrokeColor(colors.black)

    c.save()
    buffer.seek(0)
    return buffer

# --- [3. 세션 및 사이드바 설정] ---
M0, M1, M2, M3 = "🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"
if 'menu' not in st.session_state: st.session_state.menu = M0

st.set_page_config(layout="wide")
with st.sidebar:
    st.markdown("### 📂 Menu")
    for m in [M0, M1, M2, M3]:
        if st.button(m, key=f"btn_{m}", type="primary" if st.session_state.menu == m else "secondary", use_container_width=True):
            st.session_state.menu = m
            st.rerun()
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.text_area("Memo", height=200, key="side_memo")

# --- [4. 메인 변환 기능 구현] ---
curr = st.session_state.menu
st.title(curr)

if curr == M2:
    f = st.file_uploader("📊 엑셀 업로드", type=['xlsx'])
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        
        # 날짜 범위 추출
        date_series = df['전표일자'].dropna().astype(str)
        date_range = f"{date_series.min()} ~ {date_series.max()}" if not date_series.empty else "기간 없음"

        type_col = next((c for c in ['구분', '유형'] if c in df.columns), None)
        if type_col:
            st.success(f"데이터 분석 완료: {biz_name}")
            c1, c2 = st.columns(2)
            for i, g in enumerate(['매출', '매입']):
                with [c1, c2][i]:
                    st.subheader(f"📈 {g}장")
                    target = df[df[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not target.empty:
                        st.dataframe(target, height=300)
                        pdf_data = make_pdf_stream(target, f"{g} 장", biz_name, date_range)
                        st.download_button(f"📥 {g} PDF 다운로드", pdf_data, file_name=f"{biz_name}_{g}장.pdf")
        else:
            st.error("'구분' 컬럼을 찾을 수 없습니다.")
