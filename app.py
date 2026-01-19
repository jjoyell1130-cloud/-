import streamlit as st
import pdfplumber
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import io
import urllib.request
import zipfile
import re

# 1. 폰트 설정 (나눔고딕)
def load_font():
    font_path = "nanum.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except: return False
    try:
        pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        return True
    except: return False

font_status = load_font()
f_name = 'NanumGothic' if font_status else 'Helvetica'

# 2. 유틸리티 함수
def to_int(val):
    try:
        if not val: return 0
        clean_val = re.sub(r'[^0-9-]', '', str(val))
        return int(clean_val) if clean_val else 0
    except: return 0

# 3. PDF 신고서/접수증 분석 함수
def parse_tax_pdf(files):
    data = {}
    for file in files:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            
            # 업체명 추출 (보통 상호 또는 성명 뒤에 나옴)
            name_match = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", text)
            if name_match:
                biz_name = name_match.group(1).strip()
            else:
                biz_name = file.name.split('_')[0]

            if biz_name not in data: data[biz_name] = {"vat": 0, "type": "납부"}

            # 차가감납부할세액 또는 환급받을세액 추출
            # 접수증: "납부할 세액", "환급받을 세액"
            # 신고서: "27. 차가감납부할세액"
            vat_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", text)
            if vat_match:
                val = to_int(vat_match.group(1))
                # '환급' 단어가 포함되어 있으면 음수로 처리
                if "환급" in text and val > 0:
                    data[biz_name]["vat"] = -val
                    data[biz_name]["type"] = "환급"
                else:
                    data[biz_name]["vat"] = val
                    data[biz_name]["type"] = "납부"
    return data

# --- Streamlit UI ---
st.set_page_config(page_title="세무비서 통합 자동화", layout="wide")
st.title("⚖️ 부가세 확정신고 안내 시스템")

# 왼쪽 사이드바: 파일 업로드
with st.sidebar:
    st.header("📁 서류 업로드")
    st.info("먼저 홈택스 PDF를 올린 후, 엑셀 장부를 올리세요.")
    
    # 1. 국세청 PDF 업로드 (신고서, 접수증)
    tax_pdfs = st.file_uploader("1. 국세청 PDF (신고서/접수증)", type=['pdf'], accept_multiple_files=True)
    
    # 2. 엑셀 장부 업로드
    excel_files = st.file_uploader("2. 매출매입장 엑셀", type=['xlsx'], accept_multiple_files=True)

# 데이터 분석
final_reports = {}

# 1단계: PDF 분석 (정확한 세액 확보)
if tax_pdfs:
    final_reports = parse_tax_pdf(tax_pdfs)

# 2단계: 엑셀 분석 (장부 합계 확보)
if excel_files:
    for ex in excel_files:
        df = pd.read_excel(ex)
        df.columns = [c.strip() for c in df.columns]
        name_only = ex.name.split('_')[0]
        
        # PDF 분석 결과가 있으면 그 업체명 사용, 없으면 파일명 사용
        target_name = next((k for k in final_reports.keys() if k in name_only or name_only in k), name_only)
        
        if target_name not in final_reports:
            final_reports[target_name] = {"vat": 0, "type": "미확인"}
            
        sales_sum = to_int(df[df['구분'].str.contains('매출', na=False)]['합계'].sum())
        buys_sum = to_int(df[df['구분'].str.contains('매입', na=False)]['합계'].sum())
        
        final_reports[target_name]["sales"] = sales_sum
        final_reports[target_name]["buys"] = buys_sum

# 메인 화면: 최종 안내문 출력
st.subheader("✉️ 최종 발송용 안내문구")

if final_reports:
    for name, info in final_reports.items():
        with st.expander(f"📌 {name} 최종 안내문", expanded=True):
            sales = info.get("sales", 0)
            buys = info.get("buys", 0)
            vat = info.get("vat", 0)
            
            status_msg = "납부하실 세액" if vat >= 0 else "환급받으실 세액"
            refund_note = "\n☆★ 환급은 8월 말경 등록하신 계좌로 입금될 예정입니다." if vat < 0 else ""
            
            final_msg = f"""안녕하세요, {name} 대표님! 😊
이번 기수 부가가치세 확정 신고가 완료되어 안내드립니다.

✅ 매출 합계(공급대가): {sales:,}원
✅ 매입 합계(공급대가): {buys:,}원

💰 최종 {status_msg}: {abs(vat):,}원
{refund_note}

국세청 신고서와 접수증을 함께 첨부해 드립니다. 
장부 내용과 대조해 보시고 문의사항 있으시면 연락 주세요. 감사합니다!"""
            
            st.text_area("안내문 복사", final_msg, height=220, key=f"final_{name}")
else:
    st.info("왼쪽에서 홈택스 PDF와 엑셀 파일을 모두 업로드하면 최종 안내문이 생성됩니다.")
