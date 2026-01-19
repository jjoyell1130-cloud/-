import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re
import pdfplumber
from datetime import datetime

# --- [1. 데이터 추출 엔진 강화] ---
def extract_data_from_pdf(files):
    """PDF에서 금액을 더 정교하게 추출합니다."""
    data = {"매출액": "0", "매입액": "0", "세액": "0", "결과": "납부"}
    
    # 정규식 패턴: 숫자와 콤마로 이루어진 금액 추출
    amt_pattern = r"[\d,]{3,15}" 

    for file in files:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            clean_text = text.replace(" ", "") # 공백 제거 후 분석
            
            # 1. 신고서/접수증에서 세액 및 결과 추출
            if any(k in file.name for k in ["신고서", "접수증"]):
                # '납부할세액' 또는 '차가감세액' 키워드 뒤의 숫자
                tax_match = re.search(r"(납부할세액|차가감세액|합계)(" + amt_pattern + ")", clean_text)
                if tax_match:
                    amt_str = tax_match.group(2).replace(",", "")
                    amt = int(amt_str)
                    data["결과"] = "환급" if "환급" in clean_text or amt < 0 else "납부"
                    data["세액"] = f"{abs(amt):,}"

            # 2. 매출장/매입장에서 합계액 추출
            if "매출" in file.name:
                # 마지막 페이지 하단에 보통 위치하는 '총계' 또는 '합계' 추출
                sales_match = re.findall(r"(합계|총계|공급가액)(" + amt_pattern + ")", clean_text)
                if sales_match:
                    data["매출액"] = sales_match[-1][1] # 가장 마지막에 나오는 합계 금액 선택
            
            elif "매입" in file.name:
                purchase_match = re.findall(r"(합계|총계|공급가액)(" + amt_pattern + ")", clean_text)
                if purchase_match:
                    data["매입액"] = purchase_match[-1][1]
                    
    return data

# --- [2. 메인 로직 시작] ---
st.title("⚖️ 마감작업 및 안내문 발송")

# --- (A) 최상단: 자동 생성 안내문 ---
st.subheader("📝 완성된 안내문 (복사용)")
if 'config' not in st.session_state:
    st.session_state.config = {"prompt_template": "*{업체명} 부가세 신고현황☆★{결과}..."} # 기본값 생략(이전 코드와 동일)

# 파일 업로드 여부 확인 후 안내문 출력
pdf_hometax = st.session_state.get("m1_pdf", [])
pdf_ledger = st.session_state.get("m1_ledger", [])
all_uploaded = (pdf_hometax if pdf_hometax else []) + (pdf_ledger if pdf_ledger else [])

if all_uploaded:
    extracted = extract_data_from_pdf(all_uploaded)
    biz_name = all_uploaded[0].name.split("_")[0]
    
    # 템플릿 적용
    final_msg = st.session_state.config["prompt_template"].format(
        업체명=biz_name,
        결과=extracted["결과"],
        매출액=extracted["매출액"],
        매입액=extracted["매입액"],
        세액=extracted["세액"]
    )
    st.code(final_msg, language="text")
    st.success("위 문구를 복사하여 업체에 전달하세요.")
else:
    st.warning("아래에서 PDF 파일들을 업로드하면 안내문이 자동으로 작성됩니다.")

st.divider()

# --- (B) 중앙: 파일 업로드 영역 ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📄 국세청 PDF (신고서/접수증)")
    st.file_uploader("파일 업로드", type=['pdf'], accept_multiple_files=True, key="m1_pdf")

with col2:
    st.subheader("📊 매출매입장 PDF")
    st.file_uploader("파일 업로드", type=['pdf'], accept_multiple_files=True, key="m1_ledger")

st.divider()

# --- (C) 하단: 설정 영역 ---
with st.expander("⚙️ 안내문 양식 설정"):
    u_template = st.text_area("양식 수정", value=st.session_state.config.get("prompt_template", ""), height=200)
    if st.button("💾 양식 저장"):
        st.session_state.config["prompt_template"] = u_template
        st.rerun()
