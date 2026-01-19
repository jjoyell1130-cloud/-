import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF
import unicodedata
import os

# --- [1. PDF 클래스: 최신 fpdf2 문법 적용] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
        
        # 폰트 로드: unicode=True 인수를 제거하고 최신 방식으로 등록
        font_path = "malgun.ttf"
        if os.path.exists(font_path):
            try:
                # 최신 fpdf2는 unicode=True 없이도 ttf를 지원합니다.
                self.add_font('Malgun', '', font_path)
                self.font_name = 'Malgun'
            except:
                self.font_name = 'Courier' # 최악의 경우 기본 폰트
        else:
            self.font_name = 'Courier'

    def header(self):
        self.set_font(self.font_name, '', 20)
        # 한글 깨짐 방지 정규화
        title = unicodedata.normalize('NFC', self.title_text)
        self.cell(0, 15, title, new_x="LMARGIN", new_y="NEXT", align='C')
        
        self.set_font(self.font_name, '', 11)
        biz = unicodedata.normalize('NFC', f"업체명: {self.biz_name}")
        date_str = f"출력일: {datetime.now().strftime('%Y-%m-%d')}"
        
        self.cell(0, 8, biz, align='L')
        self.set_x(-50) # 날짜 위치 조정
        self.cell(0, 8, date_str, new_x="LMARGIN", new_y="NEXT", align='R')
        self.line(10, 38, 287, 38)
        self.ln(5)

    def draw_table(self, df):
        self.set_font(self.font_name, '', 9)
        if df.empty: return
        
        col_width = 277 / len(df.columns)
        
        # 헤더
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        for col in df.columns:
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(col_width, 10, txt, border=1, align='C', fill=True)
        self.ln()
        
        # 데이터
        self.set_text_color(0, 0, 0)
        for _, row in df.iterrows():
            for val in row:
                align = 'R' if isinstance(val, (int, float)) else 'C'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                txt = unicodedata.normalize('NFC', display_val)
                # 에러 발생 시 해당 칸만 공백 처리하여 중단 방지
                try:
                    self.cell(col_width, 8, txt, border=1, align=align)
                except:
                    self.cell(col_width, 8, "", border=1, align=align)
            self.ln()

# --- [2. 사이드바 및 메뉴 (4개 고정)] ---
M0, M1, M2, M3 = "🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = M0

st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# 사이드바 디자인
st.markdown("""
    <style>
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; border-radius: 6px; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -5px; border: 1px solid #ddd;
        background-color: white; color: #444; height: 2.5rem;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; color: #1f2937 !important;
        border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📂 Menu")
    for m in [M0, M1, M2, M3]:
        if st.button(m, key=f"btn_{m}", type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()
    
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📝 Memo")
    memo = st.text_area("Memo", height=200, label_visibility="collapsed", key="side_memo")

# --- [3. 메인 기능: PDF 변환] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M2:
    uploaded_file = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        biz_name = uploaded_file.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        
        if type_col:
            c1, c2 = st.columns(2)
            for d_type, col in zip(['매출', '매입'], [c1, c2]):
                with col:
                    st.subheader(f"📈 {d_type}장")
                    sub_df = df[df[type_col].str.contains(d_type, na=False)]
                    if not sub_df.empty:
                        st.dataframe(sub_df, height=300)
                        pdf = SimplePDF(f"{d_type}장", biz_name)
                        pdf.add_page()
                        pdf.draw_table(sub_df)
                        st.download_button(f"📥 {d_type} PDF 다운로드", pdf.output(), file_name=f"{biz_name}_{d_type}장.pdf")
        else:
            st.error("'구분' 컬럼을 찾을 수 없습니다.")
