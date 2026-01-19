import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF
import unicodedata
import os

# --- [1. PDF 클래스: 성공했던 양식 로직] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')  # 가로 모드
        self.title_text = title
        self.biz_name = biz
        
        # 폰트 로드: 이미지 파일 목록에 있는 malgun.ttf 우선 사용
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
        # 제목 영역
        self.set_font(self.font_name, '', 20)
        title = unicodedata.normalize('NFC', self.title_text)
        self.cell(0, 15, title, new_x="LMARGIN", new_y="NEXT", align='C')
        
        # 업체명 및 날짜 영역
        self.set_font(self.font_name, '', 11)
        biz = unicodedata.normalize('NFC', f"업체명: {self.biz_name}")
        date_str = f"출력일: {datetime.now().strftime('%Y-%m-%d')}"
        
        self.cell(0, 8, biz, align='L')
        self.set_x(-60)  # 우측 끝으로 이동
        self.cell(0, 8, date_str, new_x="LMARGIN", new_y="NEXT", align='R')
        
        # 구분선
        self.line(10, 38, 287, 38)
        self.ln(5)

    def draw_table(self, df):
        if df.empty: return
        self.set_font(self.font_name, '', 9)
        
        # [성공했던 열 너비 분배] 전체 277mm 기준
        total_w = 277
        num_cols = len(df.columns)
        
        # 특정 컬럼 가중치 부여 (품명/거래처는 넓게, 나머지는 균등)
        col_widths = []
        flexible_cols = []
        fixed_sum = 0
        
        for col in df.columns:
            if '품명' in col or '거래처' in col:
                w = 60
                col_widths.append(w)
                fixed_sum += w
            elif any(x in col for x in ['일자', '구분', '번호']):
                w = 25
                col_widths.append(w)
                fixed_sum += w
            else:
                flexible_cols.append(len(col_widths))
                col_widths.append(0) # 나중에 계산
        
        # 나머지 너비 배분
        if flexible_cols:
            rem_w = (total_w - fixed_sum) / len(flexible_cols)
            for idx in flexible_cols:
                col_widths[idx] = rem_w
        else:
            # 컬럼이 너무 많을 경우 균등 배분
            col_widths = [total_w / num_cols] * num_cols

        # 헤더 출력 (어두운 회색 배경)
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(df.columns):
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(col_widths[i], 10, txt, border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 행 출력
        self.set_text_color(0, 0, 0)
        for _, row in df.iterrows():
            for i, val in enumerate(row):
                # 숫자면 우측 정렬, 문자면 중앙 정렬
                align = 'R' if isinstance(val, (int, float)) else 'C'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                txt = unicodedata.normalize('NFC', display_val)
                
                # 글자가 칸을 넘지 않도록 예외 처리하며 출력
                try:
                    self.cell(col_widths[i], 8, txt, border=1, align=align)
                except:
                    self.cell(col_widths[i], 8, "?", border=1, align=align)
            self.ln()

# --- [2. 세션 상태 및 메뉴 설정] ---
M0, M1, M2, M3 = "🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = M0

# --- [3. 사이드바 디자인: 줄 위쪽 메뉴 4개] ---
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
    for m in [M0, M1, M2, M3]:
        is_active = (st.session_state.selected_menu == m)
        if st.button(m, key=f"btn_{m}", type="primary" if is_active else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📝 Memo")
    memo_text = st.text_area("Memo", value=st.session_state.get('memo_data', ''), height=200, label_visibility="collapsed")
    if st.button("💾 저장", use_container_width=True):
        st.session_state['memo_data'] = memo_text
        st.success("저장됨")

# --- [4. 메인 화면 로직] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M2:
    st.info("엑셀을 업로드하면 아까 성공했던 양식 그대로 PDF를 생성합니다.")
    uploaded_file = st.file_uploader("📊 엑셀 파일 선택", type=['xlsx'], key="main_pdf_up")
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file).fillna("") # 빈칸 처리
        biz_name = uploaded_file.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        
        if type_col:
            st.write(f"📁 업체명: **{biz_name}**")
            cols = st.columns(2)
            for i, d_type in enumerate(['매출', '매입']):
                with cols[i]:
                    st.subheader(f"📈 {d_type} 내역")
                    sub_df = df[df[type_col].astype(str).str.contains(d_type, na=False)]
                    if not sub_df.empty:
                        st.dataframe(sub_df, height=300)
                        
                        # PDF 생성 로직
                        pdf = SimplePDF(f"{d_type}장", biz_name)
                        pdf.add_page()
                        pdf.draw_table(sub_df)
                        
                        # 다운로드 버튼
                        st.download_button(
                            label=f"📥 {d_type} PDF 다운로드",
                            data=bytes(pdf.output()),
                            file_name=f"{biz_name}_{d_type}장.pdf",
                            mime="application/pdf",
                            key=f"dl_{d_type}"
                        )
        else:
            st.error("'구분' 컬럼을 찾을 수 없습니다. 엑셀 양식을 확인해주세요.")

elif curr == M0:
    st.write("Home 화면입니다. 사이드바의 메뉴를 이용해주세요.")
