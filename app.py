import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF
import unicodedata

# --- [1. PDF 변환 클래스: 에러 방지 강화] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
        # 폰트 파일이 있는지 확인 후 로드
        try:
            # 루트 폴더의 malgun.ttf 로드 (image_fb19e3.png에서 확인됨)
            self.add_font('Malgun', '', 'malgun.ttf', unicode=True)
            self.font_name = 'Malgun'
        except Exception as e:
            st.error(f"폰트 로드 실패: {e}")
            self.font_name = 'Arial'

    def header(self):
        self.set_font(self.font_name, '', 20)
        # 유니코드 에러 방지를 위해 NFC 정규화 적용
        title = unicodedata.normalize('NFC', self.title_text)
        self.cell(0, 15, title, ln=True, align='C')
        self.set_font(self.font_name, '', 11)
        biz = unicodedata.normalize('NFC', f"업체명: {self.biz_name}")
        self.cell(0, 8, biz, ln=False, align='L')
        self.cell(0, 8, f"출력일: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        self.line(10, 38, 287, 38)
        self.ln(5)

    def draw_table(self, df):
        self.set_font(self.font_name, '', 9)
        if df.empty: return
        
        # 테이블 너비 자동 계산
        col_width = 277 / len(df.columns)
        
        # 헤더 (검정 배경, 흰 글씨)
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        for col in df.columns:
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(col_width, 10, txt, border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 행
        self.set_text_color(0, 0, 0)
        for _, row in df.iterrows():
            for val in row:
                # 숫자와 문자 구분하여 정렬
                align = 'R' if isinstance(val, (int, float)) else 'C'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                txt = unicodedata.normalize('NFC', display_val)
                self.cell(col_width, 8, txt, border=1, align=align)
            self.ln()

# --- [2. 메뉴 정의 및 세션 초기화] ---
M0, M1, M2, M3 = "🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = M0
if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

# --- [3. 사이드바 디자인 (줄 위쪽 4개 메뉴)] ---
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
    # 메뉴 버튼 강제 렌더링
    for m in [M0, M1, M2, M3]:
        if st.button(m, key=f"btn_{m}", type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

    st.markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 📝 Memo")
    memo_val = st.text_area("Memo", value=st.session_state.daily_memo, height=200, label_visibility="collapsed")
    if st.button("💾 저장", use_container_width=True):
        st.session_state.daily_memo = memo_val
        st.success("저장되었습니다.")

# --- [4. 메뉴별 기능] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == M2:
    st.info("매출매입장 엑셀을 업로드하면 PDF로 변환하여 다운로드할 수 있습니다.")
    uploaded_file = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        biz_name = uploaded_file.name.split(" ")[0]
        
        # '구분' 또는 '유형' 컬럼 찾기
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        
        if type_col:
            st.success(f"업체명: {biz_name} 분석 완료")
            c1, c2 = st.columns(2)
            
            for d_type, col in zip(['매출', '매입'], [c1, c2]):
                with col:
                    st.subheader(f"📈 {d_type} 내역")
                    sub_df = df[df[type_col].str.contains(d_type, na=False)]
                    
                    if not sub_df.empty:
                        st.dataframe(sub_df, height=250)
                        # PDF 생성 및 저장
                        pdf = SimplePDF(f"{d_type}장", biz_name)
                        pdf.add_page()
                        pdf.draw_table(sub_df)
                        
                        # PDF 파일 다운로드 버튼
                        st.download_button(
                            label=f"📥 {d_type} PDF 다운로드",
                            data=pdf.output(dest='S'),
                            file_name=f"{biz_name}_{d_type}장.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.warning(f"{d_type} 데이터가 없습니다.")
        else:
            st.error("엑셀 파일에 '구분' 컬럼이 없습니다. 확인해 주세요.")

elif curr == M0:
    st.write("Home 화면입니다. 다른 메뉴를 선택해 주세요.")
# (M1, M3 등 나머지 메뉴 로직은 기존과 동일)
