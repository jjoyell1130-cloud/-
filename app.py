import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber

# --- 기본 설정 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")

def to_int(val):
    try:
        if pd.isna(val): return 0
        clean = re.sub(r'[^0-9.-]', '', str(val))
        return int(float(clean)) if clean else 0
    except: return 0

def find_header_and_read(file):
    """헤더를 자동으로 찾아 데이터프레임으로 변환"""
    try:
        # xlsm, xlsx, xls 대응 (엔진 자동 선택)
        df_raw = pd.read_excel(file, header=None)
        keywords = ['일자', '가맹점', '금액', '사업자', '카드번호', '승인']
        header_row = 0
        for i in range(min(40, len(df_raw))):
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

# --- 사이드바 메뉴 ---
MENU_1 = "⚖️ 매출매입장 PDF & 안내문"
MENU_2 = "💳 카드매입 수기 입력건 엑셀 변환"
menu = st.sidebar.selectbox("📂 업무 선택", [MENU_1, MENU_2])

if menu == MENU_1:
    st.title(MENU_1)
    st.info("국세청 PDF와 장부 엑셀을 업로드하면 안내문이 생성됩니다.")
    # (기존 메뉴 1 로직 위치 - 이전 코드와 동일)

elif menu == MENU_2:
    st.title(MENU_2)
    st.write("파일 내 카드번호가 여러 개인 경우 자동으로 파일을 쪼개어 저장합니다.")
    
    uploaded_cards = st.file_uploader("엑셀 파일 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    
    if uploaded_cards:
        zip_buffer = io.BytesIO()
        processed_count = 0
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_cards:
                df = find_header_and_read(file)
                if df is None: continue
                
                # 1. 컬럼 매핑 (추출 성공률 극대화)
                col_map = {
                    '매출일자': ['이용일', '승인일', '매출일', '일자'],
                    '카드번호': ['카드번호', '카드명', '구분'],
                    '가맹점명': ['가맹점', '이용처', '상호'],
                    '사업자번호': ['사업자', '등록번호'],
                    '매출금액': ['매출금액', '금액', '합계', '승인금액', '이용금액']
                }
                
                temp_df = pd.DataFrame()
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    temp_df[std] = df[actual] if actual else ""

                # 2. 금액 정제 및 0원 제거
                temp_df['매출금액'] = temp_df['매출금액'].apply(to_int)
                temp_df = temp_df[temp_df['매출금액'] > 0].copy()
                
                # 3. 공급가액 / 부가세 계산
                temp_df['공급가액'] = (temp_df['매출금액'] / 1.1).round(0).astype(int)
                temp_df['부가세'] = temp_df['매출금액'] - temp_df['공급가액']

                # 4. 카드번호별로 데이터 쪼개기 (핵심 기능)
                # 카드번호 컬럼의 뒤 4자리를 추출하여 그룹화
                temp_df['카드_그룹'] = temp_df['카드번호'].astype(str).apply(lambda x: x.split('-')[-1][-4:] if '-' in x else x[-4:])
                
                unique_cards = temp_df['카드_그룹'].unique()
                
                for card_num in unique_cards:
                    card_df = temp_df[temp_df['카드_그룹'] == card_num].copy()
                    # 출력 양식 정리
                    final_df = card_df[['카드번호', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                    
                    # 엑셀 파일 생성
                    excel_out = io.BytesIO()
                    with pd.ExcelWriter(excel_out, engine='openpyxl') as writer:
                        final_df.to_excel(writer, index=False)
                    
                    zf.writestr(f"정제_카드_{card_num}.xlsx", excel_out.getvalue())
                    processed_count += 1

        if processed_count > 0:
            st.success(f"✅ 총 {processed_count}개의 카드번호별 파일이 생성되었습니다.")
            st.download_button(
                label="📥 카드별 개별 엑셀(ZIP) 다운로드",
                data=zip_buffer.getvalue(),
                file_name="카드정제_카드별분리.zip",
                mime="application/zip",
                use_container_width=True
            )
