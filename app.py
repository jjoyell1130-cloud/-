import streamlit as st
import pandas as pd
import io
import os
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. PDF 변환 및 공통 함수 로직] ---
@st.cache_resource
def load_font():
    font_path = "malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        return 'MalgunGothic'
    return 'Helvetica'

FONT_NAME = load_font()

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

# --- [2. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환", 
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu3": "카드 엑셀을 업로드하면 '공급가액/부가세'를 자동 계산해 ZIP으로 제공합니다."
    }
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]
if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""

# --- [3. UI 스타일 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""<style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    section[data-testid="stSidebar"] div.stButton > button { width: 100%; border-radius: 6px; height: 2.2rem; font-size: 14px; text-align: left !important; padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white; color: #444; }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] { background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important; }
    </style>""", unsafe_allow_html=True)

# --- [4. 사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()
    st.divider()
    memo = st.text_area("Memo", value=st.session_state.daily_memo, height=150)
    if st.button("💾 메모 저장"):
        st.session_state.daily_memo = memo
        st.success("저장되었습니다.")

# --- [5. 메인 화면 로직] ---
# 중요: NameError 방지를 위해 curr 변수를 여기서 확실히 정의합니다.
curr = st.session_state.selected_menu
st.title(curr)

if curr == st.session_state.config["menu_3"]:
    st.info(st.session_state.config["sub_menu3"])
    card_f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="card_final_up")
    
    if card_f:
        try:
            # 엑셀 읽기 및 업체명 추출
            df = pd.read_excel(card_f)
            biz_name = card_f.name.split('-')[0].split('_')[0].strip()
            
            # 금액 관련 컬럼 자동 탐색 (카드사별 다양한 명칭 대응)
            amt_col = next((c for c in df.columns if any(k in str(c).replace(" ", "") for k in ['이용금액', '금액', '합계', '승인금액', '국내이용금액'])), None)
            
            if amt_col:
                # 1. 위하고용 공급가액/부가세 계산
                df['합계액'] = df[amt_col].apply(to_int)
                df['공급가액'] = (df['합계액'] / 1.1).round(0).astype(int)
                df['부가세'] = df['합계액'] - df['공급가액']
                
                # 2. ZIP 압축 파일 생성
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    excel_out = io.BytesIO()
                    with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='위하고_수기입력용')
                    zf.writestr(f"위하고_변환_{card_f.name}", excel_out.getvalue())
                
                # 3. 결과 출력 및 다운로드 버튼
                st.success(f"✅ {biz_name} 업체 카드 내역 변환 완료! (감지된 컬럼: {amt_col})")
                
                st.download_button(
                    label="🎁 위하고 변환파일 일괄 다운로드 (ZIP)",
                    data=zip_buf.getvalue(),
                    file_name=f"{biz_name}_위하고_카드수기입력.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                
                st.markdown("##### 🔍 가공 데이터 미리보기")
                st.dataframe(df[['공급가액', '부가세', '합계액']].head(), use_container_width=True)
            else:
                # 금액 컬럼을 찾지 못했을 때
                st.error("❌ 엑셀에서 금액 관련 컬럼을 찾을 수 없습니다.")
                st.warning("팁: 엑셀 파일의 금액 열 제목을 '금액' 또는 '이용금액'으로 수정하고 다시 업로드해 보세요.")
        except Exception as e:
            st.error(f"❌ 처리 중 오류 발생: {e}")

elif curr == st.session_state.config["menu_2"]:
    st.info("📊 매출매입장 엑셀을 업로드하면 PDF 장부로 변환하여 ZIP으로 제공합니다.")
    # (매출매입장 PDF 변환 로직도 동일한 ZIP 구조로 동작 가능)
