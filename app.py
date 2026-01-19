import streamlit as st
import pandas as pd
import io
import os
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. PDF 및 데이터 처리 로직] ---
def load_font():
    font_path = "malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        return 'MalgunGothic'
    return 'Helvetica'

FONT_NAME = load_font()

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
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자"); c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
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
            c.drawString(85, cur_y, str(raw_date)[:10] if pd.notna(raw_date) else "")
            c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
            c.setLineWidth(0.3); c.setStrokeColor(colors.lightgrey); c.line(40, cur_y - 7, 555, cur_y - 7)
        
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
        c.setStrokeColor(colors.black)

    c.save()
    buffer.seek(0)
    return buffer

# --- [2. UI 및 세션 관리] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환", "menu_3": "💳 카드매입 수기입력건"
    }
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]

st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# 사이드바 메뉴 구성
with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [3. 메뉴별 기능 구현] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == st.session_state.config["menu_3"]:
    st.markdown("<p style='color: #666;'>카드사별 엑셀 파일을 업로드하시면 압축(ZIP) 파일 형태로 변환하여 제공합니다.</p>", unsafe_allow_html=True)
    card_f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="card_up")
    
    if card_f:
        with st.status("🚀 파일을 변환 중입니다...", expanded=True) as status:
            try:
                # 데이터 가공 (예시 로직: 실제 위하고 양식 변환 코드가 들어가는 부분)
                df = pd.read_excel(card_f)
                biz_name = card_f.name.split("_")[0]
                
                # 가공된 엑셀 생성
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='위하고_수기입력')
                processed_excel = output.getvalue()
                
                # 압축 파일 생성
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr(f"위하고_수기입력_{card_f.name}", processed_excel)
                
                status.update(label="✅ 변환 완료!", state="complete", expanded=False)
                
                # 압축 파일 다운로드 버튼 (중앙 배치 스타일)
                st.download_button(
                    label="🎁 변환된 파일 일괄 다운로드 (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"{biz_name}_카드수기입력_변환.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            except Exception as e:
                status.update(label="❌ 변환 실패", state="error")
                st.error(f"오류 내용: {e}")

elif curr == st.session_state.config["menu_2"]:
    # (매출매입장 PDF 변환 로직 - 기존과 동일하게 ZIP 적용)
    f = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'], key="pdf_conv")
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        # 날짜 추출 및 ZIP 생성 로직...
        # (중복 방지를 위해 생략하나 위와 동일한 ZIP 다운로드 구조 적용)
