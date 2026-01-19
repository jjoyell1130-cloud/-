import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import unicodedata

# --- [PDF 클래스: 인코딩 및 한글 최적화] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
        # 맑은 고딕 폰트 적용 (malgun.ttf 파일이 루트 폴더에 있어야 함)
        try:
            self.add_font('Malgun', '', 'malgun.ttf', unicode=True)
            self.font_set = 'Malgun'
        except:
            self.font_set = 'Arial'

    def header(self):
        self.set_font(self.font_set, '', 20)
        # NFC 정규화로 한글 깨짐 방지
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
        
        # 헤더 디자인
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        for col in df.columns:
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(col_width, 10, txt, border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 디자인
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

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환", # 메뉴 신설
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF를 업로드하고 안내문을 작성하는 공간입니다.",
        "sub_menu2": "엑셀을 업로드하면 매출장/매입장 PDF로 변환합니다.",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}\n감기 조심하시고 건강이 최고인거 아시죠? ^.< \n\n부가세 신고 마무리되어 전체 자료 전달드립니다."""
    }

if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]

# 링크 및 단축키 데이터 유지
if 'link_group_2' not in st.session_state:
    st.session_state.link_group_2 = [
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 상반기 자료", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 하반기 자료", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드매입자료", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}, {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제유무확인후 분류"}, {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"}, {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제유무확인후 분류"}, {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"}, {"단축키": "830", "거래처": "홈쇼핑, 인터넷구매", "계정명": "소모품비", "분류": "매입"}, {"단축키": "822", "거래처": "주차장, 적은금액세금", "계정명": "차량유지비", "분류": "일반"}, {"단축키": "-", "거래처": "휴게소", "계정명": "차량/여비교통비", "분류": "공제유무확인후 분류"}, {"단축키": "-", "거래처": "전기요금", "계정명": "전력비", "분류": "매입"}, {"단축키": "-", "거래처": "수도요금", "계정명": "수도광열비", "분류": "일반"}, {"단축키": "814", "거래처": "통신비", "계정명": "통신비", "분류": "매입"}, {"단축키": "-", "거래처": "금융결제원", "계정명": "세금과공과", "분류": "일반"}, {"단축키": "830", "거래처": "약국", "계정명": "소모품비", "분류": "일반"}, {"단축키": "-", "거래처": "모텔", "계정명": "출장비/여비교통비", "분류": "일반"}, {"단축키": "831", "거래처": "캡스, 보안, 홈페이지", "계정명": "지급수수료", "분류": "매입"}, {"단축키": "-", "거래처": "아울렛(작업복)", "계정명": "소모품비", "분류": "매입"}, {"단축키": "820", "거래처": "컴퓨터 AS", "계정명": "수선비", "분류": "매입"}, {"단축키": "830", "거래처": "결제대행업체", "계정명": "소모품비", "분류": "일반"}, {"단축키": "-", "거래처": "신용카드 알림", "계정명": "지급수수료", "분류": "일반"}, {"단축키": "-", "거래처": "휴대폰 소액결제", "계정명": "소모품비", "분류": "일반"}, {"단축키": "146", "거래처": "매입 항목", "계정명": "상품", "분류": "매입"}, {"단축키": "-", "거래처": "병원", "계정명": "복리후생비", "분류": "일반"}, {"단축키": "-", "거래처": "금융결제원", "계정명": "소모품비", "분류": "일반"}, {"단축키": "-", "거래처": "로카모빌리티", "계정명": "소모품비", "분류": "일반"}, {"단축키": "831", "거래처": "소프트웨어 개발/공급", "계정명": "지급수수료", "분류": "지급수수료"}]

# --- [2. 스타일 및 사이드바] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""<style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; }
    section[data-testid="stSidebar"] div.stButton > button { width: 100%; border-radius: 6px; text-align: left !important; padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white; }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] { background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important; }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📁 Menu")
    menu_list = [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"], st.session_state.config["menu_3"]]
    for m_name in menu_list:
        if st.button(m_name, key=f"side_{m_name}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()
    
    for _ in range(12): st.write("")
    st.divider()
    st.markdown("#### 📝 Memo")
    side_memo = st.text_area("Memo Content", value=st.session_state.daily_memo, height=200, label_visibility="collapsed", key="memo_area")
    if st.button("💾 저장", use_container_width=True):
        st.session_state.daily_memo = side_memo
        st.success("저장되었습니다.")

# --- [3. 메인 화면] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# --- HOME ---
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    st.write("")
    c3, c4, c5, c6 = st.columns(4)
    links = st.session_state.link_group_2
    for i, col in enumerate([c3, c4, c5, c6]):
        with col: st.link_button(links[i]["name"], links[i]["url"], use_container_width=True)
    
    st.divider()
    st.subheader("⌨️ 차변계정 단축키")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_editor")
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("데이터가 저장되었습니다.")

# --- 마감작업 ---
elif current_menu == st.session_state.config["menu_1"]:
    st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu1']}</p>", unsafe_allow_html=True)
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=200)
        if st.button("💾 안내문 양식 저장"):
            st.session_state.config["prompt_template"] = u_template
            st.success("저장되었습니다.")
    st.divider()
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)

# --- PDF 변환 (신설 전용 메뉴) ---
elif current_menu == st.session_state.config["menu_2"]:
    st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu2']}</p>", unsafe_allow_html=True)
    uploaded_excel = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'])
    
    if uploaded_excel:
        df = pd.read_excel(uploaded_excel)
        biz_name = uploaded_excel.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        
        if type_col:
            sales_df = df[df[type_col].str.contains('매출', na=False)]
            purchase_df = df[df[type_col].str.contains('매입', na=False)]
            
            st.info(f"📁 대상 업체: {biz_name}")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 매출장")
                if not sales_df.empty:
                    st.dataframe(sales_df, height=300)
                    pdf_s = SimplePDF("매 출 장", biz_name)
                    pdf_s.add_page()
                    pdf_s.draw_table(sales_df)
                    st.download_button("📥 매출 PDF 다운로드", pdf_s.output(dest='S'), file_name=f"{biz_name}_매출장.pdf")
            
            with col2:
                st.subheader("📉 매입장")
                if not purchase_df.empty:
                    st.dataframe(purchase_df, height=300)
                    pdf_p = SimplePDF("매 입 장", biz_name)
                    pdf_p.add_page()
                    pdf_p.draw_table(purchase_df)
                    st.download_button("📥 매입 PDF 다운로드", pdf_p.output(dest='S'), file_name=f"{biz_name}_매입장.pdf")
        else:
            st.error("엑셀에 '구분' 컬럼이 없어 매출/매입을 나눌 수 없습니다.")

# --- 카드 수기입력 ---
elif current_menu == st.session_state.config["menu_3"]:
    st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu2']}</p>", unsafe_allow_html=True)
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
