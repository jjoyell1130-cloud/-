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

# --- 2. 메뉴 선택 ---
st.set_page_config(page_title="세무비서 업무자동화", layout="wide")
menu = st.sidebar.selectbox("📂 업무 선택", ["매출매입장 PDF & 안내문", "카드내역 통합 정제"])

# --- [메뉴 1] 매출매입장 PDF & 안내문 생성 로직 ---
if menu == "매출매입장 PDF & 안내문":
    st.title("⚖️ 부가세 신고 안내 및 장부 생성")
    
    with st.sidebar:
        st.header("파일 업로드")
        tax_pdfs = st.file_uploader("1. 국세청 PDF (선택사항)", type=['pdf'], accept_multiple_files=True)
        excel_files = st.file_uploader("2. 매출매입장 엑셀", type=['xlsx'], accept_multiple_files=True)

    # (기존의 PDF 분석 및 엑셀 합산 로직 실행...)
    # ... [이전 단계에서 완성한 안내문 생성 코드 위치] ...
    st.info("왼쪽 사이드바에 파일을 올려주세요. 장부 PDF 생성과 카톡 안내문이 동시에 준비됩니다.")

# --- [메뉴 2] 카드내역 통합 정제 로직 ---
elif menu == "카드내역 통합 정제":
    st.title("💳 카드사별 내역 통합 및 세액 산출")
    st.write("여러 카드사의 엑셀 자료를 업로드하면 **카드별 구분/필요정보 추출/공급가액-부가세 분리**를 한 번에 수행합니다.")
    
    uploaded_cards = st.file_uploader("카드사 엑셀 파일들을 모두 선택하세요", type=['xlsx', 'xls'], accept_multiple_files=True)
    
    if uploaded_cards:
        all_rows = []
        for file in uploaded_cards:
            try:
                # 카드 별칭 추출 (파일명 활용)
                card_name = file.name.split('(')[-1].split(')')[0] if '(' in file.name else file.name.split('.')[0]
                df = pd.read_excel(file)
                df.columns = [str(c).strip() for c in df.columns]

                # 표준 컬럼 매핑
                col_map = {
                    '일자': ['이용일자', '매출일자', '승인일자', '거래일자', '일자'],
                    '가맹점명': ['가맹점명', '가맹점명칭', '이용처', '상호'],
                    '사업자번호': ['사업자번호', '사업자등록번호', '가맹점사업자번호'],
                    '매출금액': ['이용금액', '매출금액', '승인금액', '결제금액', '합계']
                }

                res_df = pd.DataFrame()
                res_df['카드구분'] = [card_name] * len(df)
                
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in c for a in aliases)), None)
                    res_df[std] = df[actual] if actual else ""

                # 숫자 정제 및 계산
                def to_int(x):
                    try: return int(float(str(x).replace(',', '').split('.')[0]))
                    except: return 0

                res_df['매출금액'] = res_df['매출금액'].apply(to_int)
                res_df = res_df[res_df['매출금액'] > 0].copy() # 0원 데이터 제외
                
                res_df['공급가액'] = (res_df['매출금액'] / 1.1).round(0).astype(int)
                res_df['부가세'] = res_df['매출금액'] - res_df['공급가액']
                
                all_rows.append(res_df)
            except Exception as e:
                st.error(f"⚠️ {file.name} 처리 중 오류 발생: {e}")

        if all_rows:
            final_card_df = pd.concat(all_rows, ignore_index=True)
            # 순서 재배치
            final_card_df = final_card_df[['카드구분', '일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
            
            st.success(f"✅ 총 {len(uploaded_cards)}개 카드사, {len(final_card_df)}건의 내역이 통합되었습니다.")
            st.dataframe(final_card_df, use_container_width=True)

            # 엑셀 다운로드
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_card_df.to_excel(writer, index=False, sheet_name='통합카드내역')
            
            st.download_button(
                label="📥 통합 정제된 엑셀 다운로드",
                data=output.getvalue(),
                file_name="카드내역_통합정리_소울인테리어.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
