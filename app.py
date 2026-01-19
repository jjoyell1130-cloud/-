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

# --- [1. PDF 생성 엔진 로직] ---
try:
    # 맑은고딕 폰트가 경로에 있어야 한글이 깨지지 않습니다.
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
            c.setFont(FONT_NAME, 20)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont(FONT_NAME, 10)
            c.drawString(50, height - 90, f"회사명 : {biz_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            
            yh = 680 
            c.setLineWidth(1.5); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(FONT_NAME, 9)
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자")
            c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세")
            c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        # 합계 행인지 확인
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
        "sub_menu1": "국세청 PDF 및 엑셀 가공 후 안내문을 작성합니다.",
        "sub_menu2": "매출매입장을 깔끔한 PDF 압축파일로 변환합니다.",
        "sub_menu3": "불필요 열 삭제 및 날짜 간소화 후 카드별로 파일을 분리합니다."
    }
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

# --- [3. 사이드바 및 레이아웃] ---
st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        btn_type = "primary" if st.session_state.selected_menu == m_name else "secondary"
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, type=btn_type):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [4. 메인 화면 로직] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()

# --- [Menu 0, 1은 생략 (이전과 동일)] ---
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)

# --- [Menu 2: PDF 변환 엔진 복구] ---
elif current_menu == st.session_state.config["menu_2"]:
    st.info(st.session_state.config["sub_menu2"])
    f_pdf = st.file_uploader("📊 엑셀 파일 업로드 (PDF 변환용)", type=['xlsx'], key="m2_pdf_up")
    
    if f_pdf:
        # 엑셀 파일의 모든 시트를 읽음
        all_sheets = pd.read_excel(f_pdf, sheet_name=None)
        biz_name = f_pdf.name.split(" ")[0]
        
        st.success(f"✅ {len(all_sheets)}개의 시트를 분석했습니다. PDF 생성을 시작합니다.")
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
            for sheet_name, df in all_sheets.items():
                if df.empty: continue
                
                # PDF 스트림 생성
                pdf_data = make_pdf_stream(df, sheet_name, biz_name, "2025년도")
                zf.writestr(f"{sheet_name}.pdf", pdf_data.getvalue())
        
        st.download_button(
            label="📥 PDF 변환 완료 (ZIP 다운로드)",
            data=zip_buffer.getvalue(),
            file_name=f"{biz_name}_매출매입장_PDF.zip",
            mime="application/zip",
            use_container_width=True
        )

# --- [Menu 3: 카드 분리 (유지)] ---
elif current_menu == st.session_state.config["menu_3"]:
    st.info(st.session_state.config["sub_menu3"])
    card_up = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], key="m3_card_up")
    if card_up:
        # (이전에 완성한 파일명 정리 및 컬럼 삭제 로직 실행)
        raw_fn = os.path.splitext(card_up.name)[0]
        clean_name = re.sub(r'\(.*?\)', '', raw_fn.replace("위하고_수기입력_", "")).strip()
        
        temp_df = pd.read_excel(card_up, header=None)
        target_row = next((i for i, r in temp_df.iterrows() if any(k in " ".join(r.astype(str)) for k in ['카드번호', '매출금액'])), 0)
        df = pd.read_excel(card_up, header=target_row)
        
        # 열 삭제
        df = df.drop(columns=[c for c in df.columns if 'Unnamed' in str(c) or c in ['취소여부', '매출구분']])
        # 날짜 간소화
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
                    zf.writestr(f"{clean_name}_{c_co}_{str(c_num)[-4:]}_(업로드용).xlsx", get_processed_excel(up_df))
            
            st.download_button("📥 가공 및 분리 완료(ZIP)", data=z_buf.getvalue(), file_name=f"{clean_name}_가공완료.zip")

def get_processed_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()
