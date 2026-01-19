import streamlit as st
import pdfplumber
import re

# 1. 페이지 설정 및 스타일 (파일 목록 한눈에 보기)
st.set_page_config(page_title="세무비서 자동화", layout="wide")

st.markdown("""
    <style>
    /* 업로드된 파일 목록 박스에 스크롤 생성 */
    .st-emotion-cache-1erivf3 { 
        max-height: 250px; 
        overflow-y: auto !important; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 부가세 신고 안내문 생성기")

# 2. 사이드바 설정 (인사말/마무리말)
st.sidebar.header("📝 문구 설정")
greeting_text = st.sidebar.text_area("인사말 ( {biz_name} 자동 치환 )", 
    value="*2025 {biz_name}-상반기 부가세 신고현황☆★환급\n더위 조심하시고 건강이 최고인거 아시죠? ^.<")

closing_text = st.sidebar.text_area("마무리말", 
    value="혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!\n25일 까지는 수정이 가능합니다!")

def extract_amount(text, keyword):
    """키워드 기반 금액 추출 함수"""
    for line in text.split('\n'):
        if keyword in line:
            amounts = re.findall(r'\d{1,3}(?:,\d{3})+', line)
            if amounts:
                return amounts[-1]
    return "0"

# 3. 파일 업로드 섹션
uploaded_files = st.file_uploader("위하고 PDF 파일들을 올려주세요", accept_multiple_files=True, type=['pdf'])

if uploaded_files:
    # 로드된 파일 정보 표시
    file_names = [f.name for f in uploaded_files]
    st.info(f"📁 총 {len(file_names)}개의 파일이 정상적으로 로드되었습니다.")
    
    # 업체명 추출 (첫 번째 파일명 기준)
    biz_name = file_names[0].split('_')[0] if '_' in file_names
