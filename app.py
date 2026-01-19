import streamlit as st
import pdfplumber
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# --- 폰트 설정 (GitHub에 올린 malgun.ttf 파일을 읽도록 수정) ---
@st.cache_resource
def load_font():
    font_path = "malgun.ttf"  # GitHub에 업로드할 파일명과 일치해야 함
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
        return True
    return False

font_status = load_font()

# --- PDF 생성 보조 함수 ---
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        return int(float(str(val).replace(',', '')))
    except: return 0

def make_pdf(data, title, filename, date_range):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    rows_per_page = 26
    actual_item_count = 0 
    summary_keywords = ['합계', '월계', '분기', '반기', '누계']

    for i in range(len(data)):
        if i % rows_per_page == 0:
            if i > 0: c.showPage()
            p_num = (i // rows_per_page) + 1
            c.setFont('MalgunGothic', 20)
            c.drawCentredString(width/2, height - 60, title)
            c.setFont('MalgunGothic', 10)
            c.drawString(50, height - 90, "회사명 : 에덴인테리어")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            c.drawRightString(width - 50, height - 90, f"페이지 : {p_num}")
            
            yh = 680 
            c.setLineWidth(1.5)
            c.line(40, yh + 15, 555, yh + 15)
            c.setFont('MalgunGothic', 9)
            c.drawString(45, yh, "번호")
            c.drawString(90, yh, "일자")
            c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액")
            c.drawRightString(485, yh, "부가가치세")
            c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0)
            c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        
        row = data.iloc[i]
        cur_y = y_start - ((i % rows_per_page) * 23)
        
        def check_summary(r):
            if r is None: return False
            t_no = str(r.get('번호', ''))
            t_vendor = str(r.get('거래처', ''))
            txt = (t_no + t_vendor).replace(" ", "").replace("[", "").replace("]", "")
            return any(k in txt for k in summary_keywords)

        is_curr_summary = check_summary(row)
        next_row = data.iloc[i+1] if i+1 < len(data) else None
        
        if is_curr_summary:
            c.setFont('MalgunGothic', 9)
            c.drawString(90, cur_y, str(row['거래처']) if pd.notna(row['거래처']) else str(row['번호']))
            prev_row = data.iloc[i-1] if i > 0 else None
            if not check_summary(prev_row):
                c.setLineWidth(1.2); c.line(40, cur_y + 16, 555, cur_y + 16)
            if not check_summary(next_row):
                c.setLineWidth(1.2); c.line(40, cur_y - 7, 555, cur_y - 7)
        else:
            actual_item_count += 1
            c.setFont('MalgunGothic', 8.5)
            c.drawString(45, cur_y, str(actual_item_count))
            c.drawString(85, cur_y, str(row['전표일자']) if pd.notna(row['전표일자']) else "")
            c.drawString(170, cur_y, str(row['거래처'])[:25] if pd.notna(row['거래처']) else "")
            c.setLineWidth(0.3); c.setStrokeColor(colors.lightgrey)
            c.line(40, cur_y - 7, 555, cur_y - 7)
            c.setStrokeColor(colors.black)
        
        c.drawRightString(410, cur_y, f"{to_int(row['공급가액']):,}")
        c.drawRightString(485, cur_y, f"{to_int(row['부가세']):,}")
        c.drawRightString(550, cur_y, f"{to_int(row['합계']):,}")

    c.save()

# --- Streamlit UI ---
st.set_page_config(page_title="세무비서 자동화", layout="centered")

# 사이드바 기능
st.sidebar.title("📁 추가 기능")
if st.sidebar.button("📊 매출, 매입장 생성하기"):
    if not font_status:
        st.sidebar.error("❌ malgun.ttf 폰트 파일이 없습니다. GitHub에 업로드해주세요.")
    else:
        try:
            excel_path = "에덴인테리어 매입매출장.xlsx"
            if os.path.exists(excel_path):
                df_excel = pd.read_excel(excel_path)
                date_series = df_excel['전표일자'].dropna().astype(str)
                date_range = f"{date_series.min()} ~ {date_series.max()}" if not date_series.empty else "기간 없음"
                
                clean_df = df_excel[df_excel['구분'].isin(['매입', '매출'])].copy()
                for g in ['매출', '매입']:
                    target = clean_df[clean_df['구분'] == g].reset_index(drop=True)
                    if not target.empty:
                        make_pdf(target, f"{g[0]} {g[1]} 장", f"에덴인테리어_{g}장.pdf", date_range)
                st.sidebar.success("✅ PDF 생성 완료! (서버 폴더 확인)")
            else:
                st.sidebar.error("❌ '에덴인테리어 매입매출장.xlsx' 파일을 찾을 수 없습니다.")
        except Exception as e:
            st.sidebar.error(f"❌ 오류 발생: {e}")

# 메인 기능
st.title("📊 부가세 신고 안내문 생성기")
st.write("위하고에서 받은 PDF 파일들을 아래에 올려주세요.")

uploaded_files = st.file_uploader("PDF 파일을 모두 선택하세요", accept_multiple_files=True, type=['pdf'])

if uploaded_files:
    first_file_name = uploaded_files[0].name
    biz_name = first_file_name.split('_')[0] if '_' in first_file_name else "알 수 없음"
    report_data = {"매출": "0", "매입": "0", "환급": "0"}

    for file in uploaded_files:
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

    st.success(f"✅ {biz_name} 업체 분석 완료!")
    st.subheader("📋 생성된 안내문")
    st.text_area("내용을 복사해서 카톡에 붙여넣으세요", final_text, height=200)
else:
    st.info("위하고에서 다운로드한 매출장, 매입장, 접수증 PDF를 올려주세요.")
