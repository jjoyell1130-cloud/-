import streamlit as st
import pandas as pd
import io

# --- [0. 더미 변환 함수 정의] ---
# 실제 변환 로직을 이 함수 내부에 작성하세요.
def convert_card_data(uploaded_files):
    """카드사 엑셀 -> 위하고 양식 변환"""
    # 예시: 여러 파일을 하나로 합치거나 컬럼명을 변경하는 로직
    combined_df = pd.DataFrame()
    for file in uploaded_files:
        df = pd.read_excel(file)
        # TODO: 위하고 양식에 맞게 df 수정 로직 추가
        combined_df = pd.concat([combined_df, df])
    
    # 엑셀 파일로 변환 (바이트 스트림)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        combined_df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def process_vat_report(pdf_files, excel_files):
    """국세청 PDF/엑셀 분석 -> 안내문 및 결과 파일 생성"""
    # TODO: 데이터 분석 로직 추가
    summary_text = "분석된 결과 요약 메시지입니다."
    
    # 예시 결과 파일 생성
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame([{"내용": "분석완료"}]).to_excel(writer, index=False)
    return summary_text, output.getvalue()

# --- [1. 세션 상태 및 설정 초기화] (기존 코드 유지) ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}\n감기 조심하시고 건강이 최고인거 아시죠? ^.<\n\n부가세 신고 마무리되어 전체 자료 전달드립니다.\n\n=첨부파일=\n-부가세 신고서\n-매출장: {매출액}원\n-매입장: {매입액}원\n-접수증 > {결과}: {세액}원\n\n☆★{결과}예정 8월 말 정도\n\n혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!\n25일 까지는 수정이 가능합니다!"""
    }

if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]
if 'link_group_2' not in st.session_state:
    st.session_state.link_group_2 = [
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 상반기 자료", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 하반기 자료", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드매입자료", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]
if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}] # 간소화

# --- [2. 스타일 및 사이드바] (기존 코드 유지) ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    menu_items = [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
    for m_name in menu_items:
        if st.button(m_name, key=f"m_btn_{m_name}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [3. 메인 화면 출력] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# --- [4. 메뉴별 상세 기능 수정본] ---

# 1) 홈 화면
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    # ... (기존 링크 및 단축키 테이블 코드 동일)

# 2) 마감작업 (PDF/엑셀 -> 안내문 및 변환)
elif current_menu == st.session_state.config["menu_1"]:
    st.info(st.session_state.config["sub_menu1"])
    
    with st.expander("💬 카톡 안내문 양식 편집"):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=150)
        if st.button("💾 양식 저장"):
            st.session_state.config["prompt_template"] = u_template
            st.success("저장되었습니다.")

    col1, col2 = st.columns(2)
    with col1:
        pdf_files = st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    with col2:
        excel_files = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)

    if pdf_files and excel_files:
        if st.button("🚀 데이터 분석 및 결과 생성", use_container_width=True):
            with st.spinner("파일을 분석 중입니다..."):
                # 변환 함수 실행
                summary, result_file = process_vat_report(pdf_files, excel_files)
                
                st.divider()
                st.subheader("✅ 분석 결과")
                st.text_area("생성된 안내문", value=summary, height=200)
                
                st.download_button(
                    label="📥 분석 결과 엑셀 다운로드",
                    data=result_file,
                    file_name="부가세_신고_분석결과.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

# 3) 카드매입 수기입력건 (카드사 엑셀 -> 위하고 양식)
elif current_menu == st.session_state.config["menu_2"]:
    st.info(st.session_state.config["sub_menu2"])
    
    card_files = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)

    if card_files:
        if st.button("🔄 위하고 양식으로 변환하기", use_container_width=True):
            with st.spinner("양식을 변환 중입니다..."):
                # 변환 함수 실행
                converted_data = convert_card_data(card_files)
                
                st.success("변환이 완료되었습니다!")
                st.download_button(
                    label="📥 위하고 수기입력용 파일 다운로드",
                    data=converted_data,
                    file_name="WEHAGO_수기입력_변환파일.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
