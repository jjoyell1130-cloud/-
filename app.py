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

# --- [기초 폰트 및 공통 함수] ---
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
        # 따옴표, 쉼표, 공백 모두 제거 (삼성카드 데이터 대응)
        s = str(val).replace('"', '').replace(',', '').strip()
        return int(float(s))
    except: return 0

# (PDF 추출 및 생성 함수 등은 기존과 동일하므로 중략 가능하나, 전체 덮어쓰기용으로 포함)
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

# --- [Streamlit 설정] ---
st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = "🏠 Home"

with st.sidebar:
    st.markdown("### 📁 Menu")
    menus = ["🏠 Home", "⚖️ 마감작업", "📁 매출매입장 PDF 변환", "💳 카드매입 수기입력건"]
    for m in menus:
        if st.button(m, use_container_width=True, type="primary" if st.session_state.selected_menu == m else "secondary"):
            st.session_state.selected_menu = m
            st.rerun()

curr = st.session_state.selected_menu
st.title(curr)
st.divider()

# --- [메뉴별 로직] --- (Home, 마감작업 등 기존 코드 생략 또는 유지)

if curr == "💳 카드매입 수기입력건":
    card_up = st.file_uploader("💳 카드사 엑셀/CSV 업로드", type=['xlsx', 'csv'], key="m3_up")
    if card_up:
        # 1. 파일명 기반 업체명 및 카드사 추출
        raw_fn = os.path.splitext(card_up.name)[0]
        biz_name = re.sub(r'^(20\d{2}|위하고_|수기입력_|국세청_|카드내역_)', '', raw_fn).strip()
        biz_name = biz_name.split('-')[0].split(' ')[0].split('(')[0].strip()
        
        card_corp = "삼성" if "삼성" in raw_fn else "카드사"
        for corp in ["현대", "신한", "국민", "비씨", "하나", "우리", "농협", "롯데"]:
            if corp in raw_fn: card_corp = corp; break

        # 2. 데이터 헤더 자동 탐색 (삼성카드 CSV 헤더는 20행 근처에 있음)
        try:
            if card_up.name.endswith('.csv'):
                raw_df = pd.read_csv(card_up, header=None, encoding='utf-8')
            else:
                raw_df = pd.read_excel(card_up, header=None)
            
            header_idx = None
            for i, row in raw_df.iterrows():
                row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                if '카드번호' in row_str and ('이용금액' in row_str or '이용 금액' in row_str or '합계' in row_str):
                    header_idx = i; break
            
            if header_idx is not None:
                # 헤더 적용하여 데이터 로드
                df = raw_df.iloc[header_idx+1:].copy()
                df.columns = raw_df.iloc[header_idx].values
                df = df.dropna(how='all')

                # 컬럼명 유연하게 매칭
                num_col = next((c for c in df.columns if '카드번호' in str(c)), None)
                amt_col = next((c for c in df.columns if any(k in str(c) for k in ['이용금액', '이용 금액', '합계', '금액'])), None)
                
                if num_col and amt_col:
                    # 3. 데이터 정제 (따옴표, 쉼표 제거 후 정수 변환)
                    df[amt_col] = df[amt_col].apply(to_int)
                    df = df[df[amt_col] > 0].copy() # 합계 0원인 행 제외
                    
                    df['공급가액'] = (df[amt_col] / 1.1).round(0).astype(int)
                    df['부가세'] = df[amt_col] - df['공급가액']

                    # 4. 압축 파일 생성
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        for c_num, group in df.groupby(num_col):
                            if pd.isna(c_num) or str(c_num).strip() == "": continue
                            
                            excel_buf = io.BytesIO()
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                group.to_excel(writer, index=False)
                            
                            # 카드번호 뒷 4자리 추출
                            clean_num = str(c_num).replace("-", "").replace("'", "").strip()
                            safe_num = clean_num[-4:] if len(clean_num) >= 4 else clean_num
                            
                            final_fn = f"{biz_name}_{card_corp}_{safe_num}_(업로드용).xlsx"
                            zf.writestr(final_fn, excel_buf.getvalue())
                    
                    st.success(f"✅ {biz_name} {card_corp}카드 데이터 분리 완료!")
                    st.download_button(f"📥 {biz_name} 결과 다운로드", data=z_buf.getvalue(), file_name=f"{biz_name}_카드분리.zip", use_container_width=True)
                else:
                    st.error("카드번호나 이용금액 컬럼을 찾을 수 없습니다.")
            else:
                st.error("데이터 시작 지점을 찾지 못했습니다. 파일 구조를 확인해 주세요.")
        except Exception as e:
            st.error(f"오류 발생: {e}")

# (기타 Home, Menu 2 로직은 위와 동일한 구조로 덮어쓰기)
