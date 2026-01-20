import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re

# --- [기능 함수] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        # 따옴표, 쉼표, 공백, (원) 등 불필요한 문자 모두 제거
        s = re.sub(r'[^\d.-]', '', str(val))
        return int(float(s))
    except: return 0

# --- [Streamlit 설정] ---
st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

with st.sidebar:
    st.markdown("### 📁 Menu")
    menus = ["🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"]
    for m in menus:
        if st.button(m, use_container_width=True, type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

curr = st.session_state.selected_menu
st.title(curr)

if curr == "💳 카드매입 수기입력건":
    card_up = st.file_uploader("💳 삼성카드 등 카드사 CSV/Excel 업로드", type=['xlsx', 'csv'], key="m3_up")
    
    if card_up:
        # 1. 파일명에서 업체명 추출
        raw_fn = os.path.splitext(card_up.name)[0]
        biz_name = raw_fn.split('-')[0].split('_')[0].strip()
        
        try:
            # 2. 데이터 로드 (헤더 찾기 위해 우선 전체 로드)
            if card_up.name.endswith('.csv'):
                # CSV는 인코딩 이슈가 잦으므로 cp949와 utf-8 둘 다 시도
                try:
                    raw_df = pd.read_csv(card_up, header=None, encoding='cp949')
                except:
                    card_up.seek(0)
                    raw_df = pd.read_csv(card_up, header=None, encoding='utf-8')
            else:
                raw_df = pd.read_excel(card_up, header=None)

            # 3. '카드번호'와 '금액'이 있는 실제 헤더 행 찾기
            header_idx = None
            for i, row in raw_df.iterrows():
                row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                if '카드번호' in row_str and ('이용금액' in row_str or '합계' in row_str or '승인금액' in row_str):
                    header_idx = i
                    break
            
            if header_idx is not None:
                # 헤더 적용하여 데이터 재설정
                df = raw_df.iloc[header_idx+1:].copy()
                df.columns = raw_df.iloc[header_idx].values
                df = df.dropna(how='all', subset=[c for c in df.columns if c is not None])

                # 컬럼명 유연하게 찾기
                num_col = next((c for c in df.columns if '카드번호' in str(c)), None)
                amt_col = next((c for c in df.columns if any(k in str(c) for k in ['이용금액', '합계', '금액'])), None)
                
                if num_col and amt_col:
                    # 4. 데이터 정제 및 계산
                    df[amt_col] = df[amt_col].apply(to_int)
                    df = df[df[amt_col] != 0].copy() # 0원인 행(취소/합계 등) 제외
                    
                    df['공급가액'] = (df[amt_col] / 1.1).round(0).astype(int)
                    df['부가세'] = df[amt_col] - df['공급가액']

                    # 5. 카드번호별 파일 분리 및 압축
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        # 카드번호 뒷 4자리로 그룹화
                        df['tmp_card'] = df[num_col].astype(str).str.replace(r'[^0-9]', '', regex=True).str[-4:]
                        
                        for c_num, group in df.groupby('tmp_card'):
                            if not c_num or c_num == 'nan': continue
                            
                            excel_buf = io.BytesIO()
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                # 불필요한 임시 컬럼 제외하고 저장
                                group.drop(columns=['tmp_card']).to_excel(writer, index=False)
                            
                            final_fn = f"{biz_name}_카드_{c_num}_(업로드용).xlsx"
                            zf.writestr(final_fn, excel_buf.getvalue())
                    
                    if len(df) > 0:
                        st.success(f"✅ {biz_name} 데이터 분석 완료! (총 {len(df)}건)")
                        st.download_button("📥 분리된 엑셀 파일(ZIP) 다운로드", 
                                         data=z_buf.getvalue(), 
                                         file_name=f"{biz_name}_카드분리결과.zip", 
                                         use_container_width=True)
                    else:
                        st.warning("분리할 유효한 데이터가 없습니다.")
                else:
                    st.error("파일에서 '카드번호' 또는 '이용금액' 컬럼을 찾을 수 없습니다.")
            else:
                st.error("데이터 시작점(헤더)을 찾지 못했습니다. 파일 형식을 확인해주세요.")

        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

# (기타 메뉴 로직 생략 - 필요 시 기존 코드 유지)
