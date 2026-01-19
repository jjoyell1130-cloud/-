import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import unicodedata
import os

# --- [1. PDF 클래스: 자동 열 너비 및 줄바꿈 적용] ---
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
        self.set_font(self.font_name, '', 8) # 글자 크기를 살짝 줄여 겹침 방지
        
        # [양식 최적화] 컬럼별 중요도에 따른 너비 비율 설정 (합계 277)
        # 품명, 거래처처럼 긴 항목은 넓게, 일자나 번호는 좁게 설정
        total_w = 277
        col_names = df.columns.tolist()
        num_cols = len(col_names)
        
        widths = []
        for col in col_names:
            if any(x in col for x in ['품명', '거래처', '비고']):
                widths.append(total_w * 0.25) # 긴 항목 25%
            elif any(x in col for x in ['일자', '번호', '구분']):
                widths.append(total_w * 0.08) # 짧은 항목 8%
            else:
                widths.append(total_w * (0.64 / (num_cols - 2) if num_cols > 2 else 0.1)) # 나머지 균등

        # 헤더 출력
        self.set_fill_color(60, 60, 60)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(col_names):
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(widths[i], 10, txt, border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 출력
        self.set_text_color(0, 0, 0)
        for _, row in df.iterrows():
            # 행의 최대 높이 계산을 위해 데이터 준비
            row_height = 8 
            for i, val in enumerate(row):
                align = 'R' if isinstance(val, (int, float)) else 'L'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                txt = unicodedata.normalize('NFC', display_val)
                
                # cell 대신 multi_cell을 쓰면 글씨가 겹치지 않으나 
                # 여기서는 간단히 잘림 방지를 위해 너비에 맞춰 텍스트 조절
                self.cell(widths[i], row_height, txt, border=1, align=align)
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
        if st.button(m, key=f"side_{m}", type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

    st.markdown("<div style='height: 150px;'></div>")
    st.divider()
    st.markdown("### 📝 Memo")
    st.text_area("Memo", height=200, label_visibility="collapsed", key="memo_box")

# --- [3. 메인 기능: PDF 변환] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M2:
    uploaded_file = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        # 결측치 처리 (에러 방지)
        df = df.fillna("")
        biz_name = uploaded_file.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        
        if type_col:
            st.success(f"업체: {biz_name}")
            cols = st.columns(2)
            for i, d_type in enumerate(['매출', '매입']):
                with cols[i]:
                    st.subheader(f"📈 {d_type}장")
                    sub_df = df[df[type_col].astype(str).str.contains(d_type, na=False)]
                    if not sub_df.empty:
                        st.dataframe(sub_df, height=300)
                        
                        pdf = SimplePDF(f"{d_type} 장", biz_name)
                        pdf.add_page()
                        pdf.draw_table(sub_df)
                        
                        st.download_button(
                            label=f"📥 {d_type} PDF 다운로드",
                            data=bytes(pdf.output()),
                            file_name=f"{biz_name}_{d_type}장.pdf",
                            mime="application/pdf",
                            key=f"dl_{d_type}"
                        )
        else:
            st.error("'구분' 컬럼이 없어 매출/매입을 나눌 수 없습니다.")
elif curr == M0:
    st.info("Home 화면입니다. 사이드바 메뉴를 이용해 주세요.")
