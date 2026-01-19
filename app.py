import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import unicodedata
import os

# --- [1. PDF 클래스: 성공했던 양식 및 폰트 설정] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
        
        font_path = "malgun.ttf"
        if os.path.exists(font_path):
            try:
                self.add_font('Malgun', '', font_path)
                self.font_name = 'Malgun'
            except:
                self.font_name = 'helvetica'
        else:
            self.font_name = 'helvetica'

    def header(self):
        self.set_font(self.font_name, '', 20)
        title = unicodedata.normalize('NFC', self.title_text)
        self.cell(0, 15, title, new_x="LMARGIN", new_y="NEXT", align='C')
        
        self.set_font(self.font_name, '', 11)
        biz = unicodedata.normalize('NFC', f"업체명: {self.biz_name}")
        date_str = f"출력일: {datetime.now().strftime('%Y-%m-%d')}"
        self.cell(0, 8, biz, align='L')
        self.set_x(-60)
        self.cell(0, 8, date_str, new_x="LMARGIN", new_y="NEXT", align='R')
        self.line(10, 38, 287, 38)
        self.ln(5)

    def draw_table(self, df):
        if df.empty: return
        self.set_font(self.font_name, '', 9)
        
        # [성공했던 열 너비 분배]
        total_w = 277
        # 긴 항목(품명, 거래처)은 넓게, 나머지는 데이터 양에 맞춰 조절
        col_widths = []
        for col in df.columns:
            if any(x in col for x in ['품명', '거래처', '적요']):
                col_widths.append(75)
            elif any(x in col for x in ['일자', '구분', '번호']):
                col_widths.append(25)
            else:
                col_widths.append((total_w - 150 - 75) / (len(df.columns)-3) if len(df.columns) > 3 else 30)

        # 헤더 (어두운 회색)
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(df.columns):
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(col_widths[i], 10, txt, border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 (불필요한 행은 이미 제거됨)
        self.set_text_color(0, 0, 0)
        for _, row in df.iterrows():
            for i, val in enumerate(row):
                align = 'R' if isinstance(val, (int, float)) else 'C'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                txt = unicodedata.normalize('NFC', display_val)
                try:
                    self.cell(col_widths[i], 8, txt, border=1, align=align)
                except:
                    self.cell(col_widths[i], 8, "?", border=1, align=align)
            self.ln()

# --- [2. 세션 및 메뉴 고정 (줄 위 4개)] ---
M_LIST = ["🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"]
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = M_LIST[0]

st.set_page_config(page_title="세무 통합 시스템", layout="wide")
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
    for m in M_LIST:
        if st.button(m, key=f"btn_{m}", type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📝 Memo")
    st.text_area("Memo", height=200, label_visibility="collapsed", key="memo_val")

# --- [3. 메인 로직: 행 필터링 및 PDF 생성] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M_LIST[2]:
    up_file = st.file_uploader("📊 엑셀 파일 선택", type=['xlsx'])
    if up_file:
        df = pd.read_excel(up_file).fillna("")
        biz_name = up_file.name.split(" ")[0]
        
        # [중요] 불필요한 행 제거 (합계, 월계, 누계 등)
        # 모든 컬럼을 검사해서 해당 키워드가 들어있는 행은 삭제합니다.
        exclude_keywords = ['합 계', '월 계', '누 계', '합계', '월계', '누계', '[합 계]', '[월 계]']
        mask = df.apply(lambda row: row.astype(str).str.contains('|'.join(exclude_keywords)).any(), axis=1)
        df = df[~mask]

        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        if type_col:
            st.success(f"필터링 완료: {biz_name}")
            c1, c2 = st.columns(2)
            for i, d_type in enumerate(['매출', '매입']):
                with [c1, c2][i]:
                    st.subheader(f"📈 {d_type} 내역")
                    sub_df = df[df[type_col].astype(str).str.contains(d_type, na=False)]
                    if not sub_df.empty:
                        st.dataframe(sub_df, height=300)
                        pdf = SimplePDF(f"{d_type}장", biz_name)
                        pdf.add_page()
                        pdf.draw_table(sub_df)
                        st.download_button(f"📥 {d_type} PDF 다운로드", bytes(pdf.output()), file_name=f"{biz_name}_{d_type}장.pdf", key=f"dl_{i}")
        else:
            st.error("'구분' 컬럼이 없습니다.")
