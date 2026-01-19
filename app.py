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

# --- [1. PDF 변환 핵심 엔진] ---
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
        "sub_menu1": "안내문 자동 작성 및 엑셀 가공 도구입니다.",
        "sub_menu2": "매출매입장을 각각의 PDF로 일괄 변환하여 ZIP으로 제공합니다.",
        "sub_menu3": "불필요 열 삭제 및 날짜 간소화 후 카드번호별로 파일을 분리합니다."
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

# --- Menu 0: Home ---
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)

# --- Menu 2: PDF 일괄 변환 (매출/매입 구분 ZIP) ---
elif current_menu == st.session_state.config["menu_2"]:
    st.info(st.session_state.config["sub_menu2"])
    f_pdf = st.file_uploader("📊 엑셀 파일 업로드 (PDF 변환용)", type=['xlsx'], key="m2_up")
    if f_pdf:
        df_all = pd.read_excel(f_pdf)
        biz_name = f_pdf.name.split(" ")[0]
        
        # 일자 범위 자동 추출
        try:
            tmp_d = pd.to_datetime(df_all['전표일자'], errors='coerce').dropna()
            d_range = f"{tmp_d.min().strftime('%Y-%m-%d')} ~ {tmp_d.max().strftime('%Y-%m-%d')}"
        except: d_range = "2025년도"

        type_col = next((c for c in ['구분', '유형'] if c in df_all.columns), None)
        if type_col:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                for g in ['매출', '매입']:
                    target = df_all[df_all[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not target.empty:
                        pdf = make_pdf_stream(target, f"{g} 장", biz_name, d_range)
                        zf.writestr(f"{biz_name}_{g}장.pdf", pdf.getvalue())
            
            st.success(f"✅ {biz_name} 분석 완료. 매출/매입장이 포함된 ZIP을 생성했습니다.")
            st.download_button(
                label="🎁 매출/매입장 PDF 일괄 다운로드 (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"{biz_name}_매출매입장_일괄.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.error("'구분' 또는 '유형' 컬럼을 엑셀에서 찾을 수 없습니다.")

# --- Menu 3: 카드 분리 (불필요 열 삭제 + 날짜 간소화 + 카드번호별 파일명 정리) ---
elif current_menu == st.session_state.config["menu_3"]:
    st.info(st.session_state.config["sub_menu3"])
    card_up = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'], key="m3_up")
    if card_up:
        # 1. 파일명 정리
        raw_fn = os.path.splitext(card_up.name)[0]
        clean_name = re.sub(r'\(.*?\)', '', raw_fn.replace("위하고_수기입력_", "")).strip()
        
        # 2. 헤더 찾기
        temp_df = pd.read_excel(card_up, header=None)
        target_row = next((i for i, r in temp_df.iterrows() if any(k in " ".join(r.astype(str)) for k in ['카드번호', '매출금액'])), 0)
        df = pd.read_excel(card_up, header=target_row)
        
        # 3. 열 삭제 및 가공
        df = df.drop(columns=[c for c in df.columns if 'Unnamed' in str(c) or c in ['취소여부', '매출구분']])
        dt_col = next((c for c in df.columns if '이용일' in str(c)), None)
        if dt_col: df[dt_col] = pd.to_datetime(df[dt_col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        num_col = next((c for c in df.columns if '카드번호' in str(c)), None)
        amt_col = next((c for c in df.columns if any(k in str(c) for k in ['매출금액', '금액', '합계'])), None)
        co_col = next((c for c in df.columns if any(k in str(c) for k in ['카드사', '기관', '카드명'])), None)
        
        if num_col and amt_col:
            z_buf = io.BytesIO()
            with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                for c_num, group in df.groupby(num_col):
                    if pd.isna(c_num): continue
                    up_df = group.copy()
                    up_df[amt_col] = pd.to_numeric(up_df[amt_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    up_df['공급가액'] = (up_df[amt_col] / 1.1).round(0).astype(int)
                    up_df['부가세'] = up_df[amt_col] - up_df['공급가액']
                    
                    c_co = str(group[co_col].iloc[0]) if co_col else "카드"
                    safe_num = str(c_num).replace('*', '').strip()
                    
                    # 엑셀 파일 생성
                    excel_buf = io.BytesIO()
                    with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                        up_df.to_excel(writer, index=False)
                    zf.writestr(f"{clean_name}_{c_co}_{safe_num}_(업로드용).xlsx", excel_buf.getvalue())
            
            st.download_button("📥 카드별 분리 파일 일괄 다운로드 (ZIP)", data=z_buf.getvalue(), file_name=f"{clean_name}_카드분리완료.zip", use_container_width=True)
