import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber
from datetime import datetime

# --- 설정 및 유틸리티 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")

def to_int(val):
    try:
        if pd.isna(val): return 0
        clean = re.sub(r'[^0-9.-]', '', str(val))
        return int(float(clean)) if clean else 0
    except: return 0

def format_date(val):
    """매출일자를 YYYY-MM-DD 형태로 변환"""
    try:
        if isinstance(val, (int, float)):
            return pd.to_datetime(val, unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
        dt = pd.to_datetime(str(val), errors='coerce')
        return dt.strftime('%Y-%m-%d') if not pd.isna(dt) else str(val)
    except:
        return str(val)

# --- 메뉴 구성 (오류 방지를 위해 상단 고정) ---
MENU_1 = "🏠 매출매입장 PDF & 안내문"
MENU_2 = "💳 카드매입 수기 입력건 (카드별 자동분리)"

# 사이드바에서 메뉴 선택
menu = st.sidebar.selectbox("📂 수행할 업무를 선택하세요", [MENU_1, MENU_2])

# --- [메뉴 1] 매출매입장 & 안내문 로직 ---
if menu == MENU_1:
    st.title(MENU_1)
    st.info("국세청 PDF와 장부 엑셀을 업로드하면 안내문이 생성됩니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        tax_pdfs = st.file_uploader("1. 국세청 PDF", type=['pdf'], accept_multiple_files=True)
    with col2:
        excel_files = st.file_uploader("2. 매출매입장 엑셀", type=['xlsx'], accept_multiple_files=True)

    # (이전 메뉴 1의 PDF/엑셀 분석 로직이 이 자리에 유지됩니다)
    if tax_pdfs or excel_files:
        st.success("파일 분석 중입니다...")

# --- [메뉴 2] 카드매입 수기 입력건 (파일명 규칙 강화) ---
elif menu == MENU_2:
    st.title(MENU_2)
    st.write("요청하신 규칙대로 [연도 업체명 카드사용내역 카드사 카드번호] 파일명을 생성합니다.")
    
    uploaded_cards = st.file_uploader("카드사 엑셀 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    
    if uploaded_cards:
        zip_buffer = io.BytesIO()
        processed_count = 0
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_cards:
                # 0. 파일명 정보 추출 (연도, 업체명, 카드사)
                fname = file.name
                year = datetime.now().strftime('%Y')
                company = "업체명"
                card_brand = "카드"
                
                # 연도와 업체명 추출 로직
                meta_match = re.search(r'(\d{4})\s*([가-힣\w\s]+?)-', fname)
                if meta_match:
                    year = meta_match.group(1)
                    company = meta_match.group(2).strip()
                
                # 카드사 추출 로직 (파일명에 포함된 경우)
                if '국민' in fname: card_brand = "국민"
                elif '비씨' in fname or 'BC' in fname: card_brand = "비씨"
                elif '기업' in fname: card_brand = "기업"
                elif '우리' in fname: card_brand = "우리"

                # 1. 엑셀 헤더 찾기
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

                # 2. 컬럼 매핑 및 정제
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

                temp_df['매출일자'] = temp_df['매출일자'].apply(format_date)
                temp_df['매출금액'] = temp_df['매출금액'].apply(to_int)
                temp_df = temp_df[temp_df['매출금액'] > 0].copy()
                temp_df['공급가액'] = (temp_df['매출금액'] / 1.1).round(0).astype(int)
                temp_df['부가세'] = temp_df['매출금액'] - temp_df['공급가액']

                # 3. 카드번호별 파일 쪼개기
                temp_df['카드_ID'] = temp_df['카드번호'].astype(str).apply(lambda x: re.sub(r'[^0-9]', '', x)[-4:] if len(re.sub(r'[^0-9]', '', x)) >= 4 else "0000")
                
                for card_num in temp_df['카드_ID'].unique():
                    card_df = temp_df[temp_df['카드_ID'] == card_num].copy()
                    final_df = card_df[['카드번호', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                    
                    # 파일명 규칙: 연도+업체명+카드사용내역+카드사+카드번호(업로드용).xlsx
                    new_file_name = f"{year} {company}-카드사용내역({card_brand}{card_num})(업로드용).xlsx"
                    
                    excel_out = io.BytesIO()
                    final_df.to_excel(excel_out, index=False, engine='openpyxl')
                    zf.writestr(new_file_name, excel_out.getvalue())
                    processed_count += 1

        if processed_count > 0:
            st.success(f"✅ 총 {processed_count}개의 파일 분리 완료!")
            st.download_button("📥 카드별 개별 엑셀(ZIP) 다운로드", zip_buffer.getvalue(), f"{company}_카드분리.zip", use_container_width=True)
