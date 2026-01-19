import streamlit as st
import pandas as pd
import io
import os
import urllib.request
import re

# --- 폰트 및 환경 설정 ---
def load_font():
    font_path = "nanum.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except: return False
    return True

load_font()

# --- 데이터 정제 함수 ---
def find_header_and_read(file):
    """안내문 등으로 인해 데이터 시작점이 다른 엑셀에서 헤더를 찾아 읽는 함수"""
    # 전표일자, 가맹점명 등 핵심 키워드
    keywords = ['일자', '가맹점', '금액', '사업자', '승인']
    
    # 1. 일단 0행부터 읽어보기
    df_temp = pd.read_excel(file, header=None)
    
    # 2. 키워드가 가장 많이 포함된 행 찾기
    header_row = 0
    max_matches = 0
    for i in range(min(20, len(df_temp))): # 상위 20행 조사
        row_values = [str(val) for val in df_temp.iloc[i].values]
        matches = sum(1 for word in keywords if any(word in val for val in row_values))
        if matches > max_matches:
            max_matches = matches
            header_row = i
            
    # 3. 찾은 행을 헤더로 다시 읽기
    file.seek(0)
    df = pd.read_excel(file, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]
    return df

# --- UI 구성 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")
st.sidebar.title("📂 업무 선택")
menu = st.sidebar.selectbox("", ["매출매입장 PDF & 안내문", "카드매입 수기 입력건 엑셀 변환"])

if menu == "카드매입 수기 입력건 엑셀 변환":
    st.title("💳 카드매입 수기 입력건 엑셀 변환")
    st.write("카드사 원본 엑셀(국민, 비씨, 기업 등)을 업로드하면 수기 입력용 양식으로 자동 변환합니다.")
    
    uploaded_cards = st.file_uploader("변환할 카드사 엑셀 파일들을 선택하세요", type=['xlsx', 'xls'], accept_multiple_files=True)
    
    if uploaded_cards:
        all_rows = []
        for file in uploaded_cards:
            try:
                # 카드 별칭 추출
                card_id = file.name.split('(')[-1].split(')')[0] if '(' in file.name else file.name.split('.')[0]
                
                # 헤더 자동 감지 후 읽기
                df = find_header_and_read(file)

                # 컬럼 매핑 (최대한 넓게 설정)
                col_map = {
                    '매출일자': ['이용일자', '매출일자', '승인일자', '거래일자', '일자', '사용일'],
                    '가맹점명': ['가맹점명', '가맹점명칭', '이용처', '상호', '사업자명'],
                    '사업자번호': ['사업자번호', '사업자등록번호', '가맹점사업자번호', '사업자'],
                    '매출금액': ['이용금액', '매출금액', '승인금액', '결제금액', '합계', '금액']
                }

                res_df = pd.DataFrame()
                res_df['카드번호/구분'] = [card_id] * len(df)
                
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    res_df[std] = df[actual] if actual else ""

                # 숫자 변환 및 계산
                def clean_money(x):
                    if pd.isna(x): return 0
                    val = re.sub(r'[^0-9.-]', '', str(x))
                    try: return int(float(val))
                    except: return 0

                res_df['매출금액'] = res_df['매출금액'].apply(clean_money)
                res_df = res_df[res_df['매출금액'] > 0].copy() # 0원 데이터(안내문 행 등) 제거
                
                # 공급가액/부가세 계산
                res_df['공급가액'] = (res_df['매출금액'] / 1.1).round(0).astype(int)
                res_df['부가세'] = res_df['매출금액'] - res_df['공급가액']
                
                # 최종 컬럼 정리
                res_df = res_df[['카드번호/구분', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                all_rows.append(res_df)
                
            except Exception as e:
                st.error(f"⚠️ {file.name} 변환 중 오류: {e}")

        if all_rows:
            final_df = pd.concat(all_rows, ignore_index=True)
            st.divider()
            st.success(f"✅ 총 {len(all_rows)}개의 파일이 통합 변환되었습니다.")
            
            st.dataframe(final_df, use_container_width=True)

            # 다운로드 버튼 생성
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, index=False, sheet_name='수기입력용')
            
            st.download_button(
                label="📥 변환된 엑셀 파일 다운로드",
                data=output.getvalue(),
                file_name="카드매입_수기입력_통합본.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
