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
import zipfile

# --- [1. 안전한 폰트 로딩] ---
@st.cache_resource
def load_font_safe():
    font_path = "malgun.ttf"
    # 파일이 존재하고 실제 데이터가 들어있는지(최소 1MB 이상) 확인
    if os.path.exists(font_path) and os.path.getsize(font_path) > 1024 * 1024:
        try:
            pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
            return 'MalgunGothic'
        except Exception:
            # struct.error 발생 시 우회
            return 'Helvetica'
    return 'Helvetica'

# 전역 폰트 설정
FONT_NAME = load_font_safe()

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

# --- [2. PDF 생성 로직 (Menu 2)] ---
def make_pdf_buffer(data, title, biz_name, date_range):
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
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자"); c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        # 요약행 체크 로직 (pdf_convert.py 기준)
        txt = (str(row.get('번호', '')) + str(row.get('거래처', ''))).replace(" ", "")
        is_summary = any(k in txt for k in summary_keywords)

        if is_summary:
            c.setFont(FONT_NAME, 9)
            c.drawString(90, cur_y, str(row.get('거래처', row.get('번호', ''))))
        else:
            actual_item_count += 1
            c.setFont(FONT_NAME, 8.5)
            c.drawString(45, cur_y, str(actual_item_count))
            c.drawString(85, cur_y, str(row.get('전표일자', ''))[:10])
            c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
        
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")

    c.save()
    buffer.seek(0)
    return buffer

# --- [3. 메인 UI 및 사이드바] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

with st.sidebar:
    st.title("📁 세무 통합 메뉴")
    menus = ["🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"]
    for m in menus:
        if st.button(m, use_container_width=True, type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

# --- [4. 메뉴별 로직] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == "🏠 Home":
    st.write("사이드바에서 메뉴를 선택하세요.")

elif curr == "⚖️ 마감작업":
    st.subheader("📊 부가세 신고 안내문 분석")
    uploaded_files = st.file_uploader("위하고 PDF 선택", accept_multiple_files=True, type=['pdf'])
    if uploaded_files:
        # 기존 텍스트 추출 로직
        st.success(f"{len(uploaded_files)}개 분석 중...")

elif curr == "📁 매출매입장 PDF 변환":
    st.info("엑셀을 PDF로 변환하여 ZIP으로 저장합니다.")
    f = st.file_uploader("엑셀 업로드", type=['xlsx'])
    if f:
        df_excel = pd.read_excel(f)
        biz_name = f.name.split(' ')[0]
        date_range = "기간 데이터 참조"
        
        pdf_buf = make_pdf_buffer(df_excel, "매출매입장", biz_name, date_range)
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr(f"{biz_name}_장부.pdf", pdf_buf.getvalue())
        
        st.download_button("📥 PDF 장부 다운로드(ZIP)", zip_buf.getvalue(), f"{biz_name}_PDF.zip")

elif curr == "💳 카드매입 수기입력건":
    st.info("카드 엑셀을 위하고 양식(공급가/부가세 자동계산)으로 변환하여 ZIP으로 저장합니다.")
    card_f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'])
    if card_f:
        df = pd.read_excel(card_f)
        amt_col = next((c for c in df.columns if any(k in str(c) for k in ['금액', '합계', '이용', '승인'])), None)
        
        if amt_col:
            # 위하고용 공급가액/부가세 계산
            df['합계액'] = df[amt_col].apply(to_int)
            df['공급가액'] = (df['합계액'] / 1.1).round(0).astype(int)
            df['부가세'] = df['합계액'] - df['공급가액']
            
            # 엑셀 저장 및 ZIP 구성
            excel_out = io.BytesIO()
            with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='위하고_수기입력용')
            
            zip_out = io.BytesIO()
            with zipfile.ZipFile(zip_out, "w") as zf:
                zf.writestr(f"위하고_변환_{card_f.name}", excel_out.getvalue())
            
            st.success("✅ 변환 완료!")
            st.download_button("📥 위하고 변환 엑셀 다운로드 (ZIP)", zip_out.getvalue(), f"WEHAGO_{card_f.name.split('.')[0]}.zip")
