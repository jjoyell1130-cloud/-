import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re
import pdfplumber
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [기초 엔진: 숫자 변환 및 PDF 생성 로직은 동일] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        s = str(val).replace('"', '').replace(',', '').strip()
        return int(float(s))
    except: return 0

# ... (기존 extract_data_from_pdf, make_pdf_stream 함수 생략 - 위와 동일) ...

# --- [UI 및 메뉴 설정 동일] ---
# (중략: 세션 설정 및 사이드바 로직)

# --- [3. 메뉴별 메인 로직] ---
# ... (Home, 마감작업, 매출매입장 PDF 변환 로직 생략) ...

elif curr == "💳 카드매입 수기입력건":
    st.info("카드내역서 엑셀파일을 업로드하시면 위하고 업로드용으로 자동 변환됩니다.")
    card_up = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'], key="card_m3_final")
    
    if card_up:
        raw_fn = os.path.splitext(card_up.name)[0]
        biz_name = raw_fn.split('-')[0].split('_')[0].strip()
        
        try:
            # 1. 파일 읽기 (CSV/Excel 대응)
            if card_up.name.endswith('.csv'):
                try: raw_df = pd.read_csv(card_up, header=None, encoding='cp949')
                except: card_up.seek(0); raw_df = pd.read_csv(card_up, header=None, encoding='utf-8-sig')
            else:
                raw_df = pd.read_excel(card_up, header=None)

            # 2. 헤더 찾기 (신한카드 "이용카드\n(뒤4자리)" 등 줄바꿈 완벽 대응)
            header_idx = None
            for i, row in raw_df.iterrows():
                # 행 전체를 하나의 문자열로 합치고 특수문자 제거 후 검사
                combined = "".join(map(str, row.values)).replace("\n", "").replace('"', '').replace(" ", "")
                if ('가맹점' in combined or '거래처' in combined) and ('금액' in combined or '합계' in combined):
                    header_idx = i
                    break
            
            if header_idx is not None:
                # 3. 데이터 정제: 제목행 아래부터 실제 데이터만 추출
                cols = [str(c).replace("\n", " ").replace('"', '').strip() for c in raw_df.iloc[header_idx]]
                df = raw_df.iloc[header_idx + 1:].copy()
                df.columns = cols
                df = df.dropna(how='all', axis=0)

                # 컬럼 매핑 (승인일, 가맹점명, 이용금액 등 신한카드 키워드 타겟팅)
                d_col = next((c for c in df.columns if any(k in str(c) for k in ['거래일', '이용일', '일자', '승인일'])), None)
                p_col = next((c for c in df.columns if any(k in str(c) for k in ['가맹점', '거래처', '상호', '이용처'])), None)
                a_col = next((c for c in df.columns if any(k in str(c) for k in ['이용금액', '합계', '금액', '승인금액'])), None)
                n_col = next((c for c in df.columns if any(k in str(c) for k in ['카드', '번호', '뒤4자리'])), None)
                
                if p_col and a_col:
                    # 금액 전처리
                    df[a_col] = df[a_col].apply(to_int)
                    df = df[df[a_col] > 0].copy() # 0원 건 제외
                    
                    df['일자'] = df[d_col] if d_col else ""
                    df['거래처'] = df[p_col].astype(str).str.replace('"', '').str.strip()
                    df['품명'] = "카드매입" 
                    
                    # 부가세/공급가액 계산 (신한카드 파일에 공급가액이 비어있는 경우 대비)
                    df['공급가액'] = (df[a_col] / 1.1).round(0).astype(int)
                    df['부가세'] = df[a_col] - df['공급가액']
                    df['합계'] = df[a_col]

                    # 4. 카드번호별 파일 분리 및 압축
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        # 카드번호 뒷 4자리만 추출 ("본인8525" -> "8525")
                        card_nums = df[n_col].astype(str).str.extract(r'(\d{4})').fillna("카드")[0]
                        df['card_group'] = card_nums
                        
                        final_cols = ['일자', '거래처', '품명', '공급가액', '부가세', '합계']
                        for c_num, group in df.groupby('card_group'):
                            excel_buf = io.BytesIO()
                            # 신규 엑셀 시트에 데이터 기입
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                group[final_cols].to_excel(writer, index=False, sheet_name='위하고업로드')
                            zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", excel_buf.getvalue())
                    
                    st.success(f"✅ {biz_name} 처리 완료! (신한카드 형식 대응)")
                    st.download_button("📥 결과(ZIP) 다운로드", z_buf.getvalue(), f"{biz_name}_위하고변환.zip")
            else:
                st.error("데이터의 시작점(제목줄)을 찾을 수 없습니다. 파일 형식을 확인해주세요.")
        except Exception as e:
            st.error(f"변환 중 오류가 발생했습니다: {e}")
