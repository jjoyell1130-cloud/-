import streamlit as st
import pandas as pd
import pdfplumber
import io
import re
import zipfile

# --- 메뉴 이름 변수화 (오타 방지) ---
MENU_A = "🏠 매출매입장 PDF & 안내문"
MENU_B = "💳 카드매입 수기 입력건 엑셀 변환"

st.set_page_config(page_title="세무비서 자동화", layout="wide")

# --- 공통 유틸리티 함수 ---
def to_int(val):
    try:
        clean = re.sub(r'[^0-9-]', '', str(val))
        return int(float(clean)) if clean else 0
    except: return 0

def find_header_and_read(file):
    """헤더 행을 자동으로 찾아 읽는 함수"""
    try:
        # xlsxreader 등 기본 엔진 사용 (xlrd/xlsxwriter 설치 안 된 환경 대비)
        df_temp = pd.read_excel(file, header=None)
        keywords = ['일자', '가맹점', '금액', '사업자', '구분']
        header_row = 0
        for i in range(min(20, len(df_temp))):
            row_vals = [str(v) for v in df_temp.iloc[i].values]
            if any(k in v for k in keywords for v in row_vals):
                header_row = i
                break
        file.seek(0)
        df = pd.read_excel(file, header=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"파일 읽기 실패 ({file.name}): {e}")
        return None

# --- 사이드바 메뉴 ---
menu = st.sidebar.selectbox("📂 수행할 업무를 선택하세요", [MENU_A, MENU_B])

# --- [메뉴 1] 매출매입장 PDF & 안내문 ---
if menu == MENU_A:
    st.title(MENU_A)
    st.info("국세청 신고서 PDF와 매출매입 엑셀을 업로드하면 카톡 안내문이 생성됩니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        tax_pdfs = st.file_uploader("1. 국세청 PDF (신고서/접수증)", type=['pdf'], accept_multiple_files=True)
    with col2:
        excel_files = st.file_uploader("2. 매출매입장 엑셀", type=['xlsx'], accept_multiple_files=True)

    final_reports = {}

    # 1. PDF 분석
    if tax_pdfs:
        for f in tax_pdfs:
            with pdfplumber.open(f) as pdf:
                text = "".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                name_match = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", text)
                biz_name = name_match.group(1).strip() if name_match else f.name.split('_')[0]
                if biz_name not in final_reports: final_reports[biz_name] = {"vat": 0}
                vat_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", text)
                if vat_match:
                    val = to_int(vat_match.group(1))
                    final_reports[biz_name]["vat"] = -val if "환급" in text else val

    # 2. 엑셀 분석
    if excel_files:
        for ex in excel_files:
            df = find_header_and_read(ex)
            if df is not None:
                name_only = ex.name.split('_')[0]
                target_name = next((k for k in final_reports.keys() if k in name_only or name_only in k), name_only)
                if target_name not in final_reports: final_reports[target_name] = {"vat": 0}
                
                # 합계 계산
                s_sum = to_int(df[df['구분'].astype(str).str.contains('매출', na=False)]['합계'].sum())
                b_sum = to_int(df[df['구분'].astype(str).str.contains('매입', na=False)]['합계'].sum())
                final_reports[target_name].update({"sales": s_sum, "buys": b_sum})

    # 결과 출력
    if final_reports:
        st.subheader("✉️ 안내문 자동 생성 결과")
        for name, info in final_reports.items():
            with st.expander(f"📌 {name} 대표님 안내문", expanded=True):
                vat = info.get("vat", 0)
                status = "납부하실 세액" if vat >= 0 else "환급받으실 세액"
                msg = f"안녕하세요, {name} 대표님! 😊\n\n✅ 매출 합계: {info.get('sales', 0):,}원\n✅ 매입 합계: {info.get('buys', 0):,}원\n💰 최종 {status}: {abs(vat):,}원"
                if vat < 0: msg += "\n☆★ 환급은 8월 말경 입금될 예정입니다."
                st.text_area("카톡 복사용 문구", msg, height=150)

# --- [메뉴 2] 카드매입 수기 입력건 엑셀 변환 ---
elif menu == MENU_B:
    st.title(MENU_B)
    st.write("카드사 원본 엑셀을 수기 입력용 양식으로 통합합니다.")
    
    uploaded_cards = st.file_uploader("카드사 엑셀들을 선택하세요", type=['xlsx', 'xls'], accept_multiple_files=True)
    
    if uploaded_cards:
        all_rows = []
        for file in uploaded_cards:
            df = find_header_and_read(file)
            if df is not None:
                card_id = file.name.split('(')[-1].split(')')[0] if '(' in file.name else file.name.split('.')[0]
                col_map = {'매출일자': ['일자', '승인일', '이용일'], '가맹점명': ['가맹점', '이용처', '상호'],
                           '사업자번호': ['사업자', '등록번호'], '매출금액': ['금액', '합계', '승인금액']}
                
                res_df = pd.DataFrame()
                res_df['카드번호/구분'] = [card_id] * len(df)
                for std, aliases in col_map.items():
                    actual = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    res_df[std] = df[actual] if actual else ""
                
                res_df['매출금액'] = res_df['매출금액'].apply(to_int)
                res_df = res_df[res_df['매출금액'] > 0].copy()
                res_df['공급가액'] = (res_df['매출금액'] / 1.1).round(0).astype(int)
                res_df['부가세'] = res_df['매출금액'] - res_df['공급가액']
                
                all_rows.append(res_df[['카드번호/구분', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']])

        if all_rows:
            final_df = pd.concat(all_rows, ignore_index=True)
            st.success("✅ 변환 완료!")
            st.dataframe(final_df)
            
            # 엑셀 다운로드 (xlsxwriter 없이 기본 엔진 사용 시도)
            out = io.BytesIO()
            final_df.to_excel(out, index=False)
            st.download_button("📥 통합 엑셀 다운로드", out.getvalue(), "카드매입_수기입력용.xlsx")
