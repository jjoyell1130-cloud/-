import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re

# 1. 공통 숫자 변환 함수 (삼성/신한 금액 정제)
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        # 따옴표, 쉼표, 한글 등을 제거하고 숫자만 추출
        s = re.sub(r'[^\d.-]', '', str(val))
        return int(float(s))
    except: return 0

# 2. UI 설정 (기존 스타일 유지)
st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

with st.sidebar:
    st.markdown("### 📁 Menu")
    # 예림님이 사용하시던 기존 메뉴 리스트
    menus = ["🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"]
    for m in menus:
        if st.button(m, use_container_width=True, type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

curr = st.session_state.selected_menu

# --- [Menu 1: Home] ---
if curr == "🏠 Home":
    st.title("🏠 Home")
    st.write("세무 신고 업무 효율화 시스템입니다. 왼쪽 메뉴를 선택하세요.")

# --- [Menu 2: 마감작업 / PDF 변환] ---
# (이 부분은 예림님의 기존 코드가 있다면 그 로직이 그대로 들어가는 자리입니다.)
# 여기서는 예시로만 두었으니, 만약 기존 로직이 복잡하다면 Menu 3만 아래 내용으로 교체하세요.
elif curr == "⚖️ 마감작업":
    st.title("⚖️ 마감작업")
    st.write("마감 작업을 진행하는 메뉴입니다.")

elif curr == "📁 매출매입장 PDF 변환":
    st.title("📁 매출매입장 PDF 변환")
    st.write("PDF 파일을 엑셀로 변환하는 메뉴입니다.")

# --- [Menu 3: 카드매입 수기입력건] --- (이 부분이 핵심 수정 내용입니다)
elif curr == "💳 카드매입 수기입력건":
    st.title("💳 카드매입 수기입력건")
    st.info("신한카드(거래일/가맹점명)와 삼성카드(이용일/업종) 데이터를 모두 자동 인식합니다.")
    
    card_up = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'], key="card_m3")
    
    if card_up:
        raw_fn = os.path.splitext(card_up.name)[0]
        biz_name = raw_fn.split('-')[0].split('_')[0].strip()
        
        try:
            # 파일 읽기 (암호 풀린 상태 대응)
            if card_up.name.endswith('.csv'):
                try: raw_df = pd.read_csv(card_up, header=None, encoding='cp949')
                except: card_up.seek(0); raw_df = pd.read_csv(card_up, header=None, encoding='utf-8-sig')
            else:
                raw_df = pd.read_excel(card_up, header=None)

            # [핵심] 신한/삼성 UI를 모두 잡는 키워드 탐색
            date_k = ['거래일', '이용일', '일자', '승인일']
            partner_k = ['가맹점명', '거래처', '상호', '이용처']
            amt_k = ['이용금액', '합계', '승인금액', '금액']
            item_k = ['업종', '품명', '상품명', '종목']
            card_k = ['카드번호', '카드 No', '이용카드']

            # 데이터 시작 행 찾기
            header_idx = None
            for i, row in raw_df.iterrows():
                row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                if any(pk in row_str for pk in partner_k) and any(ak in row_str for ak in amt_k):
                    header_idx = i; break
            
            if header_idx is not None:
                df = raw_df.iloc[header_idx+1:].copy()
                df.columns = raw_df.iloc[header_idx].values
                df = df.dropna(how='all', axis=0)

                # 컬럼 매칭
                d_col = next((c for c in df.columns if any(k in str(c) for k in date_k)), None)
                p_col = next((c for c in df.columns if any(k in str(c) for k in partner_k)), None)
                a_col = next((c for c in df.columns if any(k in str(c) for k in amt_k)), None)
                i_col = next((c for c in df.columns if any(k in str(c) for k in item_k)), None)
                n_col = next((c for c in df.columns if any(k in str(c) for k in card_k)), None)

                if p_col and a_col:
                    df[a_col] = df[a_col].apply(to_int)
                    df = df[df[a_col] != 0].copy()
                    
                    # 표준 양식으로 내용 채우기 (공란 방지)
                    df['일자'] = df[d_col] if d_col else ""
                    df['거래처'] = df[p_col] if p_col else "상호미표기"
                    df['품명'] = df[i_col] if i_col is not None else "-" 
                    df['공급가액'] = (df[a_col] / 1.1).round(0).astype(int)
                    df['부가세'] = df[a_col] - df['공급가액']
                    df['합계'] = df[a_col]

                    # 카드번호별 파일 분리
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        df['card_id'] = df[n_col].astype(str).str.replace(r'[^0-9]', '', regex=True).str[-4:]
                        
                        final_cols = ['일자', '거래처', '품명', '공급가액', '부가세', '합계']
                        for c_num, group in df.groupby('card_id'):
                            if not c_num or c_num == 'nan' or c_num == '': continue
                            excel_buf = io.BytesIO()
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                group[final_cols].to_excel(writer, index=False)
                            zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", excel_buf.getvalue())
                    
                    st.success(f"✅ {biz_name} 분리 완료!")
                    st.download_button("📥 ZIP 파일 다운로드", z_buf.getvalue(), f"{biz_name}_결과.zip")
            else:
                st.error("파일의 데이터 시작점을 찾지 못했습니다.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
