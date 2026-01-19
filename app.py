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
        
        # 업로드하신 malgun.ttf 적용
        try:
            self.add_font('Malgun', '', 'malgun.ttf', unicode=True)
            self.font_family = 'Malgun'
        except:
            self.font_family = 'Arial' # 만약의 경우 대비

    def header(self):
        self.set_font(self.font_family, '', 20)
        self.cell(0, 15, self.report_title, ln=True, align='C')
        
        self.set_font(self.font_family, '', 11)
        self.cell(0, 8, f"업체명: {self.biz_name}", ln=False, align='L')
        self.cell(0, 8, f"출력일자: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        self.line(10, 38, 287, 38) 
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family, '', 9)
        self.cell(0, 10, f'Page {self.page_no()} / {{nb}}', align='C')

    def draw_table(self, df):
        self.set_font(self.font_family, '', 9)
        page_width = 277 
        col_widths = [page_width / len(df.columns)] * len(df.columns)
        
        # 헤더 디자인
        self.set_fill_color(50, 50, 50) 
        self.set_text_color(255, 255, 255) 
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], 10, str(col), border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 디자인
        self.set_text_color(0, 0, 0) 
        fill = False
        for _, row in df.iterrows():
            for i, val in enumerate(row):
                align = 'R' if isinstance(val, (int, float)) else 'C'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                self.cell(col_widths[i], 8, display_val, border=1, align=align, fill=fill)
            self.ln()
            fill = not fill

# --- [1. 세션 상태 초기화 및 데이터 복구] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}\n\n부가세 신고 마무리되어 전체 자료 전달드립니다.\n\n=첨부파일=\n-부가세 신고서\n-매출장: {매출액}원\n-매입장: {매입액}원\n-접수증 > {결과}: {세액}원"""
    }

if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]
if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""

# 단축키 리스트 복구 (기존 25개 데이터 유지 권장)
if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "매입"},
        {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "일반"}
        # ... 필요시 추가
    ]

# --- [2. 메인 UI] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for m_name in [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]:
        if st.button(m_name, key=f"side_{m_name}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

current_menu = st.session_state.selected_menu
st.title(current_menu)

# --- [3. 메뉴별 기능] ---

if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    
    st.divider()
    st.subheader("⌨️ 차변계정 단축키")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("데이터가 저장되었습니다.")

elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=150)
        if st.button("💾 안내문 양식 저장"):
            st.session_state.config["prompt_template"] = u_template
            st.success("안내문 양식이 저장되었습니다.")
    
    st.divider()
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    
    uploaded_file = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        biz_col = next((c for c in ['상호', '업체명', '거래처'] if c in df.columns), df.columns[0])
        biz_name = str(df[biz_col].iloc[0])

        if type_col:
            sales_df = df[df[type_col].str.contains('매출', na=False)]
            purchase_df = df[df[type_col].str.contains('매입', na=False)]
            
            st.info(f"📁 대상 업체: {biz_name}")
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("📈 매출장 내역")
                if not sales_df.empty:
                    st.dataframe(sales_df, use_container_width=True)
                    pdf = ReportPDF("매 출 장", biz_name)
                    pdf.alias_nb_pages()
                    pdf.add_page()
                    pdf.draw_table(sales_df)
                    st.download_button("📥 매출장 PDF 다운로드", pdf.output(dest='S'), file_name=f"{biz_name}_매출장_{datetime.now().strftime('%Y%m%d')}.pdf")

            with c2:
                st.subheader("📉 매입장 내역")
                if not purchase_df.empty:
                    st.dataframe(purchase_df, use_container_width=True)
                    pdf = ReportPDF("매 입 장", biz_name)
                    pdf.alias_nb_pages()
                    pdf.add_page()
                    pdf.draw_table(purchase_df)
                    st.download_button("📥 매입장 PDF 다운로드", pdf.output(dest='S'), file_name=f"{biz_name}_매입장_{datetime.now().strftime('%Y%m%d')}.pdf")

elif current_menu == st.session_state.config["menu_2"]:
    st.subheader("💳 카드매입 수기입력건")
    st.file_uploader("카드사 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
