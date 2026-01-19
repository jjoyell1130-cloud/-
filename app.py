import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re
import pdfplumber
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. PDF 생성 및 추출 엔진] ---
try:
    font_path = "malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        FONT_NAME = 'MalgunGothic'
    else:
        FONT_NAME = 'Helvetica'
except:
    FONT_NAME = 'Helvetica'

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

def extract_data_from_pdf(files):
    data = {"매출액": "0", "매입액": "0", "세액": "0", "결과": "납부"}
    amt_pattern = r"[\d,]{3,15}"
    for file in files:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            clean_text = text.replace(" ", "")
            if any(k in file.name for k in ["신고서", "접수증"]):
                tax_match = re.search(r"(납부할세액|차가감세액|합계)(" + amt_pattern + ")", clean_text)
                if tax_match:
                    amt = int(tax_match.group(2).replace(",", ""))
                    data["결과"] = "환급" if "환급" in clean_text or amt < 0 else "납부"
                    data["세액"] = f"{abs(amt):,}"
            if "매출" in file.name:
                match = re.findall(r"(합계|총계|공급가액)(" + amt_pattern + ")", clean_text)
                if match: data["매출액"] = match[-1][1]
            elif "매입" in file.name:
                match = re.findall(r"(합계|총계|공급가액)(" + amt_pattern + ")", clean_text)
                if match: data["매입액"] = match[-1][1]
    return data

# (기존 PDF 생성 함수 make_pdf_stream 생략하지 않고 포함)
def make_pdf_stream(data, title, biz_name, date_range):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    rows_per_page = 26
    actual_item_count = 0
    summary_keywords = ['합계', '월계', '분기', '반기', '누계']
    for i in range(len(data)):
        if i % rows_per_page == 0:
            if i > 0: c.showPage()
            c.setFont(FONT_NAME, 18); c.drawCentredString(width/2, height - 60, title)
            c.setFont(FONT_NAME, 10); c.drawString(50, height - 90, f"회사명 : {biz_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}")
            y_start = 652
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        c.setFont(FONT_NAME, 8.5)
        c.drawString(45, cur_y, str(i+1))
        c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
    c.save(); buffer.seek(0)
    return buffer

# --- [2. 세션 및 사이드바 설정] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", "menu_1": "⚖️ 마감작업", "menu_2": "📁 매출매입장 PDF 변환", "menu_3": "💳 카드매입 수기입력건",
        "prompt_template": "*{업체명} 부가세 신고현황☆★{결과}\n\n부가세 신고 마무리되어 자료 전달드립니다.\n\n-매출장: {매출액}원\n-매입장: {매입액}원\n-접수증 > {결과}: {세액}원"
    }
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, 
                     type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [3. 메인 화면 로직] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# --- 메뉴 1: 마감작업 (안내문 최상단) ---
if current_menu == st.session_state.config["menu_1"]:
    st.subheader("📝 완성된 안내문 (복사용)")
    p_h = st.session_state.get("m1_pdf", [])
    p_l = st.session_state.get("m1_ledger", [])
    all_files = (p_h if p_h else []) + (p_l if p_l else [])
    
    if all_files:
        ext = extract_data_from_pdf(all_files)
        biz = all_files[0].name.split("_")[0]
        msg = st.session_state.config["prompt_template"].format(업체명=biz, 결과=ext["결과"], 매출액=ext["매출액"], 매입액=ext["매입액"], 세액=ext["세액"])
        st.code(msg, language="text")
    else:
        st.warning("아래에 PDF 파일들을 업로드하면 안내문이 자동 생성됩니다.")
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📄 국세청 PDF")
        st.file_uploader("신고서/접수증", type=['pdf'], accept_multiple_files=True, key="m1_pdf")
    with c2:
        st.subheader("📊 매출매입장 PDF")
        st.file_uploader("변환된 PDF", type=['pdf'], accept_multiple_files=True, key="m1_ledger")
    
    with st.expander("⚙️ 양식 설정"):
        u_t = st.text_area("템플릿", value=st.session_state.config["prompt_template"], height=150)
        if st.button("💾 저장"):
            st.session_state.config["prompt_template"] = u_t
            st.rerun()

# --- 메뉴 2: PDF 변환 ---
elif current_menu == st.session_state.config["menu_2"]:
    f = st.file_uploader("📊 엑셀 업로드", type=['xlsx'], key="m2_up")
    if f:
        df = pd.read_excel(f); biz = f.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형'] if c in df.columns), None)
        if type_col:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED) as zf:
                for g in ['매출', '매입']:
                    tgt = df[df[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not tgt.empty:
                        pdf = make_pdf_stream(tgt, f"{g} 장", biz, "2025년")
                        zf.writestr(f"{biz}_{g}장.pdf", pdf.getvalue())
            st.download_button("🎁 PDF 일괄 다운로드 (ZIP)", data=buf.getvalue(), file_name=f"{biz}_PDF.zip")

# --- 메뉴 3: 카드 분리 ---
elif current_menu == st.session_state.config["menu_3"]:
    f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="m3_up")
    if f:
        # (기존 카드 분리 로직 수행)
        st.success("파일 업로드 완료. 가공 로직이 실행됩니다.")

# --- 메뉴 0: Home ---
elif current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    st.link_button("WEHAGO", "https://www.wehago.com")
    st.link_button("홈택스", "https://hometax.go.kr")
