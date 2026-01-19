import streamlit as st
import pdfplumber
import re

# 1. 페이지 설정
st.set_page_config(page_title="세무비서 자동화", layout="wide")
st.title("📊 부가세 신고 안내문 생성기")

# 2. 사이드바 설정 (인사말/마무리말)
st.sidebar.header("📝 문구 설정")
greeting_text = st.sidebar.text_area("인사말 ( {biz_name} 은 자동으로 바뀝니다 )", 
    value="*2025 {biz_name}-상반기 부가세 신고현황☆★환급\n더위 조심하시고 건강이 최고인거 아시죠? ^.<")

closing_text = st.sidebar.text_area("마무리말", 
    value="혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!\n25일 까지는 수정이 가능합니다!")

def extract_amount(text, keyword):
    """특정 키워드 옆의 금액(숫자와 콤마)을 찾아주는 함수"""
    lines = text.split('\n')
    for line in lines:
        if keyword in line:
            amounts = re.findall(r'\d{1,3}(?:,\d{3})+', line)
            if amounts:
                return amounts[-1]
    return "0"

# 3. 파일 업로드 섹션
uploaded_files = st.file_uploader("위하고 PDF 파일들을 올려주세요", accept_multiple_files=True, type=['pdf'])

if uploaded_files:
    # 업체명 추출 (첫 번째 파일명 기준)
    first_file_name = uploaded_files[0].name
    biz_name = first_file_name.split('_')[0] if '_' in first_file_name else "알 수 없음"
    
    # 데이터 저장용 변수 초기화
    m_sales = "0"
    m_buy = "0"
    m_refund = "0"

    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            
            fname = file.name
            if "매출장" in fname:
                m_sales = extract_amount(text, "누계")
            elif "매입장" in fname:
                m_buy = extract_amount(text, "누계매입")
            elif "접수증" in fname or "신고서" in fname:
                m_refund = extract_amount(text, "차가감납부할세액")
