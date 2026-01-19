import streamlit as st
import pdfplumber
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import io
import zipfile

# --- [1. 안전한 폰트 로딩: struct.error 방지] ---
@st.cache_resource
def load_font_safe():
    font_path = "malgun.ttf"
    # 파일이 존재하고 실제 데이터가 있는지 확인
    if os.path.exists(font_path) and os.path.getsize(font_path) > 1024 * 1024:
        try:
            pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
            return 'MalgunGothic'
        except Exception:
            return 'Helvetica' # 에러 시 기본 폰트로 우회
    return 'Helvetica'

FONT_NAME = load_font_safe()

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

# --- [2. 메인 UI 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

# 사이드바 메뉴 구성
with st.sidebar:
    st.title("📁 세무 통합 메뉴")
    menus = ["🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"]
    for m in menus:
        if st.button(m, use_container_width=True, type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

curr = st.session_state.selected_menu
st.title(curr)

# --- [3. 메뉴별 기능 구현] ---

if curr == "💳 카드매입 수기입력건":
    st.info("카드 엑셀을 위하고 양식(공급가/부가세 자동계산)으로 변환하여 ZIP으로 저장합니다.")
    card_f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'])
    
    if card_f:
        try:
            # 엑셀 읽기
            df = pd.read_excel(card_f)
            
            # 금액 관련 컬럼 자동 탐색
            amt_keywords = ['이용금액', '금액', '합계', '승인금액', '결제금액']
            amt_col = next((c for c in df.columns if any(k in str(c).replace(" ", "") for k in amt_keywords)), None)
            
            if amt_col:
                # 엑셀 산출 로직 적용
                df['합계액'] = df[amt_col].apply(to_int)
                # 공급가액 및 부가세 자동 계산
                df['공급가액'] = (df['합계액'] / 1.1).round(0).astype(int)
                df['부가세'] = df['합계액'] - df['공급가액']
                
                # 가공된 데이터를 엑셀로 변환
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='위하고_업로드용')
                
                # ZIP 파일로 압축 (성공했던 방식)
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as zf:
                    zf.writestr(f"위하고_변환_{card_f.name}", excel_buf.getvalue())
                
                st.success(f"✅ '{amt_col}' 컬럼을 기준으로 산출이 완료되었습니다.")
                st.download_button(
                    label="📥 위하고 수기입력용 양식 다운로드 (ZIP)",
                    data=zip_buf.getvalue(),
                    file_name=f"WEHAGO_CARD_{card_f.name.split('.')[0]}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                
                # 산출 결과 미리보기
                st.markdown("### 🔍 산출 결과 미리보기")
                st.dataframe(df[['공급가액', '부가세', '합계액']].head(), use_container_width=True)
            else:
                st.error("엑셀 파일에서 금액 관련 컬럼을 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"산출 중 오류 발생: {e}")

elif curr == "⚖️ 마감작업":
    st.subheader("📊 부가세 신고 안내문 분석")
    uploaded_files = st.file_uploader("위하고 PDF 파일들을 선택하세요", accept_multiple_files=True, type=['pdf'])
    if uploaded_files:
        # 기존 안내문 분석 로직
        st.success("파일 분석 준비 완료")

elif curr == "📁 매출매입장 PDF 변환":
    st.info("엑셀 장부를 PDF로 변환합니다.")
    # 기존 PDF 변환 로직 (메모리 버퍼 방식 유지)
