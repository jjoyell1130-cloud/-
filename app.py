import streamlit as st
import pandas as pd
import io
import os
import zipfile

# --- [1. 금액 처리 및 변환 로직] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

def process_wehago_excel(uploaded_file):
    """카드사 엑셀을 읽어 위하고 양식으로 변환 후 바이너리 반환"""
    df = pd.read_excel(uploaded_file)
    
    # 1. 금액 관련 컬럼 자동 탐색 (카드사별 다양한 명칭 대응)
    possible_amt_cols = ['이용금액', '금액', '합계', '결제금액', '승인금액']
    amt_col = next((c for c in df.columns if any(p in str(c).replace(" ", "") for p in possible_amt_cols)), None)
    
    if amt_col is None:
        return None, "엑셀 파일에서 금액 관련 컬럼을 찾을 수 없습니다."

    # 2. 위하고 업로드용 공급가액/부가세 산출
    df['합계액'] = df[amt_col].apply(to_int)
    df['공급가액'] = (df['합계액'] / 1.1).round(0).astype(int)
    df['부가세'] = df['합계액'] - df['공급가액']
    
    # 3. 엑셀 파일 생성 (메모리 버퍼 사용)
    excel_out = io.BytesIO()
    with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='위하고_수기입력용')
    
    return excel_out.getvalue(), None

# --- [2. UI 및 메인 로직] ---
st.set_page_config(page_title="세무비서 자동화", layout="wide")

# 세션 상태로 현재 메뉴 관리
if 'menu' not in st.session_state:
    st.session_state.menu = "💳 카드매입 수기입력건"

with st.sidebar:
    st.title("📁 메뉴 선택")
    if st.button("💳 카드매입 수기입력건", use_container_width=True):
        st.session_state.menu = "💳 카드매입 수기입력건"
    if st.button("📁 매출매입장 PDF 변환", use_container_width=True):
        st.session_state.menu = "📁 매출매입장 PDF 변환"

curr_menu = st.session_state.menu
st.title(curr_menu)

if curr_menu == "💳 카드매입 수기입력건":
    st.info("카드사별 엑셀 파일을 업로드하시면 위하고(WEHAGO) 수기입력 양식으로 즉시 변환됩니다.")
    
    # 파일 업로드
    uploaded_file = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="card_up")
    
    if uploaded_file:
        # 파일명에서 업체명 추출 (예: '2025 소울인테리어' -> '소울인테리어')
        raw_name = uploaded_file.name.split('.')[0]
        
        # 변환 실행
        excel_data, error_msg = process_wehago_excel(uploaded_file)
        
        if error_msg:
            st.error(error_msg) #
        else:
            # ZIP 압축 파일 생성 (성공했던 방식 유지)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"위하고_변환_{uploaded_file.name}", excel_data)
            
            st.success("✅ 파일 변환이 완료되었습니다.") #
            
            # 다운로드 버튼 (성공했던 ZIP 다운로드 방식)
            st.download_button(
                label="📥 위하고 수기입력용 양식 다운로드 (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"WEHAGO_{raw_name}.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            # 미리보기 화면
            st.markdown("### 🔍 가공 데이터 미리보기 (상위 5건)")
            temp_df = pd.read_excel(io.BytesIO(excel_data))
            st.dataframe(temp_df[['공급가액', '부가세', '합계액']].head(), use_container_width=True)

elif curr_menu == "📁 매출매입장 PDF 변환":
    st.write("기존 PDF 변환 기능을 여기에 유지합니다.")
