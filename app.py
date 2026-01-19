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
import zipfile

# 1. 폰트 설정
def load_font():
    font_path = "nanum.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except: return False
    try:
        pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        return True
    except: return False

font_status = load_font()
f_name = 'NanumGothic' if font_status else 'Helvetica'

# 2. 금액 변환 함수
def to_int(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0
        # 소수점이나 콤마 제거 후 정수 변환
        clean_val = str(val).replace(',', '').split('.')[0]
        return int(clean_val)
    except: return 0

# 3. 날짜 추출 함수
def get_clean_date_range(df):
    date_col = next((c for c in df.columns if '일자' in c), None)
    if date_col:
        dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
        if not dates.empty:
            return f"{dates.min().strftime('%Y-%m-%d')} ~ {dates.max().strftime('%Y-%m-%d')}"
    return "기간 정보 없음"

# 4. PDF 생성 함수 (생략 없이 유지)
def make_pdf_buffer(data, title, date_range, company_name):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    rows_per_page = 26
    actual_item_count = 0 
    for i in range(len(data)):
        if i % rows_per_page == 0:
            if i > 0: c.showPage()
            c.setFont(f_name, 20); c.drawCentredString(width/2, height - 60, title)
            c.setFont(f_name, 10); c.drawString(50, height - 90, f"회사명 : {company_name}")
            c.drawString(50, height - 105, f"기  간 : {date_range}") 
            yh = 680; c.setLineWidth(1.5); c.line(40, yh + 15, 555, yh + 15)
            c.setFont(f_name, 9); c.drawString(45, yh, "번호"); c.drawString(90, yh, "일자"); c.drawString(180, yh, "거래처(적요)")
            c.drawRightString(420, yh, "공급가액"); c.drawRightString(485, yh, "부가가치세"); c.drawRightString(550, yh, "합계")
            c.setLineWidth(1.0); c.line(40, yh - 8, 555, yh - 8)
            y_start = yh - 28
        row = data.iloc[i]; cur_y = y_start - ((i % rows_per_page) * 23); actual_item_count += 1
        c.setFont(f_name, 8.5); c.drawString(45, cur_y, str(actual_item_count))
        # '일자'가 포함된 컬럼 찾기
        date_val = row.get('전표일자', row.get('일자', ''))
        c.drawString(85, cur_y, str(date_val)[:10] if pd.notna(date_val) else "")
        # '거래처'가 포함된 컬럼 찾기
        vendor_val = row.get('거래처', row.get('적요', ''))
        c.drawString(170, cur_y, str(vendor_val)[:25] if pd.notna(vendor_val) else "")
        c.drawRightString(410, cur_y, f"{to_int(row.get('공급가액', 0)):,}")
        c.drawRightString(485, cur_y, f"{to_int(row.get('부가세', 0)):,}")
        c.drawRightString(550, cur_y, f"{to_int(row.get('합계', 0)):,}")
    c.save(); buffer.seek(0)
    return buffer

# --- Streamlit UI ---
st.set_page_config(page_title="세무비서 자동화", layout="wide")
st.title("🚀 세무비서 통합 자동화 시스템")

st.sidebar.title("📑 데이터 업로드")
uploaded_excels = st.sidebar.file_uploader("엑셀 파일들을 선택하세요", type=['xlsx'], accept_multiple_files=True)

all_company_reports = []

if uploaded_excels:
    all_pdfs = []
    for uploaded_excel in uploaded_excels:
        try:
            # 엑셀 읽기
            df = pd.read_excel(uploaded_excel)
            # 컬럼명 앞뒤 공백 제거
            df.columns = [c.strip() for c in df.columns]
            
            name_only = uploaded_excel.name.split('.')[0]
            comp_name = name_only.replace(" 매입매출장", "").replace("_매입매출장", "")
            
            # '구분' 컬럼 데이터 정리 (공백 제거)
            if '구분' in df.columns:
                df['구분'] = df['구분'].astype(str).str.strip()
            
            # 합계 계산 로직 (데이터가 있는지 확인용)
            sales_data = df[df['구분'] == '매출']
            buys_data = df[df['구분'] == '매입']
            
            s_sum = to_int(sales_data['합계'].sum())
            b_sum = to_int(buys_data['합계'].sum())
            s_vat = to_int(sales_data['부가세'].sum())
            b_vat = to_int(buys_data['부가세'].sum())
            
            # 리스트에 추가 (매출/매입 데이터가 하나라도 있으면 추가)
            all_company_reports.append({
                "name": comp_name,
                "sales": s_sum,
                "buys": b_sum,
                "vat": s_vat - b_sum # 예상 납부액 (매출세액 - 매입합계) 로직 확인 필요
            })

            # PDF용
            date_range = get_clean_date_range(df)
            for g, target_df in [('매출', sales_data), ('매입', buys_data)]:
                if not target_df.empty:
                    pdf_buf = make_pdf_buffer(target_df.reset_index(), f"{g[0]} {g[1]} 장", date_range, comp_name)
                    all_pdfs.append({"name": f"{comp_name}_{g}장.pdf", "data": pdf_buf})
                    
        except Exception as e:
            st.sidebar.error(f"⚠️ {uploaded_excel.name} 분석 중 오류: {e}")

    # ZIP 다운로드 버튼
    if all_pdfs:
        st.sidebar.markdown("---")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for pdf in all_pdfs: zf.writestr(pdf["name"], pdf["data"].getvalue())
        zip_buffer.seek(0)
        st.sidebar.download_button(label="🎁 모든 PDF ZIP 다운로드", data=zip_buffer, file_name="전체장부.zip", mime="application/zip", use_container_width=True)

# 메인 화면 안내문 출력
st.subheader("✉️ 업체별 발송용 안내문구")
if all_company_reports:
    # 데이터가 잘 들어왔는지 디버깅용 (성공하면 삭제 가능)
    # st.write(f"분석된 업체 수: {len(all_company_reports)}개") 
    
    for report in all_company_reports:
        with st.expander(f"📌 {report['name']} 안내문 보기", expanded=True):
            vat_display = report['vat']
            msg = f"""안녕하세요, {report['name']} 대표님! 😊
이번 기수 부가가치세 신고 관련하여 정리된 장부 내용 안내드립니다.

✅ 매출 합계: {report['sales']:,}원
✅ 매입 합계: {report['buys']:,}원
✅ 예상 납부세액: {vat_display:,}원

(※ 마이너스(-)일 경우 환급 예정액이며, 최종 신고서상 금액과 미세한 차이가 있을 수 있습니다.)

첨부해 드린 장부 파일 확인 부탁드리며, 이상이 있으시면 말씀해 주세요. 
감사합니다!"""
            st.text_area(label="카톡 복사용", value=msg, height=210, key=f"t_{report['name']}")
else:
    st.warning("⚠️ 아직 분석된 데이터가 없습니다. 왼쪽에서 '매입/매출' 데이터가 포함된 엑셀 파일을 업로드해 주세요.")
