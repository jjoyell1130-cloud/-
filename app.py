import streamlit as st
import pandas as pd
import io
import os
import zipfile
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- [1. PDF 변환 핵심 로직 (성공 양식)] ---
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
        
        def check_summary(r):
            txt = (str(r.get('번호', '')) + str(r.get('거래처', ''))).replace(" ", "")
            return any(k in txt for k in summary_keywords)

        is_curr_summary = check_summary(row)
        c.setFont(FONT_NAME, 8.5)
        
        if is_curr_summary:
            c.setFont(FONT_NAME, 9)
            c.drawString(90, cur_y, str(row.get('거래처', row.get('번호', ''))))
            c.setLineWidth(1.2); c.line(40, cur_y + 16, 555, cur_y + 16)
            c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.drawString(45, cur_y, str(actual_item_count))
            raw_date = row.get('전표일자', '')
            c.drawString(85, cur_y, str(raw_date)[:10] if pd.notna(raw_date) else "")
            c.drawString(170, cur_y, str(row.get('거래처', ''))[:25])
            c.setLineWidth(0.3); c.setStrokeColor(colors.lightgrey)
            c.line(40, cur_y - 7, 555, cur_y - 7)
        
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
        c.setStrokeColor(colors.black)

    c.save()
    buffer.seek(0)
    return buffer

# --- [2. 세션 상태 및 설정] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환",
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "매출매입장 엑셀을 한 번의 클릭으로 깔끔한 PDF 압축파일로 변환합니다.",
        "sub_menu3": "카드사별 엑셀 파일을 업로드하시면 위하고 양식으로 즉시 변환됩니다.",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}
감기 조심하시고 건강이 최고인거 아시죠? ^.<

부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {매출액}원
-매입장: {매입액}원
-접수증 > {결과}: {세액}원"""
    }

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

if 'daily_memo' not in st.session_state:
    st.session_state.daily_memo = ""

if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}]

# --- [3. 가공용 헬퍼 & 스타일] ---
def get_processed_excel(file):
    df = pd.read_excel(file)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.set_page_config(page_title="세무 통합 시스템", layout="wide")
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; max-width: 95%; margin-left: 0 !important; text-align: left !important; }
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%; border-radius: 6px; height: 2.2rem; font-size: 14px; text-align: left !important;
        padding-left: 15px !important; margin-bottom: -10px; border: 1px solid #ddd; background-color: white; color: #444;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #f0f2f6 !important; color: #1f2937 !important; border: 2px solid #9ca3af !important; font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바 메뉴 (4개)] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    m_list = [st.session_state.config[f"menu_{i}"] for i in range(4)]
    for m_name in m_list:
        if st.button(m_name, key=f"btn_{m_name}", use_container_width=True, type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

    for _ in range(12): st.write("") 
    st.divider()
    st.markdown("#### 📝 Memo")
    memo_val = st.text_area("Memo", value=st.session_state.daily_memo, height=200, label_visibility="collapsed")
    if st.button("💾 저장", use_container_width=True):
        st.session_state.daily_memo = memo_val
        st.success("저장되었습니다.")

# --- [5. 메인 화면] ---
curr = st.session_state.selected_menu
st.title(curr)

if curr == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    st.divider()
    st.subheader("⌨️ 차변계정 단축키")
    edited_df = st.data_editor(pd.DataFrame(st.session_state.account_data), num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장되었습니다.")

elif curr == st.session_state.config["menu_1"]:
    st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu1']}</p>", unsafe_allow_html=True)
    # 기존 마감작업 로직 (안내문 등) 수록 가능

elif curr == st.session_state.config["menu_2"]:
    st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu2']}</p>", unsafe_allow_html=True)
    f = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'], key="pdf_conv_up")
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        try:
            tmp_d = pd.to_datetime(df['전표일자'], errors='coerce').dropna()
            d_range = f"{tmp_d.min().strftime('%Y-%m-%d')} ~ {tmp_d.max().strftime('%Y-%m-%d')}" if not tmp_d.empty else "기간없음"
        except: d_range = "기간 정보 확인 필요"
        
        type_col = next((c for c in ['구분', '유형'] if c in df.columns), None)
        if type_col:
            st.success(f"분석 완료: {biz_name} ({d_range})")
            
            # ZIP 생성
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                for g in ['매출', '매입']:
                    target = df[df[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not target.empty:
                        pdf = make_pdf_stream(target, f"{g} 장", biz_name, d_range)
                        zf.writestr(f"{biz_name}_{g}장.pdf", pdf.getvalue())
            
            st.download_button("🎁 매출/매입장 PDF 일괄 다운로드 (ZIP)", zip_buf.getvalue(), file_name=f"{biz_name}_매출매입장.zip", mime="application/zip", use_container_width=True)

elif curr == st.session_state.config["menu_3"]:
    st.markdown(f"<p style='color: #666;'>{st.session_state.config['sub_menu3']}</p>", unsafe_allow_html=True)
    card_f = st.file_uploader("💳 카드사 엑셀 업로드", type=['xlsx'])
    if card_f:
        st.download_button("📥 위하고 양식 다운로드", get_processed_excel(card_f), file_name=f"위하고_{card_f.name}", use_container_width=True)
