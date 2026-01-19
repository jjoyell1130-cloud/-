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

# --- [1. PDF 변환 로직 (성공했던 양식)] ---
try:
    pdfmetrics.registerFont(TTFont('MalgunGothic', "malgun.ttf"))
    FONT_NAME = 'MalgunGothic'
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
            c.setLineWidth(1.5)
            c.line(40, yh + 15, 555, yh + 15)
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
            if r is None: return False
            txt = (str(r.get('번호', '')) + str(r.get('거래처', ''))).replace(" ", "")
            return any(k in txt for k in summary_keywords)

        is_curr_summary = check_summary(row)
        c.setFont(FONT_NAME, 8.5)
        
        if is_curr_summary:
            c.setFont(FONT_NAME, 9)
            c.drawString(90, cur_y, str(row.get('거래처', row.get('번호', ''))))
            c.setLineWidth(1.2)
            c.line(40, cur_y + 16, 555, cur_y + 16)
            c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.drawString(45, cur_y, str(actual_item_count))
            c.drawString(85, cur_y, str(row.get('전표일자', '')))
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

# --- [2. 세션 상태 초기화: 메뉴 4개로 확실히 정의] ---
# 메뉴 이름 정의
M0 = "🏠 Home"
M1 = "⚖️ 마감작업"
M2 = "📁 매출매입장 PDF 변환"
M3 = "💳 카드매입 수기입력건"

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = M0

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}]

# --- [3. 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; }
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; border-radius: 6px; height: 2.2rem; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바 구성: 4개 메뉴 버튼] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    # 리스트 순서대로 버튼 생성
    for m in [M0, M1, M2, M3]:
        # 현재 선택된 메뉴면 primary 스타일 적용
        if st.button(m, key=f"menu_btn_{m}", type="primary" if st.session_state.selected_menu == m else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()

    for _ in range(12): st.write("") 
    st.divider()
    st.markdown("#### 📝 Memo")
    memo_val = st.text_area("Memo", value=st.session_state.daily_memo, height=200, label_visibility="collapsed", key="side_memo_box")
    if st.button("💾 저장", use_container_width=True):
        st.session_state.daily_memo = memo_val
        st.success("저장되었습니다.")

# --- [5. 메인 화면 로직] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M0:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    st.divider()
    st.subheader("⌨️ 차변계정 단축키")
    edited_df = st.data_editor(pd.DataFrame(st.session_state.account_data), num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장되었습니다.")

elif curr == M1:
    st.info("국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.")
    # (기존 마감작업 로직...)

elif curr == M2:
    st.markdown("#### 📊 매출매입장 엑셀을 PDF로 변환합니다.")
    f = st.file_uploader("엑셀 파일 선택 (.xlsx)", type=['xlsx'], key="pdf_converter_up")
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        # 날짜 범위 추출
        date_series = df['전표일자'].dropna().astype(str)
        date_range = f"{date_series.min()} ~ {date_series.max()}" if not date_series.empty else "기간 없음"
        
        type_col = next((c for c in ['구분', '유형'] if c in df.columns), None)
        if type_col:
            st.success(f"업체명: {biz_name}")
            col_a, col_b = st.columns(2)
            for i, g in enumerate(['매출', '매입']):
                with [col_a, col_b][i]:
                    st.subheader(f"📈 {g} 내역")
                    target = df[df[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not target.empty:
                        st.dataframe(target, height=300)
                        pdf_stream = make_pdf_stream(target, f"{g} 장", biz_name, date_range)
                        st.download_button(f"📥 {g} PDF 다운로드", pdf_stream, file_name=f"{biz_name}_{g}장.pdf", key=f"dl_btn_{g}")
        else:
            st.error("'구분' 컬럼을 찾을 수 없습니다.")

elif curr == M3:
    st.info("카드사별 엑셀 파일을 업로드하시면 위하고 양식으로 변환됩니다.")
