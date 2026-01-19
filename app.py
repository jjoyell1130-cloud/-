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
    """위하고 양식의 매출/매입장 및 접수증 금액 정밀 추출"""
    data = {"매출액": "0", "매입액": "0", "세액": "0", "결과": "납부"}
    amt_pattern = r"[\d,]{4,15}" 

    for file in files:
        with pdfplumber.open(file) as pdf:
            pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
            full_text_clean = "\n".join(pages).replace(" ", "")
            
            # 1. 신고서/접수증 (세액 추출)
            if any(k in file.name for k in ["신고서", "접수증"]):
                tax_match = re.search(r"(납부할세액|차가감세액|합계세액|세액합계)[:]*([-]*[\d,]+)", full_text_clean)
                if tax_match:
                    raw_amt = tax_match.group(2).replace(",", "")
                    amt = int(raw_amt)
                    data["결과"] = "환급" if "환급" in full_text_clean or amt < 0 else "납부"
                    data["세액"] = f"{abs(amt):,}"

            # 2. 매출장/매입장 (위하고 양식 하단 합계 추출)
            is_sales = "매출" in file.name
            is_purchase = "매입" in file.name
            if (is_sales or is_purchase) and pages:
                last_page_lines = pages[-1].split("\n")
                for line in reversed(last_page_lines):
                    if any(k in line for k in ["합계", "총계", "누계"]):
                        amts = re.findall(amt_pattern, line)
                        if amts:
                            if is_sales: data["매출액"] = amts[0]
                            else: data["매입액"] = amts[0]
                            break
    return data

def make_pdf_stream(data, title, biz_name, date_range):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    rows_per_page = 28
    for i in range(0, len(data), rows_per_page):
        if i > 0: c.showPage()
        c.setFont(FONT_NAME, 16); c.drawCentredString(width/2, height-50, title)
        c.setFont(FONT_NAME, 10); c.drawString(50, height-80, f"업체명: {biz_name} | 기간: {date_range}")
        y = height - 110
        chunk = data.iloc[i:i+rows_per_page]
        for _, row in chunk.iterrows():
            c.setFont(FONT_NAME, 9)
            c.drawString(50, y, str(row.get('거래처', ''))[:20])
            c.drawRightString(400, y, f"{to_int(row.get('공급가액', 0)):,}")
            c.drawRightString(550, y, f"{to_int(row.get('합계', 0)):,}")
            y -= 22
    c.save(); buffer.seek(0)
    return buffer

# --- [2. 세션 및 메뉴 설정] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", "menu_1": "⚖️ 마감작업", "menu_2": "📁 매출매입장 PDF 변환", "menu_3": "💳 카드매입 수기입력건",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}
감기 조심하시고 건강이 최고인거 아시죠? ^.<

부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {매출액}원
-매입장: {매입액}원
-접수증 > {결과}: {세액}원

☆★{결과}예정 8월 말 정도"""
    }
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

# 사이드바 (모든 메뉴 복구)
with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [3. 메뉴별 화면 로직] ---
curr = st.session_state.selected_menu
st.title(curr)

# --- 메뉴 1: 마감작업 ---
if curr == st.session_state.config["menu_1"]:
    st.subheader("📝 완성된 안내문 (복사용)")
    p_h = st.session_state.get("m1_pdf", [])
    p_l = st.session_state.get("m1_ledger", [])
    all_up = (p_h if p_h else []) + (p_l if p_l else [])
    
    if all_up:
        res = extract_data_from_pdf(all_up)
        biz = all_up[0].name.split("_")[0]
        msg = st.session_state.config["prompt_template"].format(
            업체명=biz, 결과=res["결과"], 매출액=res["매출액"], 매입액=res["매입액"], 세액=res["세액"]
        )
        st.code(msg, language="text")
    else:
        st.warning("아래에 PDF를 업로드하면 안내문이 자동 완성됩니다.")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📄 국세청 PDF")
        st.file_uploader("신고서/접수증", type=['pdf'], accept_multiple_files=True, key="m1_pdf")
    with c2:
        st.subheader("📊 매출매입장 PDF")
        st.file_uploader("변환된 PDF", type=['pdf'], accept_multiple_files=True, key="m1_ledger")

    with st.expander("⚙️ 양식 설정"):
        tmp = st.text_area("템플릿 수정", value=st.session_state.config["prompt_template"], height=200)
        if st.button("💾 저장"):
            st.session_state.config["prompt_template"] = tmp
            st.rerun()

# --- 메뉴 2: PDF 변환 ---
elif curr == st.session_state.config["menu_2"]:
    f_up = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'], key="m2_up")
    if f_up:
        df = pd.read_excel(f_up)
        biz = f_up.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형'] if c in df.columns), None)
        if type_col:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                for g in ['매출', '매입']:
                    tgt = df[df[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not tgt.empty:
                        pdf = make_pdf_stream(tgt, f"{g} 장", biz, "2025년")
                        zf.writestr(f"{biz}_{g}장.pdf", pdf.getvalue())
            st.download_button("🎁 PDF 일괄 다운로드 (ZIP)", data=zip_buf.getvalue(), file_name=f"{biz}_PDF변환.zip")

# --- 메뉴 3: 카드 분리 ---
elif curr == st.session_state.config["menu_3"]:
    card_up = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="m3_up")
    if card_up:
        df_card = pd.read_excel(card_up)
        st.success("카드 데이터 로드 완료. (가공 로직 실행 가능)")

# --- 메뉴 0: Home ---
elif curr == st.session_state.config["menu_0"]:
    st.write("세무 업무 효율화를 위한 통합 관리 시스템입니다. 왼쪽 메뉴를 선택하세요.")
