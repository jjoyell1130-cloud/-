import streamlit as st
import pdfplumber
import pyautogui
import pyperclip
import time

st.set_page_config(page_title="세무 비서 자동화", layout="wide")
st.title("📊 부가세 신고 안내문 자동 생성기")

# 1. 파일 업로드 섹션
uploaded_files = st.file_uploader("위하고에서 받은 PDF 파일들을 모두 선택하세요", accept_multiple_files=True, type=['pdf'])

report_data = {"매출장": "0", "매입장": "0", "환급액": "0", "업체명": "알 수 없음"}

if uploaded_files:
    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages])
            
            if "매출장" in file.name:
                for line in text.split('\n'):
                    if "누계" in line:
                        nums = "".join([c for c in line if c.isdigit() or c == ',']).split(',')
                        if len(nums) >= 2: report_data["매출장"] = f"{nums[-2]},{nums[-1]}"
            
            elif "매입장" in file.name:
                for line in text.split('\n'):
                    if "누계매입" in line:
                        nums = "".join([c for c in line if c.isdigit() or c == ',']).split(',')
                        if len(nums) >= 2: report_data["매입장"] = f"{nums[-2]},{nums[-1]}"
            
            elif "접수증" in file.name:
                if "리베르떼" in text: report_data["업체명"] = "리베르떼" # 예시용
                for line in text.split('\n'):
                    if "차가감납부할세액" in line:
                        report_data["환급액"] = "".join([c for c in line if c.isdigit() or c == ','])

    # 2. 결과 리포트 생성
    final_text = f"""=첨부파일=
-부가세 신고서
-매출장: {report_data['매출장']}원
-매입장: {report_data['매입장']}원
-접수증 > 환급: {report_data['환급액']}원
☆★환급예정 8월 말 정도"""

    st.subheader(f"🏠 {report_data['업체명']} 안내문 미리보기")
    st.text_area("생성된 문구 (수정 가능)", final_text, height=200)

    # 3. 카카오톡 발송 버튼
    friend_name = st.text_input("카톡 보낼 친구 이름 (정확히 입력)", report_data['업체명'])
    
    if st.button("카카오톡으로 전송 시작"):
        st.warning("⚠️ 5초 뒤에 카톡 전송이 시작됩니다. 카톡 창을 가리지 마세요!")
        time.sleep(5)
        
        # 카톡 조작 로직 (단순화된 예시)
        pyautogui.hotkey('ctrl', 'alt', 'k') # 카톡 단축키로 깨우기
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'f') # 검색창
        pyperclip.copy(friend_name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        pyautogui.press('enter') # 대화방 진입
        time.sleep(1)
        
        pyperclip.copy(final_text)
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.press('enter') # 메시지 전송
        st.success("✅ 전송 완료!")

# 파일명에서 업체명을 추출하는 기능 추가 버전
if uploaded_files:
    # 첫 번째 파일 이름에서 업체명 추출 (예: '리베르떼_488...pdf' -> '리베르떼')
    first_file_name = uploaded_files[0].name
    report_data["업체명"] = first_file_name.split('_')[0] 

    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            # ... (나머지 금액 추출 로직은 동일)