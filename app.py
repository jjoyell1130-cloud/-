import streamlit as st
import pandas as pd
import io
import os
import zipfile
# ... (기존 상단 PDF 로직 및 스타일 설정 생략 - 이전과 동일하게 유지) ...

# --- [카드매입 수기입력건 변환 핵심 함수] ---
def convert_to_wehago_format(df):
    """카드사 엑셀을 위하고 수기입력 양식으로 변환 (공급가/부가세 산출)"""
    # 1. 금액 관련 컬럼 자동 탐색
    possible_cols = ['이용금액', '금액', '합계', '결제금액', '승인금액', '국내이용금액']
    amt_col = None
    for col in df.columns:
        if any(p in str(col).replace(" ", "") for p in possible_cols):
            amt_col = col
            break
    
    if amt_col is None:
        return None, "금액 관련 컬럼을 찾을 수 없습니다."

    # 2. 위하고 양식에 맞게 계산 및 정리
    # 숫자가 아닌 문자(,) 제거 후 정수 변환
    df['total'] = df[amt_col].apply(lambda x: int(float(str(x).replace(',', ''))) if pd.notna(x) else 0)
    
    # 공급가액/부가세 산출 (단수차이는 합계에 맞춤)
    df['공급가액'] = (df['total'] / 1.1).round(0).astype(int)
    df['부가세'] = df['total'] - df['공급가액']
    
    # 위하고 업로드용 핵심 컬럼만 추출 (필요 시 수정 가능)
    # 날짜, 가맹점명, 공급가액, 부가세, 합계 등
    return df, None

# --- [메인 화면 메뉴 3 로직] ---
if curr == st.session_state.config["menu_3"]:
    st.info("💳 카드사 엑셀을 업로드하면 '공급가액'과 '부가세'를 분리하여 위하고 양식으로 변환합니다.")
    card_f = st.file_uploader("카드사 엑셀 업로드 (xlsx)", type=['xlsx'], key="card_final")
    
    if card_f:
        try:
            df_raw = pd.read_excel(card_f)
            df_processed, error_msg = convert_to_wehago_format(df_raw)
            
            if error_msg:
                st.error(f"❌ 오류: {error_msg}")
                st.warning("팁: 엑셀의 금액 컬럼 이름을 '금액' 또는 '이용금액'으로 수정 후 다시 시도해보세요.")
            else:
                st.success(f"✅ 변환 성공! (감지된 금액 컬럼: {df_processed.columns[df_processed.columns.get_loc('total')-3]})")
                
                # ZIP 생성 및 다운로드
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_processed.to_excel(writer, index=False, sheet_name='위하고업로드용')
                    zf.writestr(f"위하고_변환_{card_f.name}", output.getvalue())
                
                st.download_button(
                    label="📥 위하고 변환 완료 파일(ZIP) 다운로드",
                    data=zip_buf.getvalue(),
                    file_name=f"WEHAGO_CONVERT_{card_f.name.split('.')[0]}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                
                # 미리보기 화면
                st.markdown("##### 🔍 변환 데이터 미리보기")
                st.dataframe(df_processed[['공급가액', '부가세', 'total']].head(), use_container_width=True)
                
        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
