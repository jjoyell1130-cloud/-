import streamlit as st
import pdfplumber
import re

# 1. 페이지 설정 및 파일 목록 창 크기 조절 CSS
st.set_page_config(page_title="세무비서 자동화", layout="wide")

# CSS 주입: 업로드된 파일 리스트 영역의 높이를 조절하고 스크롤 생성
st.markdown("""
    <style>
    .st-emotion-cache-1erivf3 { 
        max-height: 200px; 
        overflow-y: auto; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 부가세 신고 안내문 생성기")

# 2. 사이드바 설정
st.sidebar.header("📝 문구 설정")
greeting_text = st.sidebar.text_area("인사말 ( {biz_name} 은 자동으로 바뀝니다 )", 
    value="*2025 {biz_name}-상반기 부가세 신고현황☆★환급\n더위 조심하시고 건강이 최고인거 아시죠? ^.<")

closing_text = st.sidebar.text_area("마무리말", 
    value="혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!\n25일 까지는 수정이 가능합니다!")

def extract_amount(text, keyword):
    lines = text.split('\n')
    for line in lines:
        if keyword in line:
            amounts = re.findall(r'\d{1,3}(?:,\d{3})+', line)
            if amounts:
                return amounts[-1]
    return "0"

# 3. 파일 업로드 섹션
uploaded_files = st.file_uploader("위하고 PDF 파일들을 올려주세요 (여러 개 선택 가능)", accept_multiple_files=True, type=['pdf'])

if uploaded_files:
    # 업로드된 파일 개수 표시
    st.write(f"✅ 현재 **{len(uploaded_files)}개**의 파일이 선택되었습니다.")
    
    first_file_name = uploaded_files[0].name
    biz_name = first_file_name.split('_')[0] if '_' in first_file_name else "알 수 없음"
    
    m_sales, m_buy, m_refund = "0", "0", "0"

    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf
