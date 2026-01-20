import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re
import pdfplumber

# --- [1. 기초 엔진] ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        # 숫자 사이의 콤마, 따옴표 등을 제거하고 정수로 변환
        s = str(val).replace('"', '').replace(',', '').strip()
        return int(float(s))
    except: return 0

# (PDF 관련 함수 등은 기존과 동일하므로 생략 가능하나 전체 작동을 위해 유지)
def extract_data_from_pdf(files):
    data = {"매출액": "0", "매입액": "0", "세액": "0", "결과": "납부"}
    amt_pattern = r"[\d,]{4,15}" 
    for file in files:
        with pdfplumber.open(file) as pdf:
            pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
            full_text_clean = "\n".join(pages).replace(" ", "")
            if any(k in file.name for k in ["신고서", "접수증"]):
                tax_match = re.search(r"(납부할세액|차가감세액|합계세액|세액합계)[:]*([-]*[\d,]+)", full_text_clean)
                if tax_match:
                    raw_amt = tax_match.group(2).replace(",", "")
                    amt = int(raw_amt)
                    data["결과"] = "환급" if "환급" in full_text_clean or amt < 0 else "납부"
                    data["세액"] = f"{abs(amt):,}"
    return data

# --- [2. 세션 및 레이아웃] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", "menu_1": "⚖️ 마감작업", "menu_2": "📁 매출매입장 PDF 변환", "menu_3": "💳 카드매입 수기입력건",
        "prompt_template": "*{업체명} 부가세 신고현황..."
    }
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True):
            st.session_state.selected_menu = m_name
            st.rerun()

curr = st.session_state.selected_menu
st.title(curr)

# --- [3. 메인 로직 - 여기서 if/elif 들여쓰기가 중요합니다] ---
if curr == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    # (Home 내용 생략)

elif curr == st.session_state.config["menu_1"]:
    st.subheader("📝 완성된 안내문")
    # (마감작업 내용 생략)

elif curr == st.session_state.config["menu_2"]:
    st.subheader("📁 매출매입장 변환")
    # (PDF 변환 내용 생략)

elif curr == st.session_state.config["menu_3"]:
    st.info("카드내역서 엑셀파일을 업로드하시면 위하고 업로드용으로 자동 변환됩니다.")
    card_up = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'])
    
    if card_up:
        biz_name = card_up.name.split('-')[0].split('_')[0].strip()
        try:
            # 1. 파일 읽기 (신한카드 CSV 따옴표 완벽 대응)
            if card_up.name.endswith('.csv'):
                try: raw_df = pd.read_csv(card_up, header=None, encoding='cp949', quotechar='"')
                except: card_up.seek(0); raw_df = pd.read_csv(card_up, header=None, encoding='utf-8-sig', quotechar='"')
            else:
                raw_df = pd.read_excel(card_up, header=None)

            # 2. 신한카드 헤더 ("이용카드\n(뒤4자리)") 찾기
            header_idx = None
            for i, row in raw_df.iterrows():
                row_str = "".join(map(str, row.values)).replace("\n", "").replace(" ", "")
                if '가맹점명' in row_str and '이용금액' in row_str:
                    header_idx = i
                    break
            
            if header_idx is not None:
                # 제목행 정제 (줄바꿈 제거)
                cols = [str(c).replace("\n", " ").replace('"', '').strip() for c in raw_df.iloc[header_idx]]
                df = raw_df.iloc[header_idx + 1:].copy()
                df.columns = cols
                df = df.dropna(how='all', axis=0)

                # 3. 데이터 매핑
                d_col = next((c for c in df.columns if '거래일' in c or '일자' in c), df.columns[0])
                p_col = next((c for c in df.columns if '가맹점' in c or '거래처' in c), None)
                a_col = next((c for c in df.columns if '이용금액' in c or '합계' in c), None)
                n_col = next((c for c in df.columns if '뒤4자리' in c or '카드' in c), None)

                if p_col and a_col:
                    df[a_col] = df[a_col].apply(to_int)
                    df = df[df[a_col] > 0].copy()

                    # 위하고 양식으로 새 데이터프레임 생성
                    res_df = pd.DataFrame()
                    res_df['일자'] = df[d_col].astype(str).str.replace('"', '').str.strip()
                    res_df['거래처'] = df[p_col].astype(str).str.replace('"', '').str.strip()
                    res_df['품명'] = "카드매입"
                    res_df['공급가액'] = (df[a_col] / 1.1).round(0).astype(int)
                    res_df['부가세'] = df[a_col] - res_df['공급가액']
                    res_df['합계'] = df[a_col]
                    
                    # 카드번호 뒷자리 추출
                    card_ids = df[n_col].astype(str).str.extract(r'(\d{4})').fillna("카드")[0]
                    res_df['card_group'] = card_ids

                    # 4. 압축 파일 생성
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        for c_num, group in res_df.groupby('card_group'):
                            out_buf = io.BytesIO()
                            with pd.ExcelWriter(out_buf, engine='xlsxwriter') as writer:
                                group.drop(columns=['card_group']).to_excel(writer, index=False)
                            zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", out_buf.getvalue())
                    
                    st.success(f"✅ {biz_name} 변환 완료!")
                    st.download_button("📥 ZIP 다운로드", z_buf.getvalue(), f"{biz_name}_변환결과.zip")
            else:
                st.error("파일에서 데이터 제목줄을 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
