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

# --- [1. PDF 변환 로직] ---
try:
    font_path = "malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        FONT_NAME = 'MalgunGothic'
    else: FONT_NAME = 'Helvetica'
except: FONT_NAME = 'Helvetica'

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

# --- [2. 세션 및 설정] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환", "menu_3": "💳 카드매입 수기입력건",
        "sub_menu3": "카드사 엑셀을 업로드하면 위하고 양식(공급가/부가세 분리)으로 변환 후 ZIP으로 다운로드합니다."
    }
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]

st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""<style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    section[data-testid="stSidebar"] div.stButton > button { width: 100%; border-radius: 6px; height: 2.2rem; font-size: 14px; text-align: left !important; padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white; color: #444; }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] { background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important; }
    </style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [3. 메뉴별 상세 기능] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == st.session_state.config["menu_3"]:
    st.info(st.session_state.config["sub_menu3"])
    card_f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="card_up")
    
    if card_f:
        df = pd.read_excel(card_f)
        # 위하고 양식 변환 핵심 (공급가/부가세 산출)
        # 보통 '이용금액' 또는 '금액' 컬럼을 기준으로 1.1 나누기 처리
        amt_col = next((c for c in df.columns if '금액' in c or '이용금액' in c or '합계' in c), None)
        
        if amt_col:
            df['합계'] = df[amt_col].apply(to_int)
            df['공급가액'] = (df['합계'] / 1.1).round(0).astype(int)
            df['부가세'] = df['합계'] - df['공급가액']
            
            # ZIP 생성
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                excel_out = io.BytesIO()
                with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='위하고_수기입력용')
                zf.writestr(f"위하고_변환_{card_f.name}", excel_out.getvalue())
            
            st.success("✅ 위하고 업로드용 변환이 완료되었습니다.")
            st.download_button("📥 위하고 변환파일(ZIP) 다운로드", zip_buf.getvalue(), file_name=f"WEHAGO_{card_f.name.split('.')[0]}.zip", use_container_width=True)
        else:
            st.error("엑셀에서 '금액' 관련 컬럼을 찾을 수 없습니다. 컬럼명을 확인해주세요.")

elif curr == st.session_state.config["menu_2"]:
    # 매출매입장 PDF 변환 로직 (ZIP 적용)
    f = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'])
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        # (중략된 PDF 생성 로직 동일하게 적용 가능)
        st.write(f"{biz_name} 분석 중...")
        # ... (생략된 ZIP 생성 로직)
