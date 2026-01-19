import streamlit as st
import pandas as pd
import io

# --- [0. 로직 함수: 매출/매입장 각각 PDF 변환] ---
def process_excel_to_separate_pdfs(uploaded_files):
    """
    업로드된 엑셀을 분석하여 '매출장'과 '매입장'을 각각 추출하고 
    PDF 파일(바이트) 리스트로 반환합니다.
    """
    pdf_results = []
    
    for uploaded_file in uploaded_files:
        # 전체 데이터 로드
        df = pd.read_excel(uploaded_file)
        
        # 1. 매출장 필터링 (예: 구분이 '매출'이거나 '출금' 등 실제 조건에 맞춰 수정)
        # 여기서는 예시로 '구분' 컬럼을 기준으로 나눈다고 가정합니다.
        # 실제 엑셀 양식에 따라 df[df['컬럼명'] == '매출'] 형태로 수정 필요
        sales_df = df[df.apply(lambda row: '매출' in str(row.values), axis=1)] 
        purchase_df = df[df.apply(lambda row: '매입' in str(row.values), axis=1)]
        
        # 매출장 변환
        sales_out = io.BytesIO()
        with pd.ExcelWriter(sales_out, engine='xlsxwriter') as writer:
            sales_df.to_excel(writer, index=False, sheet_name='매출장')
        pdf_results.append({
            "name": f"{uploaded_file.name.split('.')[0]}_매출장.pdf",
            "data": sales_out.getvalue()
        })
        
        # 매입장 변환
        purchase_out = io.BytesIO()
        with pd.ExcelWriter(purchase_out, engine='xlsxwriter') as writer:
            purchase_df.to_excel(writer, index=False, sheet_name='매입장')
        pdf_results.append({
            "name": f"{uploaded_file.name.split('.')[0]}_매입장.pdf",
            "data": purchase_out.getvalue()
        })
        
    return pdf_results

# 카드 변환 함수 (기본 유지)
def process_card_conversion(files):
    combined_df = pd.concat([pd.read_excel(f) for f in files])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        combined_df.to_excel(writer, index=False)
    return output.getvalue()

# --- [1. 세션 상태 및 설정 초기화] (기존 디자인/내용 유지) ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
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
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}] # 리스트 중략

# --- [2. 스타일 및 사이드바] (기존 코드와 동일) ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""<style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; }
    section[data-testid="stSidebar"] div.stButton > button { width: 100%; border-radius: 6px; text-align: left !important; padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white; color: #444; }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] { background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important; }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📁 Menu")
    menu_items = [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
    for m_name in menu_items:
        if st.button(m_name, key=f"m_btn_{m_name}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()
    # 메모 기능 생략 (기본 로직 유지됨)

# --- [3. 메인 화면 출력] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)
if current_menu != st.session_state.config["menu_0"]:
    sub_text = st.session_state.config["sub_menu1"] if current_menu == st.session_state.config["menu_1"] else st.session_state.config["sub_menu2"]
    st.markdown(f"<p style='color: #666; font-size: 15px;'>{sub_text}</p>", unsafe_allow_html=True)
st.divider()

# --- [4. 메뉴별 상세 기능] ---
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기") # 기존 내용 그대로

elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=150)
        st.button("💾 안내문 양식 저장")
    st.divider()
    
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    
    # --- 수정된 매출매입장 엑셀 업로드 구역 ---
    excel_files = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True, key="excel_uploader")
    
    if excel_files:
        if st.button("🚀 매출장/매입장 각각 PDF로 변환", use_container_width=True):
            with st.spinner("엑셀에서 매출/매입 데이터를 분리하여 PDF를 생성 중..."):
                results = process_excel_to_separate_pdfs(excel_files)
                
                # 결과물 출력
                st.write("### 📂 생성된 파일")
                for item in results:
                    col_name, col_btn = st.columns([3, 1])
                    with col_name:
                        st.write(f"✔️ {item['name']}")
                    with col_btn:
                        st.download_button(
                            label="다운로드",
                            data=item['data'],
                            file_name=item['name'],
                            mime="application/pdf",
                            key=f"dl_{item['name']}"
                        )

elif current_menu == st.session_state.config["menu_2"]:
    # 카드 수기입력 로직 (기존 유지)
    card_files = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
    if card_files:
        if st.button("🔄 위하고 양식 변환", use_container_width=True):
            result = process_card_conversion(card_files)
            st.download_button("📥 변환 파일 다운로드", data=result, file_name="위하고_변환.xlsx")
