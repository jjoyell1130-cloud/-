import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re
import pdfplumber  # PDF 텍스트 추출용
from datetime import datetime

# --- [1. 데이터 추출 엔진] ---
def extract_data_from_pdf(files):
    """PDF 파일들에서 매출, 매입, 세액 데이터를 추출합니다."""
    data = {"매출액": "0", "매입액": "0", "세액": "0", "결과": "납부"}
    
    for file in files:
        with pdfplumber.open(file) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text()
            
            # 1. 매출액 추출 (매출장 PDF 또는 신고서)
            sales_match = re.search(r"(매출|공급가액|합계).*?([\d,]{5,15})", full_text)
            if sales_match and "매출" in file.name:
                data["매출액"] = sales_match.group(2)
            
            # 2. 매입액 추출 (매입장 PDF)
            purchase_match = re.search(r"(매입|공급가액|합계).*?([\d,]{5,15})", full_text)
            if purchase_match and "매입" in file.name:
                data["매입액"] = purchase_match.group(2)
                
            # 3. 세액 및 결과 추출 (신고서 PDF)
            tax_match = re.search(r"(차가감.*?세액|납부할.*?세액).*?([\d,]{3,15})", full_text)
            if tax_match:
                amt = tax_match.group(2).replace(",", "")
                if amt.startswith("-") or "환급" in full_text:
                    data["결과"] = "환급"
                    data["세액"] = amt.replace("-", "")
                else:
                    data["결과"] = "납부"
                    data["세액"] = amt
                    
    return data

# --- [2. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}
감기 조심하시고 건강이 최고인거 아시죠? ^.<

부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {매출액}원
-매입장: {매입액}원
-접수증 > {결과}: {세액}원

☆★{결과}예정 8월 말 정도

혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!
25일 까지는 수정이 가능합니다!"""
    }

# --- [3. 메인 화면: 마감작업] ---
st.title("⚖️ 마감작업 (안내문 자동 작성)")

# (1) 안내문구 양식 편집
with st.expander("💬 카톡 안내문 양식 편집", expanded=False):
    u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=250)
    if st.button("💾 안내문 양식 저장"):
        st.session_state.config["prompt_template"] = u_template
        st.success("양식이 저장되었습니다.")

st.divider()

# (2) 파일 업로드 영역
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 국세청 PDF 업로드")
    pdf_hometax = st.file_uploader("국세청 자료 (신고서 등)", type=['pdf'], accept_multiple_files=True, key="m1_pdf")

with col2:
    st.subheader("📊 매출매입장 PDF 업로드")
    pdf_ledger = st.file_uploader("변환된 매출매입장", type=['pdf'], accept_multiple_files=True, key="m1_ledger")

# (3) 안내문 자동 생성 로직
if pdf_hometax or pdf_ledger:
    st.divider()
    st.subheader("📝 자동 생성된 안내문")
    
    # 데이터 추출 진행
    all_files = (pdf_hometax if pdf_hometax else []) + (pdf_ledger if pdf_ledger else [])
    extracted = extract_data_from_pdf(all_files)
    
    # 업체명 추출 (첫 번째 파일명 기준)
    first_file_name = all_files[0].name
    biz_name = first_file_name.split("_")[0] if "_" in first_file_name else "업체명"
    
    # 템플릿 치환
    final_msg = st.session_state.config["prompt_template"].format(
        업체명=biz_name,
        결과=extracted["결과"],
        매출액=extracted["매출액"],
        매입액=extracted["매입액"],
        세액=f"{int(extracted['세액'].replace(',','')):,}" if extracted['세액'] != "0" else "0"
    )
    
    # 결과 출력 및 복사 기능
    st.code(final_msg, language="text")
    st.button("📋 내용 복사하기 (클립보드)", on_click=lambda: st.write("복사 기능은 브라우저 보안 정책에 따라 환경별로 다를 수 있습니다."))
    
    st.info("💡 위 내용은 업로드된 PDF의 숫자를 인식하여 작성되었습니다. 실제 금액과 대조해 보세요.")
