import streamlit as st
import pdfplumber

st.set_page_config(page_title="세무비서 자동화", layout="centered")
st.title("📊 부가세 신고 안내문 생성기")
st.write("위하고에서 받은 PDF 파일들을 아래에 올려주세요.")

uploaded_files = st.file_uploader("PDF 파일을 모두 선택하세요", accept_multiple_files=True, type=['pdf'])

if uploaded_files:
    # 1. 업체명 추출 (첫 번째 파일명에서 가져옴)
    first_file_name = uploaded_files[0].name
    biz_name = first_file_name.split('_')[0] if '_' in first_file_name else "알 수 없음"
    
    report_data = {"매출": "0", "매입": "0", "환급": "0"}

    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            # 모든 페이지 텍스트 추출
            text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            
            # 매출액 추출
            if "매출장" in file.name:
                for line in text.split('\n'):
                    if "누계" in line:
                        nums = "".join([c for c in line if c.isdigit() or c == ',']).split(',')
                        if len(nums) >= 2: report_data["매출"] = f"{nums[-2]},{nums[-1]}"
            
            # 매입액 추출
            elif "매입장" in file.name:
                for line in text.split('\n'):
                    if "누계매입" in line:
                        nums = "".join([c for c in line if c.isdigit() or c == ',']).split(',')
                        if len(nums) >= 2: report_data["매입"] = f"{nums[-2]},{nums[-1]}"
            
            # 환급액 추출 (접수증 또는 신고서)
            elif "접수증" in file.name or "신고서" in file.name:
                for line in text.split('\n'):
                    if "차가감납부할세액" in line:
                        report_data["환급"] = "".join([c for c in line if c.isdigit() or c == ','])

    # 2. 결과 리포트 출력
    final_text = f"""=첨부파일=
-부가세 신고서
-매출장: {report_data['매출']}원
-매입장: {report_data['매입']}원
-접수증 > 환급: {report_data['환급']}원
☆★환급예정 8월 말 정도"""

    st.success(f"✅ {biz_name} 업체 분석 완료!")
    st.subheader("📋 생성된 안내문")
    st.text_area("내용을 복사해서 카톡에 붙여넣으세요", final_text, height=200)
    
    st.info("💡 팁: 위 박스 안의 내용을 마우스로 긁어서 복사(Ctrl+C)하세요!")
else:
    st.info("위하고에서 다운로드한 매출장, 매입장, 접수증 PDF를 올려주세요.")
