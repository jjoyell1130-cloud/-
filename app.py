import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from datetime import datetime

# --- [PDF 생성 클래스 정의] ---
class ReportPDF(FPDF):
    def header(self):
        # 폰트 설정 (한글 폰트 경로가 필요합니다. 예: 'NanumGothic.ttf')
        try:
            self.add_font('Nanum', '', 'NanumGothic.ttf', unicode=True)
            self.set_font('Nanum', '', 16)
        except:
            self.set_font('Arial', 'B', 16)
        
        self.cell(0, 10, self.report_title, ln=True, align='C')
        self.set_font('Nanum' if 'Nanum' in self.fonts else 'Arial', '', 10)
        self.cell(0, 10, f"출력일자: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        self.ln(5)

    def draw_table(self, df):
        # 컬럼 너비 설정
        col_width = self.epw / len(df.columns)
        self.set_fill_color(240, 240, 240)
        
        # 헤더
        for col in df.columns:
            self.cell(col_width, 10, str(col), border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 라인
        self.set_fill_color(255, 255, 255)
        for _, row in df.iterrows():
            for val in row:
                self.cell(col_width, 10, str(val), border=1, align='C')
            self.ln()

# --- [기존 세션 상태 설정 유지] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", "menu_1": "⚖️ 마감작업", "menu_2": "💳 카드매입 수기입력건",
        "prompt_template": "*(업체명) 부가세 신고현황..."
    }
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

# --- [사이드바 및 기본 UI] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for m_name in [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]:
        if st.button(m_name, use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [메인 로직: 마감작업] ---
if st.session_state.selected_menu == st.session_state.config["menu_1"]:
    st.title("⚖️ 마감작업 (매출매입장 PDF 변환)")
    
    uploaded_file = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        
        # 1. 필터링 및 분리 (구분 컬럼이 '매출', '매입' 혹은 '구분'이라고 가정)
        # 엑셀 양식에 따라 '구분' 컬럼명을 수정하세요.
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        biz_name_col = next((c for c in ['상호', '업체명', '거래처'] if c in df.columns), "업체")
        
        if type_col:
            st.success("✅ 데이터를 성공적으로 분석했습니다.")
            
            # 매출/매입 분리
            sales_df = df[df[type_col].str.contains('매출', na=False)]
            purchase_df = df[df[type_col].str.contains('매입', na=False)]
            
            biz_name = df[biz_name_col].iloc[0] if not df.empty else "알수없음"
            today_str = datetime.now().strftime('%Y%m%d')

            col1, col2 = st.columns(2)

            # --- 매출장 PDF 생성 ---
            with col1:
                st.subheader("📈 매출내역")
                st.dataframe(sales_df, use_container_width=True)
                if st.button("📥 매출장 PDF 생성"):
                    pdf = ReportPDF()
                    pdf.report_title = f"[{biz_name}] 매출장"
                    pdf.add_page()
                    pdf.draw_table(sales_df)
                    pdf_output = pdf.output(dest='S')
                    st.download_button(f"{biz_name}_매출장_{today_str}.pdf", pdf_output, file_name=f"{biz_name}_매출장_{today_str}.pdf")

            # --- 매입장 PDF 생성 ---
            with col2:
                st.subheader("📉 매입내역")
                st.dataframe(purchase_df, use_container_width=True)
                if st.button("📥 매입장 PDF 생성"):
                    pdf = ReportPDF()
                    pdf.report_title = f"[{biz_name}] 매입장"
                    pdf.add_page()
                    pdf.draw_table(purchase_df)
                    pdf_output = pdf.output(dest='S')
                    st.download_button(f"{biz_name}_매입장_{today_str}.pdf", pdf_output, file_name=f"{biz_name}_매입장_{today_str}.pdf")
        else:
            st.error("엑셀에서 '구분(매출/매입)' 컬럼을 찾을 수 없습니다.")

else:
    st.write("다른 메뉴를 선택하셨습니다.")
