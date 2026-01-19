import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. PDF 변환 엔진] ---
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
            c.setFont(FONT_NAME, 18)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont(FONT_NAME, 10)
            c.drawString(50, height - 90, f"회사명 : {biz_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            
            yh = 680 
            c.setLineWidth(1.2); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(FONT_NAME, 9)
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자")
            c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세")
            c.drawRightString(550, yh, "합계")
            c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        txt = (str(row.get('번호', '')) + str(row.get('거래처', ''))).replace(" ", "")
        is_summary = any(k in txt for k in summary_keywords)

        c.setFont(FONT_NAME, 8.5)
        if is_summary:
            c.setFont(FONT_NAME, 9)
            c.drawString(90, cur_y, str(row.get('거래처', row.get('번호', ''))))
            c.line(40, cur_y + 16, 555, cur_y + 16)
            c.line(40, cur_y - 7, 555, cur_y - 7)
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

    c.save()
    buffer.seek(0)
    return buffer

# --- [2. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환",
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF와 변환된 매출매입장 PDF를 업로드하여 마감 작업을 진행합니다.",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}
감기 조심하시고 건강이 최고인거 아시죠? ^.<

부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {매출액}원
-매입장: {매입액}원
-접수증 > {결과}: {세액}원

☆★{결과}예정 8월 말 정도

혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!
25일 까지는 수정이 가능합니다!"""
    }

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

# --- [3. 레이아웃] ---
st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, 
                     type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [4. 메인 로직] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()

# --- Menu 1: 마감작업 (PDF 업로드 중심) ---
if current_menu == st.session_state.config["menu_1"]:
    st.info(st.session_state.config["sub_menu1"])
    
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=200)
        if st.button("💾 안내문 양식 저장"):
            st.session_state.config["prompt_template"] = u_template
            st.success("양식이 저장되었습니다.")
            
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 국세청 PDF 업로드")
        pdf_hometax = st.file_uploader("국세청 자료 (PDF)", type=['pdf'], accept_multiple_files=True, key="m1_hometax")
        if pdf_hometax:
            st.success(f"{len(pdf_hometax)}개의 파일 업로드됨")

    with col2:
        st.subheader("📊 매출매입장 PDF 업로드")
        pdf_ledger = st.file_uploader("변환된 매출매입장 (PDF)", type=['pdf'], accept_multiple_files=True, key="m1_ledger")
        if pdf_ledger:
            st.success(f"{len(pdf_ledger)}개의 파일 업로드됨")
            # 업로드된 파일들을 리스트로 보여주거나 다운로드 확인
            for f in pdf_ledger:
                st.caption(f"✅ {f.name} 준비 완료")

# --- Menu 2: PDF 일괄 변환 (이전 로직 유지) ---
elif current_menu == st.session_state.config["menu_2"]:
    f_pdf = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'], key="m2_up")
    if f_pdf:
        df_all = pd.read_excel(f_pdf)
        biz_name = f_pdf.name.split(" ")[0]
        type_col = next((c for c in ['구분', '유형'] if c in df_all.columns), None)
        if type_col:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                for g in ['매출', '매입']:
                    target = df_all[df_all[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not target.empty:
                        pdf = make_pdf_stream(target, f"{g} 장", biz_name, "2025년")
                        zf.writestr(f"{biz_name}_{g}장.pdf", pdf.getvalue())
            st.download_button(label="🎁 매출/매입장 PDF 일괄 다운로드 (ZIP)", data=zip_buffer.getvalue(),
                               file_name=f"{biz_name}_매출매입장_일괄.zip", mime="application/zip", use_container_width=True)

# --- Menu 3: 카드 분리 (이전 로직 유지) ---
elif current_menu == st.session_state.config["menu_3"]:
    card_up = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="m3_up")
    if card_up:
        raw_fn = os.path.splitext(card_up.name)[0]
        clean_name = re.sub(r'\(.*?\)', '', raw_fn.replace("위하고_수기입력_", "")).strip()
        temp_df = pd.read_excel(card_up, header=None)
        target_row = next((i for i, r in temp_df.iterrows() if any(k in " ".join(r.astype(str)) for k in ['카드번호', '매출금액'])), 0)
        df = pd.read_excel(card_up, header=target_row)
        df = df.drop(columns=[c for c in df.columns if 'Unnamed' in str(c) or c in ['취소여부', '매출구분']])
        dt_col = next((c for c in df.columns if '이용일' in str(c)), None)
        if dt_col: df[dt_col] = pd.to_datetime(df[dt_col], errors='coerce').dt.strftime('%Y-%m-%d')
        num_col = next((c for c in df.columns if '카드번호' in str(c)), None)
        if num_col:
            z_buf = io.BytesIO()
            with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                for c_num, group in df.groupby(num_col):
                    if pd.isna(c_num): continue
                    excel_buf = io.BytesIO()
                    with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                        group.to_excel(writer, index=False)
                    zf.writestr(f"{clean_name}_{str(c_num)[-4:]}.xlsx", excel_buf.getvalue())
            st.download_button("📥 카드분리 다운로드 (ZIP)", data=z_buf.getvalue(), file_name=f"{clean_name}_카드분리.zip")
