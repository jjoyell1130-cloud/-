import streamlit as st
import pdfplumber
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import io
import urllib.request

# 1. 폰트 설정 (가장 안전한 방식: 없으면 서버에서 나눔고딕 다운로드)
def load_font():
    font_path = "nanum.ttf"
    # 폰트 파일이 없으면 공신력 있는 주소에서 직접 다운로드
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except:
            return False
            
    try:
        pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        return True
    except:
        return False

# 폰트 상태 확인
font_status = load_font()
f_name = 'NanumGothic' if font_status else 'Helvetica'

# 2. PDF 생성 보조 함수
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

def make_pdf_buffer(data, title, date_range, company_name):
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
            c.setFont(f_name, 20)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont(f_name, 10)
            c.drawString(50, height - 90, f"회사명 : {company_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            
            yh = 680 
            c.setLineWidth(1.5); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(f_name, 9)
            c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자"); c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        def check_summary(r):
            if r is None: return False
            t_no, t_vendor = str(r.get('번호', '')), str(r.get('거래처', ''))
            txt = (t_no + t_vendor).replace(" ", "").replace("[", "").replace("]", "")
            return any(k in txt for k in summary_keywords)

        is_curr_summary = check_summary(row)
        next_row = data.iloc[i+1] if i+1 < len(data) else None
        
        if is_curr_summary:
            c.setFont(f_name, 9)
            c.drawString(90, cur_y, str(row['거래처']) if pd.notna(row['거래처']) else str(row['번호']))
        else:
            actual_item_count += 1
            c.setFont(f_name, 8.5)
            c.drawString(45, cur_y, str(actual_item_count))
            c.drawString(85, cur_y, str(row['전표일자']) if pd.notna(row['전표일자']) else "")
            c.drawString(170, cur_y, str(row['거래처'])[:25] if pd.notna(row['거래처']) else "")
        
        c.drawRightString(410, cur_y, f"{to_int(row['공급가액']):,}")
        c.drawRightString(485, cur_y, f"{to_int(row['부가세']):,}")
        c.drawRightString(550, cur_y, f"{to_int(row['합계']):,}")

    c.save()
    buffer.seek(0)
    return buffer

# 3. Streamlit UI
st.set_page_config(page_title="세무비서 자동화", layout="centered")

# 사이드바 설정
st.sidebar.title("📑 매출매입장 PDF 생성")
uploaded_excels = st.sidebar.file_uploader("엑셀 파일들을 선택하세요", type=['xlsx'], accept_multiple_files=True)

if uploaded_excels:
    for uploaded_excel in uploaded_excels:
        try:
            name_only = uploaded_excel.name.split('.')[0]
            df_excel = pd.read_excel(uploaded_excel)
            date_series = df_excel['전표일자'].dropna().astype(str)
            date_range = f"{date_series.min()} ~ {date_series.max()}" if not date_series.empty else "기간 없음"
            clean_df = df_excel[df_excel['구분'].isin(['매입', '매출'])].copy()
            
            st.sidebar.write(f"---")
            st.sidebar.markdown(f"**📂 {name_only}**")
            for g in ['매출', '매입']:
                target = clean_df[clean_df['구분'] == g].reset_index(drop=True)
                if not target.empty:
                    pdf_out = make_pdf_buffer(target, f"{g[0]} {g[1]} 장", date_range, name_only)
                    st.sidebar.download_button(
                        label=f"📥 {g}장 다운로드",
                        data=pdf_out,
                        file_name=f"{name_only}_{g}장.pdf",
                        mime="application/pdf",
                        key=f"btn_{name_only}_{g}"
                    )
        except Exception as e:
            st.sidebar.error(f"오류: {e}")

# 메인 화면
st.title("📊 부가세 신고 안내문 생성기")
if not font_status:
    st.error("❗ 한글 폰트를 로드할 수 없습니다. 한글이 깨질 수 있으니 malgun.ttf 파일을 확인해주세요.")

uploaded_pdfs = st.file_uploader("위하고 PDF 파일들을 선택하세요", accept_multiple_files=True, type=['pdf'])

if uploaded_pdfs:
    first_file = uploaded_pdfs[0].name
    biz_name = first_file.split('_')[0] if '_' in first_file else "알 수 없음"
    report_data = {"매출": "0", "매입": "0", "환급": "0"}

    for file in uploaded_pdfs:
        with pdfplumber.open(file) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            if "매출장" in file.name:
                for line in text.split('\n'):
                    if "누계" in line:
                        nums = "".join([c for c in line if c.isdigit() or c == ',']).split(',')
                        if len(nums) >= 2: report_data["매출"] = f"{nums[-2]},{nums[-1]}"
            elif "매입장" in file.name:
                for line in text.split('\n'):
                    if "누계매입" in line:
                        nums = "".join([c for c in line if c.isdigit() or c == ',']).split(',')
                        if len(nums) >= 2: report_data["매입"] = f"{nums[-2]},{nums[-1]}"
            elif "접수증" in file.name or "신고서" in file.name:
                for line in text.split('\n'):
                    if "차가감납부할세액" in line:
                        report_data["환급"] = "".join([c for c in line if c.isdigit() or c == ','])

    final_text = f"""=첨부파일=
-부가세 신고서
-매출장: {report_data['매출']}원
-매입장: {report_data['매입']}원
-접수증 > 환급: {report_data['환급']}원
☆★환급예정 8월 말 정도"""
    st.success(f"✅ {biz_name} 분석 완료!")
    st.text_area("안내문 복사", final_text, height=200)
else:
    st.info("왼쪽 사이드바에서 엑셀을 변환하거나 PDF를 올려 안내문을 만드세요.")
