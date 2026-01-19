import streamlit as st
import pdfplumber
import re

# 1. 페이지 설정
st.set_page_config(page_title="세무비서 자동화", layout="wide")

st.markdown("""
    <style>
    .st-emotion-cache-1erivf3 { 
        max-height: 180px; 
        overflow-y: auto !important; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 부가세 신고 안내문 생성기")

# 2. 사이드바 설정
st.sidebar.header("📝 문구 설정")
greeting_text = st.sidebar.text_area("인사말 ( {biz_name} 자동 치환 )", 
    value="*2025 {biz_name}-상반기 부가세 신고현황☆★환급\n더위 조심하시고 건강이 최고인거 아시죠? ^.<")

closing_text = st.sidebar.text_area("마무리말", 
    value="혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!\n25일 까지는 수정이 가능합니다!")

def extract_amount(text, keyword):
    """특정 키워드 라인에서 금액 추출"""
    for line in text.split('\n'):
        if keyword in line:
            amounts = re.findall(r'\d{1,3}(?:,\d{3})+', line)
            if amounts:
                return amounts[-1]
    return "0"

# 3. 파일 업로드 섹션
uploaded_files = st.file_uploader("PDF 파일들을 올려주세요", accept_multiple_files=True, type=['pdf'])

if uploaded_files:
    file_names = [f.name for f in uploaded_files]
    st.info(f"📁 총 {len(file_names)}개의 파일이 로드되었습니다.")
    
    # 업체명 추출
    first_name = file_names[0]
    biz_name = first_name.split('_')[0] if '_' in first_name else "알 수 없음"
    
    m_sales, m_buy, m_refund = "0", "0", "0"

    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            full_text = ""
            # 에러 방지를 위해 명확하게 페이지 순회
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    full_text += extracted
            
            fname = file.name
            if "매출장" in fname:
                m_sales = extract_amount(full_text, "누계")
            elif "매입장" in fname:
                m_buy = extract_amount(full_text, "누계매입")
            elif ("
