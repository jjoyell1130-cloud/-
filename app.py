import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF
import unicodedata

# --- [PDF 클래스: 한글 인코딩 및 테이블 최적화] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
        # 이미지 파일 목록에 포함된 malgun.ttf 활용
        try:
            self.add_font('Malgun', '', 'malgun.ttf', unicode=True)
            self.font_set = 'Malgun'
        except:
            self.font_set = 'Arial'

    def header(self):
        self.set_font(self.font_set, '', 20)
        title = unicodedata.normalize('NFC', self.title_text)
        self.cell(0, 15, title, ln=True, align='C')
        self.set_font(self.font_set, '', 11)
        biz = unicodedata.normalize('NFC', f"업체명: {self.biz_name}")
        self.cell(0, 8, biz, ln=False, align='L')
        self.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        self.line(10, 38, 287, 38)
        self.ln(5)

    def draw_table(self, df):
        self.set_font(self.font_set, '', 9)
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

# --- [1. 메뉴 구성 및 세션 초기화] ---
# 사이드바에 나타날 4개의 메뉴를 명확히 정의합니다.
MENU_0 = "🏠 Home"
MENU_1 = "⚖️ 마감작업"
MENU_2 = "📁 매출매입장 PDF 변환"
MENU_3 = "💳 카드매입 수기입력건"
ALL_MENUS = [MENU_0, MENU_1, MENU_2, MENU_3]

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = MENU_0

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

# --- [2. 스타일 설정 (원본 디자인 유지)] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""
    <style>
    /* 사이드바 버튼 정렬 및 디자인 */
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; border-radius: 6px; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -5px; border: 1px solid #ddd;
        background-color: white; color: #444; font-size: 14px; height: 2.2rem;
    }
    /* 활성화된 메뉴 강조 */
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; color: #1f2937 !important;
        border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }
    /* 메인 컨텐츠 좌측 정렬 */
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바 구성: 줄 위쪽에 4개 메뉴 배치] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    
    # 4개의 메뉴를 줄(Divider) 위에 순서대로 생성
    for m in ALL_MENUS:
        is_active = (st.session_state.selected_menu == m)
        if st.button(m, key=f"btn_{m}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.selected_menu = m
            st.rerun()

    # 여백 조절 후 구분선과 메모장 배치
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 📝 Memo")
    memo_input = st.text_area("Memo Content", value=st.session_state.daily_memo, height=250, label_visibility="collapsed", key="side_memo_box")
    if st.button("💾 저장", use_container_width=True, key="memo_save_btn"):
        st.session_state.daily_memo = memo_input
        st.success("저장되었습니다.")

# --- [4. 메인 화면 로직] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == MENU_0:
    st.subheader("🔗 바로가기")
    # (기존 Home 화면의 링크 및 단축키 로직...)
    st.info("Home 화면입니다. 단축키와 링크를 관리하세요.")

elif curr == MENU_1:
    st.markdown("<p style='color: #666;'>국세청 PDF를 업로드하고 안내문을 작성하는 공간입니다.</p>", unsafe_allow_html=True)
    st.file_uploader("📄 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)

elif curr == MENU_2:
    st.markdown("<p style='color: #666;'>엑셀을 업로드하면 매출장/매입장 PDF로 즉시 변환합니다.</p>", unsafe_allow_html=True)
    st.divider()
    
    up_excel = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'], key="pdf_conv_excel")
    if up_excel:
        df = pd.read_excel(up_excel)
        biz_name = up_excel.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        
        if type_col:
            st.info(f"📁 대상 업체: {biz_name}")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 매출장")
                s_df = df[df[type_col].str.contains('매출', na=False)]
                if not s_df.empty:
                    st.dataframe(s_df, height=300)
                    pdf_s = SimplePDF("매 출 장", biz_name)
                    pdf_s.add_page(); pdf_s.draw_table(s_df)
                    st.download_button("📥 매출 PDF 다운로드", pdf_s.output(dest='S'), file_name=f"{biz_name}_매출장.pdf")
            
            with col2:
                st.subheader("📉 매입장")
                p_df = df[df[type_col].str.contains('매입', na=False)]
                if not p_df.empty:
                    st.dataframe(p_df, height=300)
                    pdf_p = SimplePDF("매 입 장", biz_name)
                    pdf_p.add_page(); pdf_p.draw_table(p_df)
                    st.download_button("📥 매입 PDF 다운로드", pdf_p.output(dest='S'), file_name=f"{biz_name}_매입장.pdf")
        else:
            st.error("엑셀에서 '구분' 또는 '유형' 컬럼을 찾을 수 없어 매출/매입을 나눌 수 없습니다.")

elif curr == MENU_3:
    st.markdown("<p style='color: #666;'>카드사 엑셀을 위하고 수기입력 양식으로 변환합니다.</p>", unsafe_allow_html=True)
    st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="card_entry_excel")
