import streamlit as st
import pandas as pd
import io
import re
import zipfile
from datetime import datetime

# --- 설정 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")

def to_int(val):
    try:
        if pd.isna(val): return 0
        clean = re.sub(r'[^0-9.-]', '', str(val))
        return int(float(clean)) if clean else 0
    except: return 0

def format_date(val):
    """매출일자를 YYYY-MM-DD 형태로 간소화"""
    try:
        if isinstance(val, (int, float)): # 엑셀 날짜 포맷(숫자)인 경우
            return pd.to_datetime(val, unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
        dt = pd.to_datetime(str(val), errors='coerce')
        return dt.strftime('%Y-%m-%d') if not pd.isna(dt) else str(val)
    except:
        return str(val)

# --- 메뉴 구성 ---
MENU_1 = "🏠 매출매입장 PDF & 안내문"
MENU_2 = "💳 카드매입 수기 입력건 (카드별 자동분리)"
menu = st.sidebar.selectbox("📂 수행할 업무를 선택하세요", [MENU_1, MENU_2])

if menu == MENU_1:
    st.title(MENU_1)
    st.info("국세청 PDF와 장부 엑셀을 업로드해 주세요.")
    # (매출매입장 기존 로직은 유지됨)

elif menu == MENU_2:
    st.title(MENU_2)
    st.write("파일 내 카드번호별로 분리하며, 파일명을 [연도+업체명+카드사용내역+카드번호]로 지정합니다.")
    
    uploaded_cards = st.file_uploader("엑셀 파일 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    
    if uploaded_cards:
        zip_buffer = io.BytesIO()
        processed_count = 0
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_cards:
                # 파일명에서 업체명 추출 (예: '2025 소울인테리어-...' 에서 '소울인테리어' 추출)
                file_name_orig = file.name
                company_name = "업체명"
                year = datetime.now().strftime('%Y')
                
                name_match = re.search(r'(\d{4})\s*([가-힣\w\s]+?)-', file_name_orig)
                if name_match:
                    year = name_match.group(1)
                    company_name = name_match.group(2).strip()

                # 1. 헤더 자동 찾기 로직
                df_raw = pd.read_excel(file, header=None)
                header_row = 0
                for i in range(min(40, len(df_raw))):
                    row_str = "".join([str(v) for v in df_raw.iloc[i].values])
                    if any(k in row_str for k in ['카드번호', '이용일', '매출일', '승인일']):
                        header_row = i
                        break
                
                file.seek(0)
                df = pd.read_excel(file, header=header_row)
                df.columns = [str(c).strip() for c in df.columns]

                # 2. 필수 컬럼 매핑
                col_map = {
                    '매출일자': ['이용일', '승인일', '매출일', '일자'],
                    '카드번호': ['카드번호', '카드명', '구분'],
                    '가맹점명': ['가맹점', '이용처', '상호'],
                    '사업자번호': ['사업자', '등록번호', '사업자번호'],
                    '매출금액': ['매출금액', '금액', '합계', '승인금액']
                }
                
                temp_df = pd.DataFrame()
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    temp_df[std] = df[actual] if actual else ""

                # 3. 데이터 정제 (날짜 간소화 포함)
                temp_df['매출일자'] = temp_df['매출일자'].apply(format_date)
                temp_df['매출금액'] = temp_df['매출금액'].apply(to_int)
                temp_df = temp_df[temp_df['매출금액'] > 0].copy()
                
                temp_df['공급가액'] = (temp_df['매출금액'] / 1.1).round(0).astype(int)
                temp_df['부가세'] = temp_df['매출금액'] - temp_df['공급가액']

                # 4. 카드번호별 파일 쪼개기 및 저장
                # 카드번호의 마지막 4자리를 추출하여 그룹화
                temp_df['카드_ID'] = temp_df['카드번호'].astype(str).apply(lambda x: re.sub(r'[^0-9]', '', x)[-4:] if len(re.sub(r'[^0-9]', '', x)) >= 4 else "0000")
                
                for card_num in temp_df['카드_ID'].unique():
                    card_df = temp_df[temp_df['카드_ID'] == card_num].copy()
                    final_df = card_df[['카드번호', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                    
                    # 요청하신 파일명 규칙 적용: 연도+업체명+카드사용내역+카드번호(업로드용).xlsx
                    new_file_name = f"{year} {company_name}-카드사용내역({card_num})(업로드용).xlsx"
                    
                    excel_out = io.BytesIO()
                    with pd.ExcelWriter(excel_out, engine='openpyxl') as writer:
                        final_df.to_excel(writer, index=False)
                    
                    zf.writestr(new_file_name, excel_out.getvalue())
                    processed_count += 1

        if processed_count > 0:
            st.success(f"✅ 총 {processed_count}개의 파일 분리 완료!")
            st.download_button(
                label="📥 카드별 개별 엑셀(ZIP) 다운로드",
                data=zip_buffer.getvalue(),
                file_name=f"{company_name}_카드내역_정리.zip",
                mime="application/zip",
                use_container_width=True
            )
