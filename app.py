import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF
import unicodedata

# --- [1. PDF 변환 클래스] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
        try:
            # 루트 폴더의 malgun.ttf 로드 (한글 깨짐 방지)
            self.add_font('Malgun', '', 'malgun.ttf', unicode=True)
            self.font_name = 'Malgun'
        except:
            self.font_name = 'Arial'

    def header(self):
        self.set_font(self.font_name, '', 20)
        title = unicodedata.normalize('NFC', self.title_text)
        self.cell(0, 15, title, ln=True, align='C')
        self.set_font(self.font_name, '', 11)
        biz = unicodedata.normalize('NFC', f"업체명: {self.biz_name}")
        self.cell(0, 8, biz, ln=False, align='L')
        self.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        self.line(10, 38, 287, 38)
        self.ln(5)

    def draw_table(self, df):
        self.set_font(self.font_name, '', 9)
        if len(df.columns) == 0: return
        col_width = 277 / len(df.columns)
        self.set_fill_color(50, 50, 50); self.set_text_color(255, 255, 255)
        for col in df.columns:
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(col_width, 10, txt, border=1, align='C', fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)
        fill = False
        for _, row in df.iterrows():
            for val in row:
                align = 'R' if isinstance(val, (int, float)) else 'C'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                txt = unicodedata.normalize('NFC', display_val)
                self.cell(col_width, 8, txt, border=1, align=align, fill=fill)
            self.ln()
            fill = not fill

# --- [2. 메뉴 및 세션 초기화] ---
# 메뉴명을 변수로 고정하여 오타나 누락을 방지합니다.
M_HOME = "🏠 Home"
M_FINISH = "⚖️ 마감작업"
M_PDF = "📁 매출매입장 PDF 변환"
M_CARD = "💳 카드매입 수기입력건"

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = M_HOME
if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

# --- [3. 디자인 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""
    <style>
    /* 사이드바 버튼 디자인 조정 */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; border-radius: 6px; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -5px; border: 1px solid #ddd;
        background-color: white; color: #444; height: 2.5rem;
    }
    /* 선택된 활성 메뉴 강조 */
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; color: #1f2937 !important;
        border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바 구성 (줄 위쪽 메뉴 배치)] ---
with st.sidebar:
    st.markdown("### 📂 Menu")
    
    # 순서대로 4개의 메뉴 버튼 생성
    for m in [M_HOME, M_FINISH, M_PDF, M_CARD]:
        is_active = (st.session_state.selected_menu == m)
        if st.button(m, key=f"btn_{m}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()

    # 아래쪽 공백 후 구분선과 메모장 배치
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 📝 Memo")
    memo_text = st.text_area("Memo Content", value=st.session_state.daily_memo, height=250, label_visibility="collapsed")
    if st.button("💾 저장", use_container_width=True):
        st.session_state.daily_memo = memo_text
        st.success("저장되었습니다.")

# --- [5. 메인 화면 기능 로직] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M_HOME:
    st.subheader("🔗 바로가기")
    # 기존 Home 화면 로직 유지

elif curr == M_FINISH:
    st.file_uploader("📄 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)

elif curr == M_PDF:
    st.info("엑셀을 업로드하면 매출/매입장 PDF로 변환합니다.")
    up_excel = st.file_uploader("📊 엑셀 파일 선택", type=['xlsx'], key="pdf_conv_up")
    if up_excel:
        df = pd.read_excel(up_excel)
        biz_name = up_excel.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        
        if type_col:
            st.write(f"📁 업체명: **{biz_name}**")
            c1, c2 = st.columns(2)
            for d_type, col in zip(['매출', '매입'], [c1, c2]):
                with col:
                    st.subheader(f"📈 {d_type}장")
                    sub_df = df[df[type_col].str.contains(d_type, na=False)]
                    if not sub_df.empty:
                        st.dataframe(sub_df, height=300)
                        pdf = SimplePDF(f"{d_type} 장", biz_name)
                        pdf.add_page(); pdf.draw_table(sub_df)
                        st.download_button(f"📥 {d_type} PDF 다운로드", pdf.output(dest='S'), file_name=f"{biz_name}_{d_type}장.pdf")
        else:
            st.error("엑셀에서 '구분' 또는 '유형' 컬럼을 찾을 수 없습니다.")

elif curr == M_CARD:
    st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'])
