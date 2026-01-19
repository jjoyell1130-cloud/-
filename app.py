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

# --- [1. 데이터 추출 엔진: 정밀 보정 버전] ---
def extract_data_from_pdf(files):
    """PDF에서 매출, 매입, 세액 데이터를 추출합니다."""
    data = {"매출액": "0", "매입액": "0", "세액": "0", "결과": "납부"}
    # 금액 패턴: 숫자와 콤마로 이루어진 4자리 이상의 숫자
    amt_pattern = r"[\d,]{4,15}" 

    for file in files:
        with pdfplumber.open(file) as pdf:
            # 모든 페이지 텍스트 추출 (매출/매입장은 마지막 페이지가 중요)
            pages_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
            full_raw_text = "\n".join(pages_text)
            
            # 1. 신고서/접수증 (세액 추출)
            if any(k in file.name for k in ["신고서", "접수증"]):
                clean_text = full_raw_text.replace(" ", "")
                tax_match = re.search(r"(납부할세액|차가감세액|합계세액|세액합계)[:]*([-]*[\d,]+)", clean_text)
                if tax_match:
                    raw_amt = tax_match.group(2).replace(",", "")
                    amt = int(raw_amt)
                    data["결과"] = "환급" if "환급" in clean_text or amt < 0 else "납부"
                    data["세액"] = f"{abs(amt):,}"

            # 2. 매출장/매입장 (정밀 추출 로직)
            is_sales = "매출" in file.name
            is_purchase = "매입" in file.name

            if is_sales or is_purchase:
                # 마지막 페이지에서 '합계' 또는 '총계'가 포함된 라인 찾기
                last_page_text = pages_text[-1] if pages_text else ""
                lines = last_page_text.split("\n")
                
                # '합계' 단어가 들어간 라인들 중 실제 금액이 있는 라인 탐색
                target_line = ""
                for line in reversed(lines):
                    if any(k in line for k in ["합계", "총계", "누계"]):
                        # 숫자가 최소 2개 이상(공급가액, 합계액 등) 있는 라인인지 확인
                        if len(re.findall(amt_pattern, line)) >= 2:
                            target_line = line
                            break
                
                if target_line:
                    # 해당 라인에서 숫자들만 추출
                    amounts = re.findall(amt_pattern, target_line)
                    # 매출/매입장의 합계 라인 구조: [공급가액, 부가세, 합계액] 순서
                    # 사용자가 원하는 값은 대개 '공급가액'이므로 첫 번째 숫자를 가져옴
                    extracted_amt = amounts[0] 
                    
                    if is_sales:
                        data["매출액"] = extracted_amt
                    else:
                        data["매입액"] = extracted_amt
    return data

# --- [2. PDF 생성 및 유틸리티] ---
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
    try: return int(float(str(val).replace(',', '')))
    except: return 0

def make_pdf_stream(data, title, biz_name, date_range):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    rows_per_page = 26
    for i in range(0, len(data), rows_per_page):
        if i > 0: c.showPage()
        c.setFont(FONT_NAME, 18); c.drawCentredString(width/2, height-60, title)
        # ... (이하 PDF 생성 로직 동일)
    c.save(); buffer.seek(0)
    return buffer

# --- [3. 세션 및 레이아웃 설정] ---
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

with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        name = st.session_state.config[k]
        if st.button(name, use_container_width=True, type="primary" if st.session_state.selected_menu == name else "secondary"):
            st.session_state.selected_menu = name
            st.rerun()

# --- [4. 메인 화면: 마감작업] ---
current = st.session_state.selected_menu

if current == st.session_state.config["menu_1"]:
    st.title("⚖️ 마감작업")
    st.subheader("📝 완성된 안내문 (복사용)")
    
    # 세션 상태에서 업로드 파일 가져오기
    p_h = st.session_state.get("m1_pdf")
    p_l = st.session_state.get("m1_ledger")
    all_up = (p_h if p_h else []) + (p_l if p_l else [])
    
    if all_up:
        res = extract_data_from_pdf(all_up)
        # 업체명 추출: 파일명에서 언더바(_) 앞부분
        first_name = all_up[0].name
        biz = first_name.split("_")[0] if "_" in first_name else "업체명"
        
        msg = st.session_state.config["prompt_template"].format(
            업체명=biz, 결과=res["결과"], 매출액=res["매출액"], 매입액=res["매입액"], 세액=res["세액"]
        )
        st.code(msg, language="text")
    else:
        st.warning("아래 PDF 파일들을 업로드하면 안내문이 자동 생성됩니다.")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📄 국세청 PDF")
        st.file_uploader("신고서/접수증 업로드", type=['pdf'], accept_multiple_files=True, key="m1_pdf")
    with c2:
        st.subheader("📊 매출매입장 PDF")
        st.file_uploader("변환된 PDF 업로드", type=['pdf'], accept_multiple_files=True, key="m1_ledger")

    with st.expander("⚙️ 양식 설정"):
        tmp = st.text_area("템플릿 수정", value=st.session_state.config["prompt_template"], height=200)
        if st.button("💾 양식 저장"):
            st.session_state.config["prompt_template"] = tmp
            st.success("양식이 저장되었습니다.")

# --- (Menu 2, 3 로직은 이전과 동일하게 유지) ---
elif current == st.session_state.config["menu_2"]:
    st.title("📁 매출매입장 PDF 변환")
    # ... 이전 코드의 메뉴 2 로직 ...

elif current == st.session_state.config["menu_3"]:
    st.title("💳 카드매입 수기입력건")
    # ... 이전 코드의 메뉴 3 로직 ...
