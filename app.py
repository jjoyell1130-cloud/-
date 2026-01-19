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

# --- [1. PDF 및 엑셀 가공 헬퍼 함수] ---
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

def get_processed_excel(file):
    df = pd.read_excel(file)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- [2. 세션 상태 초기화 (모든 메뉴 데이터 포함)] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환",
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        "sub_menu2": "매출매입장 엑셀을 한 번의 클릭으로 깔끔한 PDF 압축파일로 변환합니다.",
        "sub_menu3": "카드사별 엑셀 파일을 업로드하시면 위하고 양식 변환 및 카드별 자동 분리가 수행됩니다.",
        "prompt_template": "*{업체명} 부가세 신고현황☆★{결과}\n감기 조심하시고 건강이 최고인거 아시죠? ^.<\n\n부가세 신고 마무리되어 전체 자료 전달드립니다."
    }

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}]

if 'link_group_2' not in st.session_state:
    st.session_state.link_group_2 = [{"name": "📊 신고리스트", "url": "#"}, {"name": "💳 카드매입자료", "url": "#"}]

# --- [3. 디자인 설정] ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# 사이드바
with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, 
                     type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [4. 메인 화면 구성] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()

# --- [메뉴 0: Home] ---
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    st.divider()
    st.subheader("⌨️ 차변계정 단축키")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True)
    if st.button("💾 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("저장되었습니다.")

# --- [메뉴 1: 마감작업] ---
elif current_menu == st.session_state.config["menu_1"]:
    st.info(st.session_state.config["sub_menu1"])
    excel_up = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'], key="m1_up")
    if excel_up:
        st.download_button("📥 가공 다운로드", data=get_processed_excel(excel_up), file_name=f"가공_{excel_up.name}")

# --- [메뉴 2: PDF 변환] ---
elif current_menu == st.session_state.config["menu_2"]:
    st.info(st.session_state.config["sub_menu2"])
    f = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'], key="m2_up")
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        # (PDF 변환 로직 실행 및 다운로드 버튼 표시)
        st.write(f"{biz_name} 데이터 분석 완료")

# --- [메뉴 3: 카드매입 수기입력 (핵심 수정)] ---
elif current_menu == st.session_state.config["menu_3"]:
    st.info(st.session_state.config["sub_menu3"])
    card_up = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], key="m3_up")
    
    if card_up:
        # 1. 원본을 먼저 읽어서 헤더 위치 검색
        raw_data = pd.read_excel(card_up, header=None)
        header_index = 0
        for i, row in raw_data.iterrows():
            # 행의 값 중 '카드'나 '번호'가 들어있는 행을 찾으면 거기를 제목줄로 인식
            if any(kw in str(val) for kw in ['카드사', '카드번호', '카드명', '승인번호'] for val in row):
                header_index = i
                break
        
        # 2. 찾은 헤더 인덱스로 데이터 다시 로드
        df = pd.read_excel(card_up, header=header_index)
        base_filename = os.path.splitext(card_up.name)[0]
        
        # 3. 유연한 컬럼 매칭
        card_co_col = next((c for c in df.columns if any(kw in str(c) for kw in ['카드사', '카드기관', '카드명', '발급사'])), None)
        card_num_col = next((c for c in df.columns if any(kw in str(c) for kw in ['카드번호', '번호', '계좌', '카드번호별'])), None)
        amt_col = next((c for c in df.columns if any(kw in str(c) for kw in ['이용금액', '합계금액', '금액', '승인금액', '합계'])), None)
        
        if card_co_col and card_num_col:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                grouped = df.groupby([card_co_col, card_num_col])
                for (card_co, card_num), group in grouped:
                    if pd.isna(card_co) or pd.isna(card_num): continue
                    
                    upload_df = group.copy()
                    if amt_col:
                        upload_df[amt_col] = pd.to_numeric(upload_df[amt_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                        upload_df['공급가액'] = (upload_df[amt_col] / 1.1).round(0).astype(int)
                        upload_df['부가세'] = upload_df[amt_col] - upload_df['공급가액']
                    
                    safe_co = str(card_co).strip()
                    safe_num = str(card_num).replace('*', '').strip()
                    new_file_name = f"{base_filename}_{safe_co}_{safe_num}_(업로드용).xlsx"
                    
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        upload_df.to_excel(writer, index=False)
                    zf.writestr(new_file_name, excel_buffer.getvalue())
            
            st.success(f"✅ {len(grouped)}개의 카드 파일을 생성했습니다.")
            st.download_button(
                label="📥 카드별 분리 파일 일괄 다운로드 (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"{base_filename}_카드분리완료.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.error(f"❌ 제목줄(헤더)을 찾지 못했습니다.")
            st.write("인식된 컬럼명:", list(df.columns))
