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

# --- [1. 폰트 및 공통 유틸리티] ---
@st.cache_resource
def load_font():
    font_path = "malgun.ttf"  # GitHub에 올린 파일명
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        return True
    return False

font_status = load_font()

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

# --- [2. PDF 장부 생성 로직 (Menu 2용)] ---
def make_pdf_buffer(data, title, date_range):
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
            c.setFont('MalgunGothic', 20)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont('MalgunGothic', 10)
            c.drawString(50, height - 90, "회사명 : 에덴인테리어")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            yh = 680 
            c.setLineWidth(1.5); c.line(40, yh + 15, 555, yh + 15)
            c.setFont('MalgunGothic', 9)
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자"); c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        def check_summary(r):
            if r is None: return False
            t_no, t_vendor = str(r.get('번호', '')), str(r.get('거래처', ''))
            txt = (t_no + t_vendor).replace(" ", "").replace("[", "").replace("]", "")
            return any(k in txt for k in summary_keywords)

        is_curr_summary = check_summary(row)
        if is_curr_summary:
            c.setFont('MalgunGothic', 9)
            c.drawString(90, cur_y, str(row.get('거래처', row.get('번호', ''))))
            prev_row = data.iloc[i-1] if i > 0 else None
            if not check_summary(prev_row):
                c.setLineWidth(1.2); c.line(40, cur_y + 16, 555, cur_y + 16)
            next_row = data.iloc[i+1] if i+1 < len(data) else None
            if not check_summary(next_row):
                c.setLineWidth(1.2); c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.setFont('MalgunGothic', 8.5)
            c.drawString(45, cur_y, str(actual_item_count))
            c.drawString(85, cur_y, str(row.get('전표일자', ''))[:10])
            c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
            c.setLineWidth(0.3); c.setStrokeColor(colors.lightgrey); c.line(40, cur_y - 7, 555, cur_y - 7)
            c.setStrokeColor(colors.black)
        
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
    
    c.save()
    buffer.seek(0)
    return buffer

# --- [3. Streamlit 설정 및 사이드바] ---
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

# --- [4. 메인 로직] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == "🏠 Home":
    st.info("왼쪽 사이드바에서 원하시는 업무를 선택해주세요.")

elif curr == "⚖️ 마감작업":
    st.subheader("📊 부가세 신고 안내문 분석")
    uploaded_files = st.file_uploader("위하고 PDF 파일들을 선택하세요", accept_multiple_files=True, type=['pdf'])
    if uploaded_files:
        # 로직 적용
        first_file_name = uploaded_files[0].name
        biz_name = first_file_name.split('_')[0] if '_' in first_file_name else "알 수 없음"
        report_data = {"매출": "0", "매입": "0", "환급": "0"}
        for file in uploaded_files:
            with pdfplumber.open(file) as pdf:
                text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
                if "매출장" in file.name:
                    for line in text.split('\n'):
                        if "누계" in line:
                            nums = "".join([c for c in line if c.isdigit() or c == ',']).split(',')
                            if len(nums) >= 2: report_data["매출"] = f"{nums[-2]},{nums[-1]}"
                elif "매입장" in file.name:
                    for line in text.split('\n'):
                        if "누계매입" in line:
                            nums = "".join([c for c in line if c.isdigit() or c == ',']).split(',')
                            if len(nums) >= 2: report_data["매입"] = f"{nums[-2]},{nums[-1]}"
                elif "접수증" in file.name or "신고서" in file.name:
                    for line in text.split('\n'):
                        if "차가감납부할세액" in line:
                            report_data["환급"] = "".join([c for c in line if c.isdigit() or c == ','])
        st.success(f"✅ {biz_name} 분석 완료!")
        st.text_area("카톡 복사용 내용", f"-매출장: {report_data['매출']}원\n-매입장: {report_data['매입']}원\n-환급예정: {report_data['환급']}원", height=150)

elif curr == "📁 매출매입장 PDF 변환":
    st.info("엑셀 장부를 PDF로 변환하여 ZIP으로 저장합니다.")
    uploaded_excel = st.file_uploader("장부 엑셀 업로드", type=['xlsx'])
    if uploaded_excel:
        df_excel = pd.read_excel(uploaded_excel)
        biz_name = uploaded_excel.name.split(' ')[0]
        date_series = df_excel['전표일자'].dropna().astype(str)
        date_range = f"{date_series.min()} ~ {date_series.max()}" if not date_series.empty else "기간 없음"
        
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            clean_df = df_excel[df_excel['구분'].isin(['매입', '매출'])].copy()
            for g in ['매출', '매입']:
                target = clean_df[clean_df['구분'] == g].reset_index(drop=True)
                if not target.empty:
                    pdf_data = make_pdf_buffer(target, f"{g[0]} {g[1]} 장", date_range)
                    zf.writestr(f"{biz_name}_{g}장.pdf", pdf_data.getvalue())
        st.download_button("📥 PDF 장부 ZIP 다운로드", zip_buf.getvalue(), f"{biz_name}_장부.zip", use_container_width=True)

elif curr == "💳 카드매입 수기입력건":
    st.info("카드사 엑셀을 업로드하면 '공급가액/부가세'를 산출하여 ZIP으로 변환합니다.")
    card_f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'])
    if card_f:
        try:
            df = pd.read_excel(card_f)
            # 금액 컬럼 자동 찾기
            amt_col = next((c for c in df.columns if any(k in str(c) for k in ['금액', '합계', '이용', '승인'])), None)
            
            if amt_col:
                # 엑셀 변환 (공급가/부가세 산출)
                df['합계액'] = df[amt_col].apply(to_int)
                df['공급가액'] = (df['합계액'] / 1.1).round(0).astype(int)
                df['부가세'] = df['합계액'] - df['공급가액']
                
                # 가공된 엑셀을 ZIP으로 생성
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='위하고_업로드용')
                
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as zf:
                    zf.writestr(f"위하고_변환_{card_f.name}", excel_buf.getvalue())
                
                st.success("✅ 위하고용 엑셀 변환 완료!")
                st.download_button("📥 위하고 수기입력용 양식 다운로드 (ZIP)", zip_buf.getvalue(), f"WEHAGO_{card_f.name.split('.')[0]}.zip", use_container_width=True)
            else:
                st.error("엑셀 파일에서 금액 관련 컬럼을 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"오류: {e}")
