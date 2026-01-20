import streamlit as st
import pandas as pd
import io
import zipfile
import os

# --- [기초 엔진: 숫자 정제] ---
def clean_int(val):
    try:
        if pd.isna(val): return 0
        # 숫자만 남기고 제거 (따옴표, 콤마 등 방해 요소 제거)
        s = "".join(filter(str.isdigit, str(val)))
        return int(s) if s else 0
    except: return 0

# --- [메인 로직] ---
# (중략: 메뉴 설정 및 UI 부분은 기존 코드와 동일)

elif curr == "💳 카드매입 수기입력건":
    st.info("카드내역서 엑셀파일을 업로드하시면 위하고 업로드용으로 자동 변환됩니다.")
    card_up = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'], key="final_card_v4")
    
    if card_up:
        biz_name = card_up.name.split('-')[0].split('_')[0].strip()
        try:
            # 1. 파일 읽기 (인코딩 문제 방지)
            if card_up.name.endswith('.csv'):
                try: df_raw = pd.read_csv(card_up, header=None, encoding='cp949')
                except: card_up.seek(0); df_raw = pd.read_csv(card_up, header=None, encoding='utf-8-sig')
            else:
                df_raw = pd.read_excel(card_up, header=None)

            # 2. 제목 행 찾기 (설명글 무시하고 '거래일'이 시작되는 지점 탐색)
            target_idx = None
            for i, row in df_raw.iterrows():
                row_str = "".join(map(str, row.values))
                if '거래일' in row_str and '가맹점명' in row_str:
                    target_idx = i
                    break
            
            if target_idx is not None:
                # 3. 데이터 로드 (제목 줄 기준 아래 데이터만 추출)
                df = df_raw.iloc[target_idx + 1:].copy()
                # 헤더 줄바꿈/따옴표 청소
                df.columns = [str(c).replace("\n", " ").replace('"', '').strip() for c in df_raw.iloc[target_idx]]
                df = df.dropna(subset=[df.columns[0]]) # 날짜 없는 행 제거

                # 4. 위하고 필수 양식으로 재조립
                new_df = pd.DataFrame()
                new_df['일자'] = df['거래일'].astype(str).str.replace('"', '').str.strip()
                new_df['거래처'] = df['가맹점명'].astype(str).str.replace('"', '').str.strip()
                new_df['품명'] = "카드매입"
                
                # 금액 처리 (공급가액, 부가가치세 추출)
                total_amt = df['이용금액'].apply(clean_int)
                new_df['공급가액'] = df['공급가액'].apply(clean_int)
                new_df['부가세'] = df['부가세'].apply(clean_int)
                new_df['합계'] = total_amt
                
                # 카드번호 뒷자리 분리 (파일명용)
                card_col = next((c for c in df.columns if '카드' in c), df.columns[2])
                new_df['card_no'] = df[card_col].astype(str).str.extract(r'(\d{4})').fillna("0000")

                # 5. 파일 분리 및 압축
                z_buf = io.BytesIO()
                with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                    for c_num, group in new_df.groupby('card_no'):
                        out_buf = io.BytesIO()
                        with pd.ExcelWriter(out_buf, engine='xlsxwriter') as writer:
                            # '위하고업로드' 시트에 정제된 내용만 기입
                            group.drop(columns=['card_no']).to_excel(writer, index=False, sheet_name='위하고업로드')
                        zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", out_buf.getvalue())
                
                st.success(f"✅ {biz_name} 변환 성공!")
                st.download_button("📥 위하고 양식 다운로드", z_buf.getvalue(), f"{biz_name}_변환완료.zip")
            else:
                st.error("파일 제목행을 찾지 못했습니다. (거래일/가맹점명 항목 없음)")
        except Exception as e:
            st.error(f"처리 중 오류 발생: {e}")
