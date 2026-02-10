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

# --- [1. 기초 엔진] ---
try:
    font_path = "malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        FONT_NAME = 'MalgunGothic'
    else:
        FONT_NAME = 'Helvetica'
except:
    FONT_NAME = 'Helvetica'

def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        s = re.sub(r'[^0-9.-]', '', str(val)).strip()
        return int(float(s))
    except: return 0

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
                        amts = re.findall(amt_pattern, line)
                        if amts:
                            if is_sales: data["매출액"] = amts[0]
                            else: data["매입액"] = amts[0]
                            break
    return data

def make_pdf_stream(data, title, biz_name, date_range):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    rows_per_page = 26
    actual_item_count = 0 
    summary_keywords = ['합계', '월계', '분기', '반기', '누계']
    
    # [수정] 데이터 전체의 NaN 값을 빈 문자열로 처리하여 오류 방지
    data = data.fillna("")
    
    y_start = height - 133
    for i in range(len(data)):
        if i % rows_per_page == 0:
            if i > 0: c.showPage()
            p_num = (i // rows_per_page) + 1
            c.setFont(FONT_NAME, 18); c.drawCentredString(width/2, height - 60, title)
            c.setFont(FONT_NAME, 10); c.drawString(50, height - 90, f"회사명 : {biz_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            yh = 680 
            c.setLineWidth(1.2); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(FONT_NAME, 9); c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자")
            c.drawString(180, yh, "거래처(적요)"); c.drawRightString(420, yh, "공급가액")
            c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
            c.line(40, yh - 8, 555, yh - 8); y_start = yh - 28
            
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        # [수정] 카드/현금영수증 매출 시 거래처가 NaN인 경우 처리
        raw_partner = str(row.get('거래처', '')).strip()
        if raw_partner == "":
            # 비고나 유형 컬럼에서 카드/현금 매출 정보 가져오기
            raw_partner = str(row.get('비고', row.get('유형', '카드/현금 매출')))
            
        txt = (str(row.get('번호', '')) + raw_partner).replace(" ", "")
        is_summary = any(k in txt for k in summary_keywords)
        
        c.setFont(FONT_NAME, 8.5)
        if is_summary:
            c.setFont(FONT_NAME, 9); c.drawString(90, cur_y, raw_partner)
            c.line(40, cur_y + 16, 555, cur_y + 16); c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.drawString(45, cur_y, str(actual_item_count))
            raw_date = row.get('전표일자', row.get('일자', ''))
            c.drawString(85, cur_y, str(raw_date)[:10] if raw_date != "" else "")
            c.drawString(170, cur_y, raw_partner[:25])
            c.setStrokeColor(colors.lightgrey); c.line(40, cur_y - 7, 555, cur_y - 7); c.setStrokeColor(colors.black)
            
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
        
    c.save(); buffer.seek(0)
    return buffer

# --- 이하 세션 로직 및 메뉴 구성 (기존 코드 유지) ---
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

if curr == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c_top1, c_top2 = st.columns(2)
    with c_top1: st.link_button("🌐 WEHAGO", "https://www.wehago.com/#/main", use_container_width=True)
    with c_top2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    c_bot1, c_bot2, c_bot3, c_bot4 = st.columns(4)
    with c_bot1: st.link_button("📋 신고리스트", "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?gid=1260813981#gid=1260813981", use_container_width=True)
    with c_bot2: st.link_button("📅 부가세 상반기", "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3", use_container_width=True)
    with c_bot3: st.link_button("📅 부가세 하반기", "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r", use_container_width=True)
    with c_bot4: st.link_button("💳 카드매입자료", "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe", use_container_width=True)
    st.divider()
    st.subheader("⌨️ 전표 입력 가이드")
    acc_data = [["유류대", "매입/불공제", "차량유지비", "822"], ["편의점", "매입/불공제", "여비교통비", "812"], ["다이소", "매입", "소모품비", "830"], ["식당", "매입/불공제", "복리후생비", "811"], ["거래처(물건)", "매입", "상품", "146"], ["홈쇼핑/인터넷구매", "매입", "소모품비", "830"], ["주장/소액세금", "일반", "차량유지비", "822"], ["휴게소", "공제확인", "차량/여비교통", ""], ["전기요금", "매입", "전력비", ""], ["수도요금", "일반", "수도광열비", ""], ["통신비", "매입", "통신비", "814"], ["금융결제원", "일반", "세금과공과", ""], ["약국", "일반", "소모품비", "830"], ["모텔", "일반", "여비교통비/출장비", ""], ["보안(캡스)/홈페이지", "매입", "지급수수료", "831"], ["아울렛(작업복)", "매입", "소모품비", ""], ["컴퓨터 A/S", "매입", "수선비", "820"], ["결제대행업체(PG)", "일반", "소모품비", "830"], ["신용카드알림", "일반", "지급수수료", ""], ["휴대폰소액결제", "일반", "소모품비", ""], ["병원", "일반", "복리후생비", ""], ["로카모빌리티", "일반", "소모품비", ""], ["소프트웨어 개발", "매입", "지급수수료", "831"]]
    df_acc = pd.DataFrame(acc_data, columns=["항목", "구분", "계정과목", "코드"])
    st.dataframe(df_acc, use_container_width=True, height=600, hide_index=True)

elif curr == st.session_state.config["menu_1"]:
    st.subheader("📝 안내문")
    p_h = st.session_state.get("m1_pdf_up", [])
    p_l = st.session_state.get("m1_ledger_up", [])
    all_up = (p_h if p_h else []) + (p_l if p_l else [])
    if all_up:
        res = extract_data_from_pdf(all_up)
        biz = all_up[0].name.split("_")[0] if "_" in all_up[0].name else all_up[0].name.split(" ")[0]
        msg = st.session_state.config["prompt_template"].format(업체명=biz, 결과=res["결과"], 매출액=res["매출액"], 매입액=res["매입액"], 세액=res["세액"])
        st.code(msg, language="text")
    else:
        st.info("파일을 업로드하면 안내문이 이곳에 생성됩니다.")
    st.divider()
    col1, col2 = st.columns(2)
    with col1: st.file_uploader("📄 국세청 PDF", type=['pdf'], accept_multiple_files=True, key="m1_pdf_up")
    with col2: st.file_uploader("📊 매출매입장 PDF", type=['pdf'], accept_multiple_files=True, key="m1_ledger_up")
    st.divider()
    with st.expander("✉️ 안내문 템플릿 수정", expanded=False):
        new_template = st.text_area("템플릿 내용", value=st.session_state.config["prompt_template"], height=250)
        if st.button("템플릿 저장"):
            st.session_state.config["prompt_template"] = new_template
            st.success("템플릿이 저장되었습니다!")

elif curr == st.session_state.config["menu_2"]:
    f_excels = st.file_uploader("📊 엑셀 파일 업로드 (여러 파일 가능)", type=['xlsx'], accept_multiple_files=True, key="m2_up")
    if f_excels:
        zip_buf = io.BytesIO()
        first_biz = os.path.splitext(f_excels[0].name)[0].split(" ")[0]
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zf:
            for f_excel in f_excels:
                try:
                    df_all = pd.read_excel(f_excel)
                    pure_name = os.path.splitext(f_excel.name)[0].split(" ")[0]
                    try:
                        tmp_d = pd.to_datetime(df_all['전표일자'], errors='coerce').dropna()
                        d_range = f"{tmp_d.min().strftime('%Y-%m-%d')} ~ {tmp_d.max().strftime('%Y-%m-%d')}"
                    except: d_range = "2025년"
                    type_col = next((c for c in ['구분', '유형'] if c in df_all.columns), None)
                    if type_col:
                        for g in ['매출', '매입']:
                            tgt = df_all[df_all[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                            if not tgt.empty:
                                pdf_stream = make_pdf_stream(tgt, f"{g} 장", pure_name, d_range)
                                pdf_filename = f"2025 {pure_name} -하반기 {g}장.pdf"
                                zf.writestr(pdf_filename, pdf_stream.getvalue())
                except Exception as e: st.error(f"{f_excel.name} 오류: {e}")
        st.download_button("🎁 ZIP 다운로드", data=zip_buf.getvalue(), file_name=f"{first_biz}_매출매입장_모음.zip", use_container_width=True)

elif curr == st.session_state.config["menu_3"]:
    st.info("카드내역서 엑셀파일을 업로드하시면 위하고 업로드용으로 자동 변환됩니다.")
    card_ups = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'], accept_multiple_files=True, key="card_m3_final")
    if card_ups:
        z_buf = io.BytesIO()
        success_count = 0
        with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
            for card_up in card_ups:
                try:
                    if card_up.name.lower().endswith('.csv'):
                        try: raw_df = pd.read_csv(card_up, header=None, encoding='cp949')
                        except: card_up.seek(0); raw_df = pd.read_csv(card_up, header=None, encoding='utf-8-sig')
                    else:
                        try: raw_df = pd.read_excel(card_up, header=None)
                        except:
                            card_up.seek(0)
                            raw_df = pd.read_excel(card_up, header=None, engine='openpyxl')
                    
                    date_k, partner_k, biz_num_k, amt_k = ['이용일','일자','승인일'], ['가맹점','거래처','상호'], ['사업자등록번호','사업자번호','등록번호'], ['이용 금액','합계','승인금액','금액']
                    header_idx = None
                    for i, row in raw_df.iterrows():
                        row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                        if any(pk in row_str for pk in partner_k) and any(ak in row_str for ak in amt_k):
                            header_idx = i; break
                    
                    if header_idx is not None:
                        df = raw_df.iloc[header_idx+1:].copy()
                        df.columns = [str(c).strip() for c in raw_df.iloc[header_idx].values]
                        df = df.dropna(how='all', axis=0)
                        d_col = next((c for c in df.columns if any(k in str(c) for k in date_k)), None)
                        p_col = next((c for c in df.columns if any(k in str(c) for k in partner_k)), None)
                        b_col = next((c for c in df.columns if any(k in str(c) for k in biz_num_k)), None)
                        a_col = next((c for c in df.columns if any(k in str(c) for k in amt_k)), None)
                        
                        if p_col and a_col:
                            df['일자'] = pd.to_datetime(df[d_col], errors='coerce').dt.strftime('%Y-%m-%d')
                            df['사업자번호'] = df[b_col].astype(str).str.replace(r'[^0-9]', '', regex=True) if b_col else ""
                            df['거래처'], df['품명'] = df[p_col], "카드매입"
                            df['합계'] = df[a_col].apply(to_int)
                            df = df[df['합계'] > 0].copy()
                            df['공급가액'] = (df['합계'] / 1.1).round(0).astype(int)
                            df['부가세'] = df['합계'] - df['공급가액']
                            f_cols = ['일자', '거래처', '사업자번호', '품명', '공급가액', '부가세', '합계']
                            excel_buf = io.BytesIO()
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                df[f_cols].to_excel(writer, index=False)
                            original_fn = os.path.splitext(card_up.name)[0]
                            biz_part = original_fn.split('-')[0].strip()
                            if "2025" not in biz_part: biz_part = f"2025 {biz_part}"
                            final_filename = f"{biz_part} -하반기 카드매입_업로드용.xlsx"
                            zf.writestr(final_filename, excel_buf.getvalue())
                            success_count += 1
                except Exception as e: st.error(f"{card_up.name} 오류: {e}")
        
        if success_count > 0:
            st.success(f"✅ {success_count}개 파일 변환 완료!")
            st.download_button("📥 결과(ZIP) 다운로드", z_buf.getvalue(), f"카드매입_위하고용_모음.zip", use_container_width=True)
