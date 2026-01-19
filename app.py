import streamlit as st
import pandas as pd
import io
import re
import zipfile
from datetime import datetime

# --- 기본 설정 ---
st.set_page_config(page_title="세무비서 업무자동화 시스템", layout="wide")

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

# --- 사이드바 메뉴 구성 ---
st.sidebar.title("🗂️ 업무 선택")
# 초기값을 "선택하세요"로 설정하여 홈 화면 유도
menu = st.sidebar.radio(
    "수행할 업무를 클릭하세요:",
    ["🏠 홈 (사용 안내)", "⚖️ 매출매입장 PDF & 안내문", "💳 카드별 개별 엑셀 변환"]
)

# --- [홈 화면] ---
if menu == "🏠 홈 (사용 안내)":
    st.title("🚀 세무비서 업무자동화 시스템")
    st.markdown("---")
    st.subheader("원하시는 업무를 왼쪽 메뉴에서 선택해 주세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("### 1. 매출매입장 PDF & 안내문\n- 국세청 신고서 PDF 분석\n- 매출/매입 합계 자동 계산\n- 카톡 발송용 안내문구 생성")
    with col2:
        st.success("### 2. 카드별 개별 엑셀 변환\n- 통합 카드 엑셀을 카드사/번호별로 분리\n- 파일명 자동 생성 (업로드용)\n- 매출일자 간소화 및 부가세 자동 계산")

# --- [메뉴 1] 매출매입장 로직 ---
elif menu == "⚖️ 매출매입장 PDF & 안내문":
    st.title("⚖️ 매출매입장 PDF & 안내문 생성")
    # (기존 매출매입장 분석 및 안내문 생성 코드 로직...)
    st.info("파일을 업로드하면 분석이 시작됩니다.")

# --- [메뉴 2] 카드사별 개별 엑셀 분리 ---
elif menu == "💳 카드별 개별 엑셀 변환":
    st.title("💳 카드매입 수기 입력건 (자동분리)")
    st.write("요청하신 규칙: `연도 업체명-카드사용내역(카드사+번호)(업로드용).xlsx`")
    
    uploaded_cards = st.file_uploader("엑셀 파일 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    
    if uploaded_cards:
        zip_buffer = io.BytesIO()
        processed_count = 0
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_cards:
                # 파일 정보 추출
                fname = file.name
                year = datetime.now().strftime('%Y')
                company = "업체명"
                card_brand = "카드"
                
                meta_match = re.search(r'(\d{4})\s*([가-힣\w\s]+?)-', fname)
                if meta_match:
                    year = meta_match.group(1)
                    company = meta_match.group(2).strip()
                
                # 카드사 식별
                if '국민' in fname: card_brand = "국민"
                elif '비씨' in fname or 'BC' in fname: card_brand = "비씨"
                elif '기업' in fname: card_brand = "기업"
                elif '우리' in fname: card_brand = "우리"

                # 엑셀 읽기
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

                # 데이터 추출 및 정제
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

                # 카드번호 뒷자리별 파일 분할
                temp_df['카드_ID'] = temp_df['카드번호'].astype(str).apply(lambda x: re.sub(r'[^0-9]', '', x)[-4:] if len(re.sub(r'[^0-9]', '', x)) >= 4 else "0000")
                
                for card_num in temp_df['카드_ID'].unique():
                    card_df = temp_df[temp_df['카드_ID'] == card_num].copy()
                    final_df = card_df[['카드번호', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                    
                    # 파일명 규칙 적용
                    new_file_name = f"{year} {company}-카드사용내역({card_brand}{card_num})(업로드용).xlsx"
                    
                    excel_out = io.BytesIO()
                    with pd.ExcelWriter(excel_out, engine='openpyxl') as writer:
                        final_df.to_excel(writer, index=False)
                    zf.writestr(new_file_name, excel_out.getvalue())
                    processed_count += 1

        if processed_count > 0:
            st.success(f"✅ 총 {processed_count}개의 파일 분리 완료!")
            st.download_button("📥 카드별 개별 엑셀(ZIP) 다운로드", zip_buffer.getvalue(), f"{company}_카드분리.zip", use_container_width=True)
