import streamlit as st
import pdfplumber
import re

# 1. 페이지 설정
st.set_page_config(page_title="세무비서 자동화", layout="wide")
st.title("📊 부가세 신고 안내문 생성기")

# 2. 사이드바 설정
st.sidebar.header("📝 문구 설정")
greeting_text = st.sidebar.text_area("인사말", value="*2025 {biz_name}-상반기 부가세 신고현황☆★환급\n더위 조심하세요! ^.<")
closing_text = st.sidebar.text_area("마무릿말", value="궁금한 점은 연락주세요!\n25일까지 수정 가능합니다.")

def get_money(text, key):
    """금액 추출용 간단 함수"""
    for line in text.split('\n'):
        if key in line:
            nums = re.findall(r'\d{1,3}(?:,\d{3})+', line)
            if nums: return nums[-1]
    return "0"

# 3. 파일 업로드
files = st.file_uploader("PDF 파일을 올려주세요", accept_multiple_files=True, type=['pdf'])

if files:
    names = [f.name for f in files]
    st.info(f"📁 총 {len(names)}개 로드됨")
    
    # 업체명 추출
    biz_name = names[0].split('_')[0] if '_' in names[0] else "알 수 없음"
    m_sales, m_buy, m_refund = "0", "0", "0"

    for f in files:
        with pdfplumber.open(f) as pdf:
            txt = ""
            for pg in pdf.pages:
                tmp = pg.extract_text()
                if tmp: txt += tmp
            
            # 파일 종류별 데이터 추출
            nm = f.name
            if "매출장" in nm:
                m_sales = get_money(txt, "누계")
            elif "매입장" in nm:
                m_buy = get_money(txt, "누계매입")
            elif "접수증" in nm or "신고서" in nm:
                res = get_money(txt, "차가감납부할세액")
                if res != "0": m_refund = res

    # 4. 결과 조립
    hi = greeting_text.replace("{biz_name}", biz_name)
    res_text = f"{hi}\n\n매출장: {m_sales}원\n매입장: {m_buy}원\n환급액: {m_refund}원\n\n{closing_text}"

    st.success(f"✅ {biz_name} 분석 완료")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader
