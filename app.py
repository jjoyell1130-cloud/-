import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF

# --- [PDF 생성을 위한 서식 클래스] ---
class ReportPDF(FPDF):
    def __init__(self, title_name):
        super().__init__()
        self.report_title = title_name

    def header(self):
        # 폰트 설정 (한글 폰트 파일이 폴더에 있어야 함, 없을 시 Arial 대체)
        try:
            self.add_font('Nanum', '', 'NanumGothic.ttf', unicode=True)
            self.set_font('Nanum', '', 16)
        except:
            self.set_font('Arial', 'B', 16)
        
        self.cell(0, 10, self.report_title, ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        try: self.set_font('Nanum', '', 8)
        except: self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def draw_table(self, df):
        # 표 서식 설정
        try: self.set_font('Nanum', '', 9)
        except: self.set_font('Arial', '', 9)
        
        # 컬럼 너비 계산
        page_width = self.w - 20
        col_width = page_width / len(df.columns)
        
        # 헤더 (배경색 있음)
        self.set_fill_color(230, 230, 230)
        for col in df.columns:
            self.cell(col_width, 10, str(col), border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 (테두리 유지)
        self.set_fill_color(255, 255, 255)
        for _, row in df.iterrows():
            for val in row:
                self.cell(col_width, 8, str(val), border=1, align='C')
            self.ln()

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건",
        "sub_menu1": "매출매입장 엑셀을 업로드하면 매출장과 매입장 PDF로 각각 자동 변환됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면 수기입력 양식으로 변환됩니다.",
        "prompt_template": """*{업체명} 부가세 신고현황..."""
    }

if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]
if 'account_data' not in st.session_state: st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}]
if 'link_group_2' not in st.session_state:
    st.session_state.link_group_2 = [
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 상반기 자료", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 하반기 자료", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드매입자료", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

# --- [2. 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""<style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; }
    section[data-testid="stSidebar"] div.stButton > button { width: 100%; border-radius: 6px; text-align: left !important; }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] { background-color: #f0f2f6; color: #1f2937; border: 2px solid #9ca3af; font-weight: 600; }
</style>""", unsafe_allow_html=True)

# --- [사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    for m_name in [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]:
        is_selected = (st.session_state.selected_menu == m_name)
        if st.button(m_name, key=f"m_btn_{m_name}", use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()
    
    for _ in range(15): st.write("")
    st.divider()
    st.markdown("#### 📝 Memo")
    side_memo = st.text_area("Memo Content", value=st.session_state.daily_memo, height=200, label_visibility="collapsed")
    if st.button("💾 저장", use_container_width=True):
        st.session_state.daily_memo = side_memo
        st.success("저장완료")

# --- [3. 메인 화면 출력] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# --- [4. 메뉴별 기능 구현] ---
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
        st.success("데이터 저장됨")

elif current_menu == st.session_state.config["menu_1"]:
    st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu1']}</p>", unsafe_allow_html=True)
    
    # 엑셀 업로드
    uploaded_file = st.file_uploader("📊 매출매입장 엑셀 업로드 (파일 1개당 1개 업체)", type=['xlsx'])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        
        # 업체명 및 분류 컬럼 자동 감지
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        biz_name_col = next((c for c in ['상호', '업체명', '거래처'] if c in df.columns), df.columns[0])
        biz_name = str(df[biz_name_col].iloc[0]) if not df.empty else "업체미상"
        today_str = datetime.now().strftime('%Y%m%d')

        if type_col:
            # 데이터 분리
            sales_df = df[df[type_col].str.contains('매출', na=False)]
            purchase_df = df[df[type_col].str.contains('매입', na=False)]
            
            st.info(f"📍 대상 업체: {biz_name} (매출: {len(sales_df)}건 / 매입: {len(purchase_df)}건)")

            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("📈 매출장")
                if not sales_df.empty:
                    st.dataframe(sales_df, use_container_width=True)
                    pdf = ReportPDF(f"[{biz_name}] 매출장")
                    pdf.add_page()
                    pdf.draw_table(sales_df)
                    st.download_button(
                        label="📥 매출장 PDF 다운로드",
                        data=pdf.output(dest='S').encode('latin-1'),
                        file_name=f"{biz_name}_매출장_{today_str}.pdf",
                        mime="application/pdf"
                    )
                else: st.write("매출 내역이 없습니다.")

            with c2:
                st.subheader("📉 매입장")
                if not purchase_df.empty:
                    st.dataframe(purchase_df, use_container_width=True)
                    pdf = ReportPDF(f"[{biz_name}] 매입장")
                    pdf.add_page()
                    pdf.draw_table(purchase_df)
                    st.download_button(
                        label="📥 매입장 PDF 다운로드",
                        data=pdf.output(dest='S').encode('latin-1'),
                        file_name=f"{biz_name}_매입장_{today_str}.pdf",
                        mime="application/pdf"
                    )
                else: st.write("매입 내역이 없습니다.")
        else:
            st.error("엑셀 파일에 '구분' 또는 '유형' 컬럼이 없어 매출/매입을 나눌 수 없습니다.")

elif current_menu == st.session_state.config["menu_2"]:
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
