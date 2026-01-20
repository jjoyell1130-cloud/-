import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re
import pdfplumber
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. 기초 엔진: 기존 동일] ---
try:
    font_path = "malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        FONT_NAME = 'MalgunGothic'
    else: FONT_NAME = 'Helvetica'
except: FONT_NAME = 'Helvetica'

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        s = str(val).replace('"', '').replace(',', '').strip()
        return int(float(s))
    except: return 0

# --- [기존 PDF 추출 및 생성 함수: 내용 유지] ---
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
            is_sales, is_purchase = "매출" in file.name, "매입" in file.name
            if (is_sales or is_purchase) and pages:
                last_page_lines = pages[-1].split("\n")
                for line in reversed(last_page_lines):
                    if any(k in line for k in ["합계", "총계", "누계"]):
                        # (중략: 기존 로직 동일)
                        amts = re.findall(amt_pattern, line)
                        if amts:
                            if is_sales: data["매출액"] = amts[0]
                            else: data["매입액"] = amts[0]
                            break
    return data

def make_pdf_stream(data, title, biz_name, date_range):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    # (중략: 기존 PDF 생성 로직 동일)
    c.save(); buffer.seek(0)
    return buffer

# --- [2. 세션 및 레이아웃] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", "menu_1": "⚖️ 마감작업", "menu_2": "📁 매출매입장 PDF 변환", "menu_3": "💳 카드매입 수기입력건",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}
감기 조심하시고 건강이 최고인거 아시죠? ^.<
부가세 신고 마무리되어 전체 자료 전달드립니다.
=첨부파일=
-부가세 신고서
-매출장: {매출액}원
-매입장: {매입액}원
-접수증 > {결과}: {세액}원
☆★{결과}예정 8월 말 정도"""
    }
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, 
                       type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

curr = st.session_state.selected_menu
st.title(curr)
st.divider()

# --- [3. 메뉴별 메인 로직] ---
if curr == st.session_state.config["menu_0"]:
    # (중략: 기존 Home 로직 동일)
    st.subheader("🔗 바로가기")
    c_top1, c_top2 = st.columns(2)
    with c_top1: st.link_button("🌐 WEHAGO", "https://www.wehago.com/#/main", use_container_width=True)
    with c_top2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    st.divider()
    st.subheader("⌨️ 전표 입력 가이드")
    acc_data = [["유류대", "매입/불공제", "차량유지비", "822"], ["편의점", "매입/불공제", "여비교통비", "812"], ["다이소", "매입", "소모품비", "830"]]
    st.dataframe(pd.DataFrame(acc_data, columns=["항목", "구분", "계정과목", "코드"]), use_container_width=True, hide_index=True)

elif curr == st.session_state.config["menu_1"]:
    # (중략: 기존 마감작업 로직 동일)
    st.subheader("📝 완성된 안내문 (복사용)")
    p_h = st.file_uploader("📄 국세청 PDF", type=['pdf'], accept_multiple_files=True, key="m1_pdf")
    p_l = st.file_uploader("📊 매출매입장 PDF", type=['pdf'], accept_multiple_files=True, key="m1_ledger")
    if p_h or p_l:
        all_up = (p_h if p_h else []) + (p_l if p_l else [])
        res = extract_data_from_pdf(all_up)
        biz = all_up[0].name.split("_")[0] if "_" in all_up[0].name else "업체"
        msg = st.session_state.config["prompt_template"].format(업체명=biz, 결과=res["결과"], 매출액=res["매출액"], 매입액=res["매입액"], 세액=res["세액"])
        st.code(msg, language="text")

elif curr == st.session_state.config["menu_2"]:
    # (중략: 기존 PDF 변환 로직 동일)
    f_excel = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'], key="m2_up")
    if f_excel:
        st.success(f"{f_excel.name} 변환 준비 완료")

elif curr == "💳 카드매입 수기입력건":
    st.info("💡 카드내역서들을 한 번에 올리면 각각 카드번호별로 분류하여 ZIP으로 묶어줍니다.")
    card_ups = st.file_uploader("카드사 파일 업로드 (다중 선택)", type=['xlsx', 'csv', 'xls'], accept_multiple_files=True, key="card_m3_fix")
    
    if card_ups:
        zip_main_buf = io.BytesIO()
        # 압축파일 명칭을 위한 첫 번째 업체명 추출
        first_fn = card_ups[0].name
        main_biz = first_fn.split('_')[0].split('-')[0].split(' ')[0].strip()
        
        with zipfile.ZipFile(zip_main_buf, "a", zipfile.ZIP_DEFLATED) as zf_main:
            for card_up in card_ups:
                fn = card_up.name
                # 1. 파일명에서 정보 추출 (이디야 안산한대점 등)
                biz_name = fn.split('_')[0].split('-')[0].split(' ')[0].strip()
                
                # 2. 카드사 판별
                card_company = "카드사"
                for c_key in ["신한", "삼성", "현대", "국민", "KB", "우리", "농협", "NH", "하나", "롯데"]:
                    if c_key in fn:
                        card_company = c_key.replace("KB", "국민").replace("NH", "농협")
                        break
                
                # 3. 파일명에서 카드번호 4자리 우선 추출
                card_id_match = re.search(r'(\d{4})', fn)
                fn_card_id = card_id_match.group(1) if card_id_match else None

                try:
                    if fn.endswith('.csv'):
                        try: df_raw = pd.read_csv(card_up, header=None, encoding='cp949')
                        except: card_up.seek(0); df_raw = pd.read_csv(card_up, header=None, encoding='utf-8-sig')
                    else:
                        df_raw = pd.read_excel(card_up, header=None)

                    # 헤더 탐색
                    header_idx = None
                    for i, row in df_raw.iterrows():
                        row_str = " ".join([str(v) for v in row.values if pd.notna(v)]).replace("\n", "")
                        if ('가맹점' in row_str or '거래처' in row_str) and ('금액' in row_str or '합계' in row_str):
                            header_idx = i; break
                    
                    if header_idx is not None:
                        df = df_raw.iloc[header_idx+1:].copy()
                        df.columns = [str(c).replace("\n", " ").strip() for c in df_raw.iloc[header_idx].values]
                        
                        d_col = next((c for c in df.columns if any(k in str(c) for k in ['거래일', '이용일', '일자', '승인일'])), df.columns[0])
                        p_col = next((c for c in df.columns if any(k in str(c) for k in ['가맹점', '거래처', '상호'])), None)
                        a_col = next((c for c in df.columns if any(k in str(c) for k in ['금액', '합계', '승인금액'])), None)
                        n_col = next((c for c in df.columns if any(k in str(c) for k in ['카드', '번호'])), None)

                        if p_col and a_col:
                            df[a_col] = df[a_col].apply(to_int)
                            df = df[df[a_col] != 0].copy()
                            
                            res_df = pd.DataFrame()
                            res_df['일자'] = df[d_col].astype(str)
                            res_df['거래처'] = df[p_col].astype(str)
                            res_df['품명'] = "카드매입"
                            res_df['공급가액'] = (df[a_col] / 1.1).round(0).astype(int)
                            res_df['부가세'] = df[a_col] - res_df['공급가액']
                            res_df['합계'] = df[a_col]

                            # 카드번호 결정 (파일명 번호가 있으면 그것을 사용, 없으면 데이터 내부에서 추출)
                            if fn_card_id:
                                res_df['card_group'] = fn_card_id
                            elif n_col:
                                res_df['card_group'] = df[n_col].astype(str).str.replace(r'[^0-9]', '', regex=True).str[-4:]
                            else:
                                res_df['card_group'] = "0000"

                            for c_num, group in res_df.groupby('card_group'):
                                if not c_num or c_num == 'nan': c_num = "0000"
                                out_buf = io.BytesIO()
                                with pd.ExcelWriter(out_buf, engine='xlsxwriter') as writer:
                                    group.drop(columns=['card_group']).to_excel(writer, index=False)
                                
                                # [요청반영] 내부 파일명: 업체명_카드사_뒷자리_(업로드용).xlsx
                                final_fn = f"{biz_name}_{card_company}_{c_num}_(업로드용).xlsx"
                                zf_main.writestr(final_fn, out_buf.getvalue())
                except Exception as e:
                    st.error(f"{fn} 오류: {e}")
        
        st.success(f"✅ {main_biz} 외 변환 완료!")
        # [요청반영] 압축파일 이름: 업체명_카드매입_(업로드용).zip
        st.download_button(f"📥 {main_biz}_카드매입_(업로드용) 다운로드", zip_main_buf.getvalue(), f"{main_biz}_카드매입_(업로드용).zip", use_container_width=True)
