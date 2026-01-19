import streamlit as st
import pandas as pd
import io
import os
import re

# --- 라이브러리 체크 및 엔진 설정 ---
# .xls 파일을 읽기 위해 내부적으로 처리를 강화합니다.
def safe_read_excel(file):
    try:
        # 1. 일반적인 방식으로 시도 (xlsx 등)
        return pd.read_excel(file)
    except Exception:
        try:
            # 2. .xls 파일일 경우 엔진을 명시적으로 지정하여 시도
            file.seek(0)
            return pd.read_excel(file, engine='xlrd')
        except:
            # 3. 만약 xlrd가 없다면 html 방식으로라도 읽기 시도 (일부 xls는 html 구조임)
            file.seek(0)
            try:
                return pd.read_html(file)[0]
            except:
                return None

# --- 헤더 자동 찾기 함수 (강화 버전) ---
def find_header_and_read(file):
    # .xls와 .xlsx 모두 대응 가능한 읽기
    try:
        # 우선 데이터가 어디서 시작될지 모르니 전체를 읽음
        df_raw = pd.read_excel(file, header=None)
    except Exception as e:
        # xlrd 오류 발생 시 안내 메시지
        st.error(f"⚠️ '{file.name}'은 구형 엑셀(.xls) 형식입니다. 서버에 'xlrd' 라이브러리가 필요합니다.")
        return None

    keywords = ['일자', '가맹점', '금액', '사업자', '승인', '구분', '매출']
    header_row = 0
    max_matches = 0
    
    for i in range(min(25, len(df_raw))):
        row_values = [str(val) for val in df_raw.iloc[i].values]
        matches = sum(1 for word in keywords if any(word in val for val in row_values))
        if matches > max_matches:
            max_matches = matches
            header_row = i
            
    file.seek(0)
    df = pd.read_excel(file, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]
    return df

# --- UI 메인 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")
menu = st.sidebar.selectbox("📂 업무 선택", ["매출매입장 PDF & 안내문", "카드매입 수기 입력건 엑셀 변환"])

if menu == "카드매입 수기 입력건 엑셀 변환":
    st.title("💳 카드매입 수기 입력건 엑셀 변환")
    st.info("💡 .xls 파일 오류 시, 엑셀에서 파일을 열어 '다른 이름으로 저장' -> 'Excel 통합 문서(.xlsx)'로 저장 후 다시 올려주시면 가장 정확합니다.")
    
    uploaded_cards = st.file_uploader("파일 업로드", type=['xlsx', 'xls'], accept_multiple_files=True)
    
    if uploaded_cards:
        all_rows = []
        for file in uploaded_cards:
            df = find_header_and_read(file)
            
            if df is not None:
                # 카드 식별 (파일명)
                card_id = file.name.split('(')[-1].split(')')[0] if '(' in file.name else file.name.split('.')[0]
                
                # 컬럼 매핑
                col_map = {
                    '매출일자': ['이용일', '매출일', '승인일', '거래일', '일자'],
                    '가맹점명': ['가맹점', '이용처', '상호'],
                    '사업자번호': ['사업자', '등록번호'],
                    '매출금액': ['금액', '합계', '승인금액']
                }
                
                res_df = pd.DataFrame()
                res_df['카드번호/구분'] = [card_id] * len(df)
                
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    res_df[std] = df[actual] if actual else ""

                # 숫자 정제 로직
                def clean_val(x):
                    v = re.sub(r'[^0-9.-]', '', str(x))
                    try: return int(float(v))
                    except: return 0

                res_df['매출금액'] = res_df['매출금액'].apply(clean_val)
                res_df = res_df[res_df['매출금액'] > 0].copy()
                
                # 세액 계산
                res_df['공급가액'] = (res_df['매출금액'] / 1.1).round(0).astype(int)
                res_df['부가세'] = res_df['매출금액'] - res_df['공급가액']
                
                # 최종 정리
                res_df = res_df[['카드번호/구분', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                all_rows.append(res_df)

        if all_rows:
            final_df = pd.concat(all_rows, ignore_index=True)
            st.success("✅ 변환 완료!")
            st.dataframe(final_df)
            
            # 다운로드
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                final_df.to_excel(wr, index=False)
            st.download_button("📥 통합 엑셀 다운로드", out.getvalue(), "카드매입_정리본.xlsx")
