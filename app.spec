import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF
import unicodedata

# --- [PDF 클래스: 한글 인코딩 최적화] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
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

# --- [1. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환", 
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "엑셀을 업로드하면 매출장/매입장 PDF로 변환합니다.",
        "sub_menu3": "카드사별 엑셀 파일을 업로드하시면 전용 파일로 즉시 변환됩니다.",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}\n감기 조심하시고 건강이 최고인거 아시죠? ^.< \n\n부가세 신고 마무리되어 전체 자료 전달드립니다..."""
    }

if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}, {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제유무확인후 분류"}]

def get_processed_excel(file):
    df = pd.read_excel(file)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- [2. 스타일 및 사이드바 (메뉴 위치 수정)] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""<style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; }
    section[data-testid="stSidebar"] div.stButton > button { width: 100%; border-radius: 6px; text-align: left !important; padding-left: 15px !important; margin-bottom: -5px; border: 1px solid #ddd; background-color: white; }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] { background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important; }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📁 Menu")
    
    # [수정] 모든 메뉴 버튼을 구분선(Divider) 위쪽에 배치
    m0 = st.session_state.config["menu_0"]
    m1 = st.session_state.config["menu_1"]
    m2 = st.session_state.config["menu_2"]
    m3 = st.session_state.config["menu_3"]

    if st.button(m0, key="btn_m0", use_container_width=True, type="primary" if st.session_state.selected_menu == m0 else "secondary"):
        st.session_state.selected_menu = m0; st.rerun()
    if st.button(m1, key="btn_m1", use_container_width=True, type="primary" if st.session_state.selected_menu == m1 else "secondary"):
        st.session_state.selected_menu = m1; st.rerun()
    if st.button(m2, key="btn_m2", use_container_width=True, type="primary" if st.session_state.selected_menu == m2 else "secondary"):
        st.session_state.selected_menu = m2; st.rerun()
    if st.button(m3, key="btn_m3", use_container_width=True, type="primary" if st.session_state.selected_menu == m3 else "secondary"):
        st.session_state.selected_menu = m3; st.rerun()

    # 아래쪽으로 밀어내기 및 구분선
    for _ in range(10): st.write("")
    st.divider()
    
    st.markdown("#### 📝 Memo")
    memo_val = st.text_area("Memo", value=st.session_state.daily_memo, height=200, label_visibility="collapsed", key="side_memo")
    if st.button("💾 저장", use_container_width=True, key="memo_save"):
        st.session_state.daily_memo = memo_val; st.success("저장됨")

# --- [3. 메인 화면 로직] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# 메뉴별 서브 텍스트
if current_menu == m1: st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu1']}</p>", unsafe_allow_html=True)
elif current_menu == m2: st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu2']}</p>", unsafe_allow_html=True)
elif current_menu == m3: st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu3']}</p>", unsafe_allow_html=True)
st.divider()

if current_menu == m0:
    st.subheader("⌨️ 차변계정 단축키")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"): st.session_state.account_data = edited.to_dict('records'); st.success("저장완료")

elif current_menu == m1:
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)

elif current_menu == m2:
    excel_up = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'], key="excel_pdf")
    if excel_up:
        df = pd.read_excel(excel_up)
        biz_name = excel_up.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형', '매출매입'] if c in df.columns), None)
        if type_col:
            st.info(f"📁 대상 업체: {biz_name}")
            c1, c2 = st.columns(2)
            for d_type, col in zip(['매출', '매입'], [c1, c2]):
                with col:
                    st.subheader(f"📈 {d_type}장")
                    sub_df = df[df[type_col].str.contains(d_type, na=False)]
                    if not sub_df.empty:
                        st.dataframe(sub_df, height=300)
                        pdf = SimplePDF(f"{d_type} 장", biz_name)
                        pdf.add_page(); pdf.draw_table(sub_df)
                        st.download_button(f"📥 {d_type} PDF 다운로드", pdf.output(dest='S'), file_name=f"{biz_name}_{d_type}장.pdf")

elif current_menu == m3:
    card_up = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="card_up_only")
    if card_up:
        st.download_button("📥 위하고용 다운로드", data=get_processed_excel(card_up), file_name=f"위하고_{card_up.name}")
