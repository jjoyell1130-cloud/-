import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re

# --- [숫자 변환기: 따옴표, 쉼표 제거] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        s = re.sub(r'[^\d.-]', '', str(val))
        return int(float(s))
    except: return 0

# --- [메인 로직] ---
st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

# 사이드바 생략 (기존과 동일하게 유지하거나 아래 코드 참고)
curr = st.sidebar.radio("Menu", ["🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"])

if curr == "💳 카드매입 수기입력건":
    st.title("💳 카드매입 수기입력건 (신한/삼성 통합)")
    card_up = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'])
    
    if card_up:
        raw_fn = os.path.splitext(card_up.name)[0]
        biz_name = raw_fn.split('-')[0].split('_')[0].strip()
        
        try:
            # 1. 파일 읽기
            if card_up.name.endswith('.csv'):
                try: raw_df = pd.read_csv(card_up, header=None, encoding='cp949')
                except: card_up.seek(0); raw_df = pd.read_csv(card_up, header=None, encoding='utf-8-sig')
            else:
                raw_df = pd.read_excel(card_up, header=None)

            # 2. 헤더 찾기 (핵심 키워드)
            date_k = ['거래일', '이용일', '일자', '승인일']
            partner_k = ['가맹점명', '거래처', '상호', '이용처', '내용']
            amt_k = ['이용금액', '합계', '승인금액', '금액', '결제액']
            item_k = ['업종', '품명', '상품명', '종목']
            card_k = ['카드번호', '카드 No', '이용카드', '카드명']

            header_idx = None
            for i, row in raw_df.iterrows():
                row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                # 거래처와 금액 키워드가 동시에 있는 행을 헤더로 인식
                if any(pk in row_str for pk in partner_k) and any(ak in row_str for ak in amt_k):
                    header_idx = i
                    break
            
            if header_idx is not None:
                df = raw_df.iloc[header_idx+1:].copy()
                df.columns = raw_df.iloc[header_idx].values
                df = df.dropna(how='all', axis=0)

                # 3. 컬럼 이름 매칭 (삼성/신한 통합)
                d_col = next((c for c in df.columns if any(k in str(c) for k in date_k)), None)
                p_col = next((c for c in df.columns if any(k in str(c) for k in partner_k)), None)
                a_col = next((c for c in df.columns if any(k in str(c) for k in amt_k)), None)
                i_col = next((c for c in df.columns if any(k in str(c) for k in item_k)), None)
                n_col = next((c for c in df.columns if any(k in str(c) for k in card_k)), None)

                if p_col and a_col:
                    # 데이터 정제
                    df[a_col] = df[a_col].apply(to_int)
                    df = df[df[a_col] != 0].copy()
                    
                    # 표준 컬럼 생성 (여기서 공란을 채움!)
                    df['일자'] = df[d_col] if d_col else ""
                    df['거래처'] = df[p_col] if p_col else "상호미표기"
                    df['품명'] = df[i_col] if i_col is not None else "-" # 신한카드 대응
                    df['공급가액'] = (df[a_col] / 1.1).round(0).astype(int)
                    df['부가세'] = df[a_col] - df['공급가액']
                    df['합계'] = df[a_col]

                    # 4. 파일 분리 및 다운로드
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        # 카드번호 뒷 4자리만 추출
                        df['card_group'] = df[n_col].astype(str).str.replace(r'[^0-9]', '', regex=True).str[-4:]
                        
                        final_cols = ['일자', '거래처', '품명', '공급가액', '부가세', '합계']
                        for c_num, group in df.groupby('card_group'):
                            if not c_num or c_num == 'nan' or c_num == '': continue
                            excel_buf = io.BytesIO()
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                group[final_cols].to_excel(writer, index=False)
                            zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", excel_buf.getvalue())
                    
                    st.success(f"✅ {biz_name} 분석 완료!")
                    st.download_button("📥 결과물(ZIP) 다운로드", z_buf.getvalue(), f"{biz_name}_결과.zip")
            else:
                st.error("데이터 시작점을 찾지 못했습니다. 엑셀의 컬럼명(가맹점명, 이용금액 등)을 확인해주세요.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
