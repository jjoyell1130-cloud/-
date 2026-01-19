import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="세무비서 자동화", layout="centered")
st.title("📊 부가세 신고 안내문 생성기")

uploaded_files = st.file_uploader("PDF 파일을 모두 선택하세요", accept_multiple_files=True, type=['pdf'])

def extract_amount(text, keyword):
    """특정 키워드 근처에서 금액 형태의 숫자만 추출하는 함수"""
    lines = text.split('\n')
    for line in lines:
        if keyword in line:
            # 숫자와 콤마만 추출
            amounts = re.findall(r'\d{1,3}(?:,\d{3})+', line)
            if amounts:
                return amounts[-1] # 보통 줄의 맨 뒤에 있는 금액이 합계일 확률이 높음
    return "0"

if uploaded_files:
    first_file_name = uploaded_files[0].name
    biz_name = first_file_name.split('_')[0] if '_' in first_file_name else "알 수 없음"
    
    report_data = {"매출": "0", "매입": "0", "환급": "0"}

    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            
            if "매출장" in file.name:
                # '누계' 또는 '합계' 라인에서 금액 추출
                report_data["매출"] = extract_amount(text, "누계")
            
            elif "매입장" in file.name:
                report_data["매입"] = extract_amount(text, "누계매입")
            
            elif "접수증" in file.name or "신고서" in file.name:
                # 차가감납부할세액 옆의 금액만 정확히 추출
                report_data["환급"] = extract_amount(text, "차가감납부할세액")

    final_text = f"""*2025 {biz_name}-상반기 부가세 신고현황☆★환급
더위 조심하시고 건강이 최고인거 아시죠? ^.<
부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {report_data['매출']}원
-매입장: {report_data['매입']}원
-접수증 > 환급: {report_data['환급']}원
☆★환급예정 8월 말 정도

혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!
25일 까지는 수정이 가능합니다!"""

    st.success(f"✅ {biz_name} 업체 분석 완료!")
    st.text_area("내용을 복사해서 카톡에 붙여넣으세요", final_text, height=350)
    st.info("💡 위 박스 안의 내용을 마우스로 긁어서 복사(Ctrl+C)하세요!")
