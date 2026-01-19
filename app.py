import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="세무비서 자동화", layout="wide") # 넓게 보기 설정
st.title("📊 부가세 신고 안내문 생성기")

# 사이드바 또는 상단에 설정란 만들기
st.sidebar.header("📝 문구 설정")
greeting = st.sidebar.text_area("인사말", 
    "*2025 {biz_name}-상반기 부가세 신고현황☆★환급\n더위 조심하시고 건강이 최고인거 아시죠? ^.<")

closing = st.sidebar.text_area("마무리말", 
    "혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!\n25일 까지는 수정이 가능합니다!")

def extract_amount(text, keyword):
    lines = text.split('\n')
    for line in lines:
        if keyword in line:
            amounts = re.findall(r'\d{1,3}(?:,\d{3})+', line)
            if amounts:
                return amounts[-1]
    return "0"

uploaded_files = st.file_uploader("위하고 PDF 파일들을 올려주세요", accept_multiple_files=True, type=['pdf'])

if uploaded_files:
    first_file_name = uploaded_files[0].name
    biz_name = first_file_name.split('_')[0] if '_' in first_file_name else "알 수 없음"
    
    report_data = {"매출": "0", "매입": "0", "환급": "0"}

    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            if "매출장" in file.name:
                report_data["매출"] = extract_amount(text, "누계")
            elif "매입장" in file.name:
                report_data["매입"] = extract_amount(text, "누계매입")
            elif "접수증" in file.name or "신고서" in file.name:
                report_data["환급"] = extract_amount(text, "차가감납부할세액")

    # 설정된 문구 적용
    formatted_greeting = greeting.replace("{biz_name}", biz_name)
    
    final_text = f"""{formatted_greeting}

부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {report_data['매출']}원
