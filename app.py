import streamlit as st
import pandas as pd
import io
import re
import zipfile

# --- 메뉴 이름 설정 ---
MENU_NAME = "💳 카드매입 수기 입력건 엑셀 변환"

st.set_page_config(page_title="세무비서 자동화", layout="wide")

def to_int(val):
    try:
        if pd.isna(val): return 0
        clean = re.sub(r'[^0-9-]', '', str(val))
        return int(float(clean)) if clean else 0
    except: return 0

def find_header_and_read(file):
    """헤더를 찾지 못해 변환에 실패하는 문제를 해결하기 위한 강화된 로직"""
    try:
        # 1. 우선 시트를 읽어옴 (엔진 자동 선택)
        df_raw = pd.read_excel(file, header=None)
        
        # 2. 핵심 키워드가 포함된 행을 헤더로 지정
        keywords = ['일자', '가맹점', '금액', '사업자', '카드번호', '승인']
        header_row = 0
        for i in range(min(30, len(df_raw))): # 상위 30행까지 검색
            row_vals = [str(v) for v in df_raw.iloc[i].values]
            if any(k in v for k in keywords for v in row_vals):
                header_row = i
                break
        
        file.seek(0)
        df = pd.read_excel(file, header=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"⚠️ '{file.name}' 읽기 실패: {e}")
        return None

st.title(MENU_NAME)
st.markdown("---")

uploaded_files = st.file_uploader("변환할 카드사 엑셀들을 모두 선택하세요", type=['xlsx', 'xls'], accept_multiple_files=True)

if uploaded_files:
    processed_files = [] # 변환된 데이터프레임과 파일명을 담을 리스트
    
    for file in uploaded_files:
        df = find_header_and_read(file)
        
        if df is not None:
            # 파일명에서 카드 구분 정보 추출
            card_info = file.name.split('(')[-1].split(')')[0] if '(' in file.name else file.name.split('.')[0]
            
            # 카드사별 다양한 컬럼명 대응 매핑
            col_map = {
                '매출일자': ['일자', '승인일', '이용일', '매출일'],
                '가맹점명': ['가맹점', '이용처', '상호', '사업장'],
                '사업자번호': ['사업자', '등록번호', '사업자번호'],
                '매출금액': ['금액', '합계', '승인금액', '이용금액', '결제금액']
            }
            
            res_df = pd.DataFrame()
            res_df['카드번호/구분'] = [card_info] * len(df)
            
            for std, aliases in col_map.items():
                actual = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                if actual:
                    res_df[std] = df[actual]
                else:
                    res_df[std] = ""
            
            # 금액 정제 및 0원 데이터 제거
            res_df['매출금액'] = res_df['매출금액'].apply(to_int)
            res_df = res_df[res_df['매출금액'] > 0].copy()
            
            # 공급가액/부가세 계산 (요청하신 산식 적용)
            res_df['공급가액'] = (res_df['매출금액'] / 1.1).round(0).astype(int)
            res_df['부가세'] = res_df['매출금액'] - res_df['공급가액']
            
            # 최종 컬럼 순서 (요청 양식)
            final_df = res_df[['카드번호/구분', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
            processed_files.append({"filename": f"정제_{card_info}.xlsx", "df": final_df})

    if processed_files:
        st.success(f"✅ 총 {len(processed_files)}개의 파일 변환에 성공했습니다.")
        
        # 압축 파일(ZIP) 생성을 위한 버퍼
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for item in processed_files:
                # 각 데이터프레임을 개별 엑셀 파일로 변환하여 ZIP에 추가
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    item["df"].to_excel(writer, index=False)
                zf.writestr(item["filename"], excel_buffer.getvalue())
        
        st.info("아래 버튼을 누르면 변환된 카드별 엑셀 파일들이 담긴 압축파일(ZIP)을 내려받습니다.")
        
        # 최종 다운로드 버튼
        st.download_button(
            label="📥 변환된 카드별 엑셀(ZIP) 다운로드",
            data=zip_buffer.getvalue(),
            file_name="카드매입_수기입력용_개별파일.zip",
            mime="application/zip",
            use_container_width=True
        )
        
        # 미리보기 화면
        for item in processed_files:
            with st.expander(f"👀 {item['filename']} 미리보기"):
                st.dataframe(item["df"], use_container_width=True)
