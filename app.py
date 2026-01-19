import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber
from datetime import datetime

# --- [1. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택",
        "menu_1": "⚖️ 매출매입장 PDF & 안내문",
        "menu_2": "💳 카드별 개별 엑셀 변환",
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "PDF와 엑셀을 업로드하면 아래 설정된 프롬프트 양식으로 안내문이 자동 생성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하여 변환을 시작하세요.",
        # [복구] 안내문 자동 완성 프롬프트 양식
        "prompt_template": """*2025 리베르떼-하반기 부가세 신고현황☆★환급
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

if 'account_data' not in st.session_state:
    st.session_state.account_data = [
        {"구분": "차량/교통", "주요 거래처": "유류대", "분류": "공제유무확인", "계정명": "차량유지비", "코드": "822"}
    ]

# --- [2. 유틸리티 함수] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(re.sub(r'[^0-9.-]', '', str(val))))
    except: return 0

# --- [3. 메인 화면 출력 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# --- [4. 사이드바 및 설정창] ---
st.sidebar.title(st.session_state.config["sidebar_title"])
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.pills(label="Menu", options=menu_options, selection_mode="single", default="🏠 홈 (대시보드)")

# 현재 부제목 결정
current_subtitle = st.session_state.config["sub_home"] if selected_menu == "🏠 홈 (대시보드)" else (st.session_state.config["sub_menu1"] if selected_menu == st.session_state.config["menu_1"] else st.session_state.config["sub_menu2"])

with st.sidebar.expander("⚙️ 명칭 및 안내문 프롬프트 수정"):
    st.markdown("### ⚖️ 메뉴 1 안내문 프롬프트 설정")
    st.caption("{매출액}, {매입액}, {결과}, {세액} 변수가 자동으로 치환됩니다.")
    st.session_state.config["prompt_template"] = st.text_area("안내문 양식(프롬프트)", st.session_state.config["prompt_template"], height=300)
    
    st.divider()
    st.session_state.config["sub_menu1"] = st.text_area("메인 화면 상단 설명", st.session_state.config["sub_menu1"])
    
    if st.button("💾 설정 저장"):
        st.rerun()

# --- [5. 메인 화면 레이아웃] ---
st.title(selected_menu)
st.markdown(f"<div style='font-size: 14px; line-height: 1.5; color: #555; text-align: left;'>{current_subtitle}</div>", unsafe_allow_html=True)
st.divider()

# --- [6. 메뉴별 기능] ---
if selected_menu == "🏠 홈 (대시보드)":
    st.subheader("⌨️ 단축키 관리")
    st.data_editor(pd.DataFrame(st.session_state.account_data), num_rows="dynamic", use_container_width=True)

elif selected_menu == st.session_state.config["menu_1"]:
    col1, col2 = st.columns(2)
    with col1:
        tax_pdfs = st.file_uploader("📄 1. 국세청 PDF (접수증/신고서)", type=['pdf'], accept_multiple_files=True)
    with col2:
        excel_ledgers = st.file_uploader("📊 2. 매출매입장 엑셀", type=['xlsx'], accept_multiple_files=True)
    
    if tax_pdfs:
        final_reports = {}
        for f in tax_pdfs:
            with pdfplumber.open(f) as pdf:
                text = "".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                name_match = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", text)
                biz_name = name_match.group(1).strip() if name_match else f.name.replace(".pdf","")
                
                if biz_name not in final_reports: 
                    final_reports[biz_name] = {"매출": 0, "매입": 0, "세액": 0, "결과": "납부"}
                
                # 세액 추출 로직
                vat_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", text)
                if vat_match:
                    val = to_int(vat_match.group(1))
                    final_reports[biz_name]["세액"] = abs(val)
                    final_reports[biz_name]["결과"] = "환급" if "환급" in text or val < 0 else "납부"

        # 결과 출력 및 프롬프트 적용
        for name, data in final_reports.items():
            with st.expander(f"✅ {name} 안내문 자동 생성 결과", expanded=True):
                # 프롬프트 치환 적용
                generated_msg = st.session_state.config["prompt_template"].format(
                    매출액=f"{data['매출']:,}",
                    매입액=f"{data['매입']:,}",
                    결과=data['결과'],
                    세액=f"{data['세액']:,}"
                )
                st.text_area("복사해서 사용하세요", generated_msg, height=250)
                st.button(f"📋 {name} 안내문 복사", on_click=lambda: st.write("클립보드 복사 기능은 브라우저 보안상 직접 복사를 권장합니다."))

elif selected_menu == st.session_state.config["menu_2"]:
    st.info("카드 변환 기능을 이용하려면 파일을 업로드하세요.")
