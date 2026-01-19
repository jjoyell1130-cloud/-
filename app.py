import streamlit as st
import pdfplumber
import re

# 1. 페이지 설정
st.set_page_config(page_title="세무비서 자동화", layout="wide")
st.title("📊 부가세 신고 안내문 생성기")

# 2. 사이드바 설정 (인사말/환급안내/마무리말)
st.sidebar.header("📝 문구 설정")
greeting_text = st.sidebar.text_area("1. 인사말", 
    value="*2025 {biz_name}-하반기 부가세 신고현황☆★환급\n감기 조심하시고 건강이 최고인거 아시죠? ^.<")

refund_date = st.sidebar.text_input("2. 환급 예정 시기", value="8월 말 정도")

closing_text = st.sidebar.text_area("3. 마무리말", 
    value="혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!\n25일 까지는 수정이 가능합니다!")

def get_money(text, key):
    for line in text.split('\n'):
        if key in line:
            nums = re.findall(r'\d{1,3}(?:,\d{3})+', line)
            if nums: return nums[-1]
    return "0"

# 3. 파일 업로드
files = st.file_uploader("PDF 파일을 올려주세요", accept_multiple_files=True, type=['pdf'])

if files:
    names = [f.name for f in files]
    st.info(f"📁 총 {len(names)}개의 파일이 로드되었습니다.")
    
    # 업체명 추출
    first_name = names[0]
    biz_name = first_name.split('_')[0] if '_' in first_name else "알 수 없음"
    m_sales, m_buy, m_refund = "0", "0", "0"

    for f in files:
        with pdfplumber.open(f) as pdf:
            txt = ""
            for pg in pdf.pages:
                tmp = pg.extract_text()
                if tmp: txt += tmp
            
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
    
    final_msg = f"{hi}\n\n"
    final_msg += "부가세 신고 마무리되어 전체 자료 전달드립니다.\n\n"
    final_msg += "=첨부파일=\n"
    final_msg += "-부가세 신고서\n"
    final_msg += f"-매출장: {m_sales}원\n"
    final_msg += f"-매입장: {m_buy}원\n"
    final_msg += f"-접수증 > 환급: {m_refund}원\n\n"
    final_msg += f"☆★환급예정 {refund_date}\n\n" # 이 부분이 왼쪽 입력값으로 바뀝니다
    final_msg += closing_text

    st.success(f"✅ {biz_name} 분석 완료!")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("📋 최종 안내문 (카톡용)")
        st.text_area("내용을 복사해서 사용하세요", final_msg, height=450)
    with c2:
        st.subheader("📁 업로드 확인")
        for n in names: st.write(f"✔️ {n}")
else:
    st.info("위하고에서 받은 PDF 파일들을 올려주세요.")
