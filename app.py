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
        self.font_family_name = 'Malgun'
        
        # 폰트 등록
        try:
            self.add_font('Malgun', '', 'malgun.ttf', unicode=True)
        except:
            self.font_family_name = 'Arial' # 실패 시 대비

    def header(self):
        # 헤더 진입 시마다 폰트 재설정 (Encoding 에러 방지)
        self.set_font(self.font_family_name, '', 20)
        
        # 메인 제목 (매 출 장 / 매 입 장)
        self.cell(0, 15, self.report_title, ln=True, align='C')
        
        # 서브 정보
        self.set_font(self.font_family_name, '', 11)
        self.cell(0, 8, f"업체명: {self.biz_name}", ln=False, align='L')
        self.cell(0, 8, f"출력일자: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        self.line(10, 38, 287, 38) 
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_name, '', 9)
        self.cell(0, 10, f'Page {self.page_no()} / {{nb}}', align='C')

    def draw_table(self, df):
        self.set_font(self.font_family_name, '', 9)
        page_width = 277 
        # 열 너비 자동 계산
        if not df.empty:
            col_width = page_width / len(df.columns)
        else:
            return
        
        # 헤더 (어두운 회색)
        self.set_fill_color(50, 50, 50) 
        self.set_text_color(255, 255, 255) 
        for col in df.columns:
            self.cell(col_width, 10, str(col), border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 (검은색)
        self.set_text_color(0, 0, 0) 
        fill = False
        for _, row in df.iterrows():
            for val in row:
                # 숫자 포맷팅 및 정렬
                align = 'R' if isinstance(val, (int, float)) else 'C'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                self.cell(col_width, 8, display_val, border=1, align=align, fill=fill)
            self.ln()
            fill = not fill

# --- [1. 세션 상태 초기화 및 데이터] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}\n\n부가세 신고 마무리되어 전체 자료 전달드립니다.\n\n=첨부파일=\n-부가세 신고서\n-매출장: {매출액}원\n-매입장: {매입액}원\n-접수증 > {결과}: {세액}원"""
    }

if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]
if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""

# --- [2. 메인 UI 디자인] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for m_name in [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]:
        if st.button(m_name, key=f"side_{m_name}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()

# --- [3. 메뉴별 기능] ---

if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.link_button("WEHAGO", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("홈택스", "https://hometax.go.kr/", use_container_width=True)
    
    st.divider()
    st.subheader("⌨️ 차변계정 단축키")
    # 기존에 입력된 데이터가 있으면 사용, 없으면 빈 데이터
    if 'account_data' not in st.session_state:
        st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "매입"}]
    
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장되었습니다.")

elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=150)
        if st.button("💾 안내문 양식 저장"):
            st.session_state.config["prompt_template"] = u_template
            st.success("저장되었습니다.")
    
    st.divider()
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    
    uploaded_file = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        
        # 업체명 추출 로직 강화: 파일명에서 가져오거나 엑셀 내부에서 탐색
        biz_name = uploaded_file.name.split(" ")[0] # 파일명의 첫 단어 (예: 소울인테리어)
        
        # 매출/매입 분류용 컬럼 자동 찾기
        type_col = next((c for c in ['구분', '유형', '매출매입', '거래구분'] if c in df.columns), None)

        if type_col:
            sales_df = df[df[type_col].str.contains('매출', na=False)]
            purchase_df = df[df[type_col].str.contains('매입', na=False)]
            
            st.info(f"📁 대상 업체: **{biz_name}**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 매출장")
                if not sales_df.empty:
                    st.dataframe(sales_df, use_container_width=True)
                    if st.button("📥 매출장 PDF 생성"):
                        pdf = ReportPDF("매 출 장", biz_name)
                        pdf.alias_nb_pages()
                        pdf.add_page()
                        pdf.draw_table(sales_df)
                        st.download_button(f"{biz_name}_매출장.pdf", pdf.output(dest='S'), file_name=f"{biz_name}_매출장_{datetime.now().strftime('%m%d')}.pdf")
                else: st.warning("매출 내역이 없습니다.")

            with col2:
                st.subheader("📉 매입장")
                if not purchase_df.empty:
                    st.dataframe(purchase_df, use_container_width=True)
                    if st.button("📥 매입장 PDF 생성"):
                        pdf = ReportPDF("매 입 장", biz_name)
                        pdf.alias_nb_pages()
                        pdf.add_page()
                        pdf.draw_table(purchase_df)
                        st.download_button(f"{biz_name}_매입장.pdf", pdf.output(dest='S'), file_name=f"{biz_name}_매입장_{datetime.now().strftime('%m%d')}.pdf")
                else: st.warning("매입 내역이 없습니다.")
        else:
            st.error("엑셀에 '구분' 또는 '유형' 컬럼이 없어 매출/매입을 나눌 수 없습니다.")

elif current_menu == st.session_state.config["menu_2"]:
    st.subheader("💳 카드매입 수기입력건")
    st.file_uploader("엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
