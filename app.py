import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re

# --- [기초 엔진: 숫자 변환] ---
def to_int(val):
    try:
        if pd.isna(val): return 0
        # 따옴표, 콤마, 공백 제거 후 숫자로 변환
        s = str(val).replace('"', '').replace(',', '').strip()
        return int(float(s))
    except:
        return 0

# (중략: 메뉴 설정 및 기타 PDF 함수는 기존과 동일하게 유지)

# --- [3. 메뉴별 메인 로직] ---
# ... (Home, 마감작업, 매출매입장 변환 생략) ...

elif curr == "💳 카드매입 수기입력건":
    st.info("카드내역서 엑셀파일을 업로드하시면 위하고 업로드용으로 자동 변환됩니다.")
    card_up = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'], key="card_final_v3")
    
    if card_up:
        raw_fn = os.path.splitext(card_up.name)[0]
        biz_name = raw_fn.split('-')[0].split('_')[0].strip()
        
        try:
            # 1. 파일 읽기 (신한카드 CSV 특성 반영)
            if card_up.name.endswith('.csv'):
                try: raw_df = pd.read_csv(card_up, header=None, encoding='cp949', quotechar='"')
                except: card_up.seek(0); raw_df = pd.read_csv(card_up, header=None, encoding='utf-8-sig', quotechar='"')
            else:
                raw_df = pd.read_excel(card_up, header=None)

            # 2. 헤더 행 찾기 (신한카드: 거래일, 이용카드, 가맹점명 등 포함 행)
            header_idx = None
            for i, row in raw_df.iterrows():
                row_str = "".join(map(str, row.values)).replace("\n", "").replace(" ", "")
                if '가맹점명' in row_str and '이용금액' in row_str:
                    header_idx = i
                    break
            
            if header_idx is not None:
                # 3. 데이터 정제: 제목행 아래부터 추출
                df = raw_df.iloc[header_idx + 1:].copy()
                # 제목행의 줄바꿈과 따옴표 제거하여 컬럼명 설정
                df.columns = [str(c).replace("\n", "").replace('"', '').strip() for c in raw_df.iloc[header_idx]]
                df = df.dropna(how='all', axis=0)

                # 4. 필수 컬럼 매핑 (신한카드 헤더 기준)
                d_col = '거래일' if '거래일' in df.columns else (df.columns[0] if len(df.columns) > 0 else None)
                p_col = '가맹점명' if '가맹점명' in df.columns else None
                a_col = '이용금액' if '이용금액' in df.columns else None
                n_col = next((c for c in df.columns if '뒤4자리' in c or '카드' in c), None)

                if p_col and a_col:
                    # 데이터 내용에서 따옴표 제거 및 숫자 변환
                    df[a_col] = df[a_col].apply(to_int)
                    df = df[df[a_col] > 0].copy() # 0원 건 제외
                    
                    # 위하고 양식에 맞게 데이터 재구성
                    new_df = pd.DataFrame()
                    new_df['일자'] = df[d_col].astype(str).str.replace('"', '').str.strip()
                    new_df['거래처'] = df[p_col].astype(str).str.replace('"', '').str.strip()
                    new_df['품명'] = "카드매입"
                    
                    # 신한카드 공급가액/부가세 컬럼이 있으면 활용, 없으면 계산
                    if '공급가액' in df.columns and '부가세' in df.columns:
                        new_df['공급가액'] = df['공급가액'].apply(to_int)
                        new_df['부가세'] = df['부가세'].apply(to_int)
                    else:
                        new_df['공급가액'] = (df[a_col] / 1.1).round(0).astype(int)
                        new_df['부가세'] = df[a_col] - new_df['공급가액']
                    
                    new_df['합계'] = df[a_col]
                    
                    # 카드번호 뒷자리 추출하여 그룹화
                    card_ids = df[n_col].astype(str).str.extract(r'(\d{4})').fillna("카드")[0]
                    new_df['card_group'] = card_ids

                    # 5. 파일 생성 및 압축
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        for c_num, group in new_df.groupby('card_group'):
                            excel_buf = io.BytesIO()
                            # '위하고업로드'라는 새 시트에 깔끔하게 저장
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                final_output = group.drop(columns=['card_group'])
                                final_output.to_excel(writer, index=False, sheet_name='위하고업로드')
                            zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", excel_buf.getvalue())
                    
                    st.success(f"✅ {biz_name} 변환 완료! (신한카드 CSV 특수구조 해결)")
                    st.download_button("📥 변환파일(ZIP) 다운로드", z_buf.getvalue(), f"{biz_name}_위하고양식.zip")
            else:
                st.error("파일에서 '가맹점명'과 '이용금액'이 포함된 제목 행을 찾지 못했습니다.")
        except Exception as e:
            st.error(f"변환 오류 발생: {e}")
