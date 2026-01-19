import streamlit as st
import pandas as pd
import io
import os
import zipfile

# --- [1. 공통 유틸리티] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        # 금액에 포함된 콤마(,) 제거 후 정수 변환
        return int(float(str(val).replace(',', '')))
    except: return 0

# --- [2. 세션 및 기본 설정] ---
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "💳 카드매입 수기입력건"

st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# --- [3. 사이드바 메뉴] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    # 사용자가 업로드한 이미지의 메뉴 구성 반영
    menus = ["🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"]
    for m in menus:
        if st.button(m, use_container_width=True, type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

# --- [4. 메인 로직: 카드매입 수기입력건] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == "💳 카드매입 수기입력건":
    st.info("카드사별 엑셀 파일을 업로드하시면 위하고(WEHAGO) 수기입력 양식으로 즉시 변환됩니다.")
    
    # 파일 업로드
    card_f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="card_excel_up")
    
    if card_f:
        try:
            # 1. 데이터 읽기
            df = pd.read_excel(card_f)
            biz_name = card_f.name.split('.')[0]
            
            # 2. 금액 컬럼 자동 찾기
            # 카드사마다 다른 컬럼명(이용금액, 승인금액, 합계 등) 대응
            amt_col = next((c for c in df.columns if any(k in str(c) for k in ['금액', '합계', '이용', '승인'])), None)
            
            if amt_col:
                # 3. 엑셀 변환 작업: 공급가액 및 부가세 산출 
                df['합계액'] = df[amt_col].apply(to_int)
                # 위하고 업로드용 역산 (합계 / 1.1)
                df['공급가액'] = (df['합계액'] / 1.1).round(0).astype(int)
                df['부가세'] = df['합계액'] - df['공급가액']
                
                # 4. 가공된 데이터를 엑셀로 저장하여 ZIP 구성
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    excel_out = io.BytesIO()
                    # 위하고 수기입력 양식 시트로 저장
                    with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='위하고_수기입력용')
                    zf.writestr(f"위하고_변환_{card_f.name}", excel_out.getvalue())
                
                # 5. 다운로드 버튼 제공
                st.success(f"✅ '{amt_col}' 컬럼을 기준으로 변환이 완료되었습니다.")
                st.download_button(
                    label="📥 위하고 수기입력용 양식 다운로드 (ZIP)",
                    data=zip_buf.getvalue(),
                    file_name=f"WEHAGO_CARD_{biz_name}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                
                # 결과 확인용 미리보기
                st.markdown("### 🔍 변환 결과 미리보기 (상위 5건)")
                st.dataframe(df[['공급가액', '부가세', '합계액']].head())
                
            else:
                st.error("엑셀 파일에서 금액 관련 컬럼을 찾을 수 없습니다.")
                
        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

elif curr == "📁 매출매입장 PDF 변환":
    st.write("이 메뉴는 기존처럼 PDF 변환 기능을 수행합니다.")
