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

# --- [1. 기초 엔진 및 PDF 추출] ---
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
        return int(float(str(val).replace(',', '')))
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
        txt = (str(row.get('번호', '')) + str(row.get('거래처', ''))).replace(" ", "")
        is_summary = any(k in txt for k in summary_keywords)
        c.setFont(FONT_NAME, 8.5)
        if is_summary:
            c.setFont(FONT_NAME, 9); c.drawString(90, cur_y, str(row.get('거래처', row.get('번호', ''))))
            c.line(40, cur_y + 16, 555, cur_y + 16); c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.drawString(45, cur_y, str(actual_item_count))
            raw_date = row.get('전표일자', row.get('일자', ''))
            c.drawString(85, cur_y, str(raw_date)[:10] if pd.notna(raw_date) else "")
            c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
            c.setStrokeColor(colors.lightgrey); c.line(40, cur_y - 7, 555, cur_y - 7); c.setStrokeColor(colors.black)
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
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

# --- [3. 메뉴별 메인 로직] ---
curr = st.session_state.selected_menu
st.title(curr)
st.divider()

# Menu 0: Home (수정됨)
if curr == st.session_state.config["menu_0"]:
    # 바로가기 링크
    st.subheader("🔗 업무 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("🌐 WEHAGO", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    
    st.divider()
    
    # 단축키 안내
    st.subheader("⌨️ 전표입력 구분코드 단축키")
    col_code1, col_code2 = st.columns(2)
    with col_code1:
        st.info("**[차변]**\n* **3** : 차변 (자산의 증가/비용의 발생)\n* **1** : 출금 (현금 지급 시)")
    with col_code2:
        st.success("**[대변]**\n* **4** : 대변 (부채의 증가/수익의 발생)\n* **2** : 입금 (현금 회수 시)")
    
    shortcut_data = {
        "코드": ["1", "2", "3", "4", "5", "6"],
        "구분": ["입금", "출금", "차변", "대변", "결차", "결대"],
        "설명": ["현금 증가", "현금 감소", "자산/비용", "부채/수익", "결산차변", "결산대변"]
    }
    st.table(pd.DataFrame(shortcut_data))

# Menu 1: 마감작업
elif curr == st.session_state.config["menu_1"]:
    st.subheader("📝 완성된 안내문 (복사용)")
    p_h = st.session_state.get("m1_pdf", [])
    p_l = st.session_state.get("m1_ledger", [])
    all_up = (p_h if p_h else []) + (p_l if p_l else [])
    if all_up:
        res = extract_data_from_pdf(all_up)
        biz = all_up[0].name.split("_")[0] if "_" in all_up[0].name else all_up[0].name.split(" ")[0]
        msg = st.session_state.config["prompt_template"].format(업체명=biz, 결과=res["결과"], 매출액=res["매출액"], 매입액=res["매입액"], 세액=res["세액"])
        st.code(msg, language="text")
    else: st.warning("파일을 업로드하면 안내문이 자동 생성됩니다.")
    st.divider()
    col1, col2 = st.columns(2)
    with col1: st.file_uploader("📄 국세청 PDF", type=['pdf'], accept_multiple_files=True, key="m1_pdf")
    with col2: st.file_uploader("📊 매출매입장 PDF", type=['pdf'], accept_multiple_files=True, key="m1_ledger")

# Menu 2: PDF 변환
elif curr == st.session_state.config["menu_2"]:
    f_pdf = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'], key="m2_up")
    if f_pdf:
        df_all = pd.read_excel(f_pdf); biz_name = f_pdf.name.split(" ")[0]
        try:
            tmp_d = pd.to_datetime(df_all['전표일자'], errors='coerce').dropna()
            d_range = f"{tmp_d.min().strftime('%Y-%m-%d')} ~ {tmp_d.max().strftime('%Y-%m-%d')}"
        except: d_range = "2025년"
        type_col = next((c for c in ['구분', '유형'] if c in df_all.columns), None)
        if type_col:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                for g in ['매출', '매입']:
                    tgt = df_all[df_all[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not tgt.empty:
                        pdf = make_pdf_stream(tgt, f"{g} 장", biz_name, d_range)
                        zf.writestr(f"{biz_name}_{g}장.pdf", pdf.getvalue())
            st.download_button("🎁 ZIP 다운로드", data=zip_buf.getvalue(), file_name=f"{biz_name}_매출매입장.zip", use_container_width=True)

# Menu 3: 카드 분리
elif curr == st.session_state.config["menu_3"]:
    card_up = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="m3_up")
    if card_up:
        raw_fn = os.path.splitext(card_up.name)[0]
        clean_name = re.sub(r'\(.*?\)', '', raw_fn.replace("위하고_수기입력_", "")).strip()
        temp_df = pd.read_excel(card_up, header=None)
        target_row = next((i for i, r in temp_df.iterrows() if any(k in " ".join(r.astype(str)) for k in ['카드번호', '매출금액'])), 0)
        df = pd.read_excel(card_up, header=target_row)
        
        df = df.drop(columns=[c for c in df.columns if 'Unnamed' in str(c) or c in ['취소여부', '매출구분']])
        
        dt_col = next((c for c in df.columns if '이용일' in str(c)), None)
        if dt_col:
            df[dt_col] = pd.to_datetime(df[dt_col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        num_col = next((c for c in df.columns if '카드번호' in str(c)), None)
        amt_col = next((c for c in df.columns if any(k in str(c) for k in ['매출금액', '금액', '합계'])), None)
        
        if num_col and amt_col:
            z_buf = io.BytesIO()
            with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                for c_num, group in df.groupby(num_col):
                    if pd.isna(c_num): continue
                    up_df = group.copy()
                    total_amt = pd.to_numeric(up_df[amt_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    up_df['공급가액'] = (total_amt / 1.1).round(0).astype(int)
                    up_df['부가세'] = total_amt.astype(int) - up_df['공급가액']
                    
                    excel_buf = io.BytesIO()
                    with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                        up_df.to_excel(writer, index=False)
                    zf.writestr(f"{clean_name}_{str(c_num)[-4:]}.xlsx", excel_buf.getvalue())
            st.download_button("📥 카드분리 다운로드", data=z_buf.getvalue(), file_name=f"{clean_name}_카드분리.zip", use_container_width=True)
