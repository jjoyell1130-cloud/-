import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF

# --- [PDF 서식 최적화 클래스] ---
class ReportPDF(FPDF):
    def __init__(self, title_name, biz_name):
        super().__init__(orientation='L') 
        self.report_title = title_name
        self.biz_name = biz_name
        # 폰트 등록 시도
        try:
            self.add_font('Nanum', '', 'NanumGothic.ttf', unicode=True)
            self.font_name = 'Nanum'
        except:
            self.font_name = 'Arial'

    def header(self):
        self.set_font(self.font_name, '', 16 if self.font_name == 'Nanum' else 14)
        self.cell(0, 15, self.report_title, ln=True, align='C')
        self.set_font(self.font_name, '', 10)
        self.cell(0, 8, f"업체명: {self.biz_name} | 출력일자: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        self.line(10, 35, 287, 35) 
        self.ln(5)

    def draw_table(self, df):
        self.set_font(self.font_name, '', 9)
        # 컬럼 너비 계산
        col_width = (self.w - 20) / len(df.columns)
        
        # 헤더
        self.set_fill_color(200, 200, 200)
        for col in df.columns:
            # 한글 깨짐 방지를 위해 가공
            txt = str(col).encode('utf-8').decode('utf-8') if self.font_name == 'Nanum' else str(col)
            self.cell(col_width, 10, txt, border=1, align='C', fill=True)
        self.ln()
        
        # 데이터
        for _, row in df.iterrows():
            for val in row:
                txt = str(val).encode('utf-8').decode('utf-8') if self.font_name == 'Nanum' else str(val)
                self.cell(col_width, 8, txt, border=1, align='C')
            self.ln()

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", "menu_1": "⚖️ 마감작업", "menu_2": "💳 카드매입 수기입력건",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}\n부가세 신고 마무리되어 자료 전달드립니다."""
    }
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]
if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무"}]

# --- [2. 스타일 및 사이드바] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for m_name in [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]:
        if st.button(m_name, use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

current_menu = st.session_state.selected_menu
st.title(current_menu)

# --- [3. 메뉴별 기능] ---
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("⌨️ 차변계정 단축키")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장되었습니다.")

elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=150)
    
    st.divider()
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    
    uploaded_file = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        # 구분 컬럼 감지 (매출/매입 분류용)
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        biz_col = next((c for c in ['상호', '업체명', '거래처'] if c in df.columns), df.columns[0])
        biz_name = str(df[biz_col].iloc[0])

        if type_col:
            sales_df = df[df[type_col].str.contains('매출', na=False)]
            purchase_df = df[df[type_col].str.contains('매입', na=False)]
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📈 매출장")
                if not sales_df.empty:
                    pdf = ReportPDF("SALES REPORT", biz_name)
                    pdf.add_page()
                    pdf.draw_table(sales_df)
                    # 바이너리로 변환하여 다운로드
                    pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
                    st.download_button("📥 매출장 PDF 다운로드", pdf_bytes, f"sales_{biz_name}.pdf", "application/pdf")
            with c2:
                st.subheader("📉 매입장")
                if not purchase_df.empty:
                    pdf = ReportPDF("PURCHASE REPORT", biz_name)
                    pdf.add_page()
                    pdf.draw_table(purchase_df)
                    pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
                    st.download_button("📥 매입장 PDF 다운로드", pdf_bytes, f"purchase_{biz_name}.pdf", "application/pdf")
