import streamlit as st
import pandas as pd
import io
import os
import urllib.request
import zipfile
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 1. 환경 설정 및 폰트 로드 ---
def load_font():
    font_path = "nanum.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except: return False
    try:
        pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        return True
    except: return False

font_status = load_font()
f_name = 'NanumGothic' if font_status else 'Helvetica'

# --- 2. 사이드바 메뉴 선택 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")
menu = st.sidebar.selectbox("📂 업무 선택", ["매출매입장 PDF & 안내문", "카드매입 수기 입력건 엑셀 변환"])

# --- [메뉴 1] 매출매입장 PDF & 안내문 생성 ---
if menu == "매출매입장 PDF & 안내문":
    st.title("⚖️ 부가세 신고 안내 및 장부 생성")
    st.write("국세청 PDF와 장부 엑셀을 결합하여 최종 안내문과 PDF 장부를 생성합니다.")
    
    with st.sidebar:
        st.header("파일 업로드")
        tax_pdfs = st.file_uploader("1. 국세청 PDF (신고서/접수증)", type=['pdf'], accept_multiple_files=True)
        excel_files = st.file_uploader("2. 매출매입장 엑셀", type=['xlsx'], accept_multiple_files=True)

    # (이전 단계의 매출매입장 분석 및 안내문 생성 로직이 이 자리에 위치합니다)
    st.info("파일을 업로드하면 하단에 업체별 안내문이 생성됩니다.")

# --- [메뉴 2] 카드매입 수기 입력건 엑셀 변환 ---
elif menu == "카드매입 수기 입력건 엑셀 변환":
    st.title("💳 카드매입 수기 입력건 엑셀 변환")
    st.write("카드사별 원본 엑셀을 업로드하면 **수기 입력에 최적화된 양식**으로 자동 변환합니다.")
    
    uploaded_cards = st.file_uploader("카드사 엑셀 파일들을 선택하세요", type=['xlsx', 'xls'], accept_multiple_files=True)
    
    if uploaded_cards:
        all_rows = []
        for file in uploaded_cards:
            try:
                # 파일명에서 카드 구분 정보 추출
                card_id = file.name.split('(')[-1].split(')')[0] if '(' in file.name else file.name.split('.')[0]
                
                # 엑셀 읽기
                df = pd.read_excel(file)
                df.columns = [str(c).strip() for c in df.columns]

                # 표준 컬럼 매핑 (카드사별 다양한 명칭 대응)
                col_map = {
                    '매출일자': ['이용일자', '매출일자', '승인일자', '거래일자', '일자'],
                    '가맹점명': ['가맹점명', '가맹점명칭', '이용처', '상호'],
                    '사업자번호': ['사업자번호', '사업자등록번호', '가맹점사업자번호'],
                    '매출금액': ['이용금액', '매출금액', '승인금액', '결제금액', '합계']
                }

                res_df = pd.DataFrame()
                res_df['카드번호/구분'] = [card_id] * len(df)
                
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in c for a in aliases)), None)
                    res_df[std] = df[actual] if actual else ""

                # 숫자 데이터 정제 함수
                def to_int(x):
                    try: 
                        val = str(x).replace(',', '').split('.')[0]
                        return int(float(val))
                    except: return 0

                res_df['매출금액'] = res_df['매출금액'].apply(to_int)
                
                # 금액이 있는 행만 유지
                res_df = res_df[res_df['매출금액'] > 0].copy()
                
                # 3. 공급가액(1.1 나누기), 부가세 계산
                res_df['공급가액'] = (res_df['매출금액'] / 1.1).round(0).astype(int)
                res_df['부가세'] = res_df['매출금액'] - res_df['공급가액']
                
                # 2. 지정 정보 외 삭제 및 순서 정렬
                res_df = res_df[['카드번호/구분', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                
                all_rows.append(res_df)
                
            except Exception as e:
                st.error(f"⚠️ {file.name} 변환 중 오류: {e}")

        if all_rows:
            final_card_df = pd.concat(all_rows, ignore_index=True)
            
            st.divider()
            st.success(f"✅ 총 {len(all_rows)}개 카드사 데이터 변환 성공!")
            
            # 미리보기 및 다운로드
            st.dataframe(final_card_df, use_container_width=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_card_df.to_excel(writer, index=False, sheet_name='수기입력용_변환데이터')
            
            st.download_button(
                label="📥 변환된 엑셀 파일 다운로드",
                data=output.getvalue(),
                file_name="카드매입_수기입력용_변환.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
