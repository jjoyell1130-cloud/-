import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. PDF 변환 로직: 날짜 처리 강화] ---
try:
    # 폰트 경로를 유연하게 설정 (로컬 및 클라우드 공용)
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
            # 날짜 출력 형식 안정화
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

# --- [2. 세션 상태 초기화] ---
M0, M1, M2, M3 = "🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = M0
if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""

# --- [3. 디자인 및 사이드바] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
with st.sidebar:
    st.markdown("### 📁 Menu")
    for m in [M0, M1, M2, M3]:
        if st.button(m, key=f"m_{m}", type="primary" if st.session_state.selected_menu == m else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()
    for _ in range(10): st.write("")
    st.divider()
    memo = st.text_area("Memo", value=st.session_state.daily_memo, height=200, label_visibility="collapsed")
    if st.button("💾 저장"): st.session_state.daily_memo = memo

# --- [4. 메인 화면 - PDF 변환 (날짜 오류 수정본)] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M2:
    f = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'])
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        
        # [해결] 날짜 범위 추출 오류 방지 로직
        try:
            # 전표일자 컬럼을 날짜 형식으로 강제 변환 (오류 데이터는 NaT 처리)
            temp_dates = pd.to_datetime(df['전표일자'], errors='coerce').dropna()
            if not temp_dates.empty:
                date_range = f"{temp_dates.min().strftime('%Y-%m-%d')} ~ {temp_dates.max().strftime('%Y-%m-%d')}"
            else:
                date_range = "기간 정보 없음"
        except:
            date_range = "날짜 형식 확인 필요"

        type_col = next((c for c in ['구분', '유형'] if c in df.columns), None)
        if type_col:
            st.success(f"업체명: {biz_name} / 기간: {date_range}")
            cols = st.columns(2)
            for i, g in enumerate(['매출', '매입']):
                with cols[i]:
                    st.subheader(f"📈 {g}장")
                    target = df[df[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not target.empty:
                        st.dataframe(target, height=300)
                        pdf_stream = make_pdf_stream(target, f"{g} 장", biz_name, date_range)
                        st.download_button(f"📥 {g} PDF 다운로드", pdf_stream, file_name=f"{biz_name}_{g}장.pdf")
        else:
            st.error("'구분' 또는 '유형' 컬럼을 찾을 수 없습니다.")

elif curr == M0:
    st.subheader("🔗 바로가기")
    # (기존 홈 화면 구성...)
