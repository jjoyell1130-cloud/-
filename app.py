import streamlit as st
import pandas as pd
import io
import re
import zipfile
import pdfplumber
from datetime import datetime

# --- [세션 상태 초기화] 모든 설정값 저장 ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택:",
        "main_title": "🚀 세무 업무 통합 대시보드",
        "menu_1": "⚖️ 매출매입장 PDF & 안내문",
        "menu_2": "💳 카드별 개별 엑셀 변환"
    }

if 'link_data' not in st.session_state:
    st.session_state.link_data = [
        {"name": "WEHAGO (위하고)", "url": "https://www.wehago.com/#/main"},
        {"name": "홈택스 (Hometax)", "url": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index3"},
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 부가세 상반기", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 부가세 하반기", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드자료 보관함", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

if 'memo_content' not in st.session_state:
    st.session_state.memo_content = ""

# --- 기본 설정 ---
st.set_page_config(page_title="세무 통합 시스템", layout="wide")

# 유틸리티 함수
def to_int(val):
    try:
        if pd.isna(val): return 0
        return int(float(re.sub(r'[^0-9.-]', '', str(val))))
    except: return 0

def format_date(val):
    try:
        if isinstance(val, (int, float)):
            return pd.to_datetime(val, unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
        dt = pd.to_datetime(str(val), errors='coerce')
        return dt.strftime('%Y-%m-%d') if not pd.isna(dt) else str(val)
    except: return str(val)

# --- 사이드바 메뉴 (수정된 설정값 반영) ---
st.sidebar.title(st.session_state.config["sidebar_title"])
menu_options = ["🏠 홈 (대시보드)", st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
selected_menu = st.sidebar.radio(st.session_state.config["sidebar_label"], menu_options)

# --- [⚙️ 전체 설정창] ---
with st.expander("⚙️ 시스템 모든 명칭 및 링크 수정하기"):
    st.subheader("1. 사이드바 및 메인 제목")
    col_s1, col_s2 = st.columns(2)
    new_sidebar_title = col_s1.text_input("사이드바 상단 제목", value=st.session_state.config["sidebar_title"])
    new_sidebar_label = col_s2.text_input("사이드바 라디오 버튼 라벨", value=st.session_state.config["sidebar_label"])
    
    new_main_title = st.text_input("메인 화면 대시보드 제목", value=st.session_state.config["main_title"])
    
    col_m1, col_m2 = st.columns(2)
    new_menu1 = col_m1.text_input("업무 메뉴 1 이름", value=st.session_state.config["menu_1"])
    new_menu2 = col_m2.text_input("업무 메뉴 2 이름", value=st.session_state.config["menu_2"])
    
    st.divider()
    
    st.subheader("2. 바로가기 버튼 설정")
    new_link_data = []
    for i in range(len(st.session_state.link_data)):
        c_btn_n, c_btn_u = st.columns([1, 2])
        u_name = c_btn_n.text_input(f"버튼 {i+1} 이름", value=st.session_state.link_data[i]["name"], key=f"btn_edit_n_{i}")
        u_url = c_btn_u.text_input(f"버튼 {i+1} 주소", value=st.session_state.link_data[i]["url"], key=f"btn_edit_u_{i}")
        new_link_data.append({"name": u_name, "url": u_url})
        
    if st.button("💾 모든 설정 적용하기"):
        st.session_state.config["sidebar_title"] = new_sidebar_title
        st.session_state.config["sidebar_label"] = new_sidebar_label
        st.session_state.config["main_title"] = new_main_title
        st.session_state.config["menu_1"] = new_menu1
        st.session_state.config["menu_2"] = new_menu2
        st.session_state.link_data = new_link_data
        st.success("모든 명칭과 링크가 업데이트되었습니다!")
        st.rerun()

# --- [1. 홈 화면] ---
if selected_menu == "🏠 홈 (대시보드)":
    st.title(st.session_state.config["main_title"])
    st.markdown("---")
    
    st.subheader("🔗 바로가기")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state.link_data):
        cols[i % 3].link_button(item["name"], item["url"], use_container_width=True)
    
    st.divider()
    st.subheader("📝 업무 메모")
    st.session_state.memo_content = st.text_area("내용을 입력하세요 (자동 저장)", value=st.session_state.memo_content, height=200)

# --- [2. 업무 메뉴 1 로직] ---
elif selected_menu == st.session_state.config["menu_1"]:
    st.title(st.session_state.config["menu_1"])
    # (매출매입장 로직 동일...)
    tax_pdfs = st.file_uploader("1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True)
    excel_ledgers = st.file_uploader("2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True)
    
    final_reports = {}
    if tax_pdfs:
        for f in tax_pdfs:
            with pdfplumber.open(f) as pdf:
                text = "".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                name_match = re.search(r"상\s*호\s*[:：]\s*([가-힣\w\s]+)\n", text)
                biz_name = name_match.group(1).strip() if name_match else f.name.split('_')[0]
                if biz_name not in final_reports: final_reports[biz_name] = {"vat": 0}
                vat_match = re.search(r"(?:납부할\s*세액|차가감납부할세액|환급받을\s*세액)\s*([0-9,.-]+)", text)
                if vat_match:
                    val = to_int(vat_match.group(1))
                    final_reports[biz_name]["vat"] = -val if "환급" in text else val
    if excel_ledgers:
        for ex in excel_ledgers:
            df = pd.read_excel(ex)
            biz_name = ex.name.split('_')[0]
            if biz_name not in final_reports: final_reports[biz_name] = {"vat": 0}
            try:
                s_sum = to_int(df[df.iloc[:, 0].astype(str).str.contains('매출|매입', na=False)].iloc[:, -1].sum()) # 예시 로직
                final_reports[biz_name].update({"sales_info": "분석됨"})
            except: pass
    if final_reports:
        for name, info in final_reports.items():
            with st.expander(f"📌 {name} 결과"):
                st.write(f"납부/환급액: {info.get('vat', 0):,}원")

# --- [3. 업무 메뉴 2 로직] ---
elif selected_menu == st.session_state.config["menu_2"]:
    st.title(st.session_state.config["menu_2"])
    uploaded_files = st.file_uploader("카드사 엑셀 업로드", type=['xlsx', 'xls', 'xlsm'], accept_multiple_files=True)
    if uploaded_files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in uploaded_files:
                fname = file.name
                year, company, brand = datetime.now().strftime('%Y'), "업체명", "카드"
                m = re.search(r'(\d{4})\s*([가-힣\w\s]+?)-', fname)
                if m: year, company = m.group(1), m.group(2).strip()
                if '국민' in fname: brand = "국민"
                elif '비씨' in fname: brand = "비씨"
                
                df_raw = pd.read_excel(file, header=None)
                h_idx = 0
                for i in range(min(40, len(df_raw))):
                    row_s = "".join([str(v) for v in df_raw.iloc[i].values])
                    if any(k in row_s for k in ['카드번호', '이용일', '매출일']):
                        h_idx = i; break
                file.seek(0)
                df = pd.read_excel(file, header=h_idx)
                df.columns = [str(c).strip() for c in df.columns]
                col_map = {'매출일자': ['이용일', '승인일', '매출일'], '카드번호': ['카드번호', '카드명'], 
                           '가맹점명': ['가맹점', '이용처'], '사업자번호': ['사업자', '등록번호'], '매출금액': ['금액', '합계', '이용금액']}
                tmp = pd.DataFrame()
                for std, aliases in col_map.items():
                    act = next((c for c in df.columns if any(a in str(c) for a in aliases)), None)
                    tmp[std] = df[act] if act else ""
                tmp['매출일자'] = tmp['매출일자'].apply(format_date)
                tmp['매출금액'] = tmp['매출금액'].apply(to_int)
                tmp = tmp[tmp['매출금액'] > 0].copy()
                tmp['공급가액'] = (tmp['매출금액'] / 1.1).round(0).astype(int)
                tmp['부가세'] = tmp['매출금액'] - tmp['공급가액']
                tmp['C_ID'] = tmp['카드번호'].astype(str).apply(lambda x: re.sub(r'\D', '', x)[-4:] if len(re.sub(r'\D', '', x)) >= 4 else "0000")
                for cid in tmp['C_ID'].unique():
                    f_df = tmp[tmp['C_ID'] == cid][['카드번호', '매출일자', '사업자번호', '가맹점명', '매출금액', '공급가액', '부가세']]
                    new_name = f"{year} {company}-카드사용내역({brand}{cid})(업로드용).xlsx"
                    buf = io.BytesIO()
                    f_df.to_excel(buf, index=False)
                    zf.writestr(new_name, buf.getvalue())
        st.download_button("📥 변환 완료 파일 다운로드", zip_buffer.getvalue(), "카드데이터분리.zip")
