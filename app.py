import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re

# --- [1. 기초 설정 및 헬퍼 함수] ---
def get_processed_excel(file):
    df = pd.read_excel(file)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# --- [2. 세션 상태 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환",
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "안내문 자동 작성 및 엑셀 가공 도구입니다.",
        "sub_menu2": "매출매입장을 깔끔한 PDF로 일괄 변환합니다.",
        "sub_menu3": "불필요한 항목 제거 및 날짜 간소화 후 카드별로 파일을 분리합니다."
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

# --- [4. 메인 화면 로직] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()

if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)

elif current_menu == st.session_state.config["menu_1"]:
    st.info(st.session_state.config["sub_menu1"])
    excel_up = st.file_uploader("📊 매출매입장 업로드", type=['xlsx'], key="m1_up")
    if excel_up:
        st.download_button("📥 가공 파일 다운로드", data=get_processed_excel(excel_up), file_name=f"가공_{excel_up.name}")

elif current_menu == st.session_state.config["menu_3"]:
    st.info(st.session_state.config["sub_menu3"])
    card_up = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], key="m3_up")
    
    if card_up:
        # 1. 파일명 정리
        raw_filename = os.path.splitext(card_up.name)[0]
        clean_name = raw_filename.replace("위하고_수기입력_", "")
        clean_name = re.sub(r'\(.*?\)', '', clean_name).strip()
        
        # 2. 헤더 위치 자동 찾기
        temp_df = pd.read_excel(card_up, header=None)
        target_row = 0
        for i, row in temp_df.iterrows():
            row_str = " ".join(row.astype(str))
            if any(kw in row_str for kw in ['카드번호', '매출금액', '이용일']):
                target_row = i
                break
        
        df = pd.read_excel(card_up, header=target_row)
        
        # 3. 불필요한 열 삭제 (Unnamed, 취소여부, 매출구분)
        # Unnamed 열 찾기
        unnamed_cols = [c for c in df.columns if 'Unnamed' in str(c)]
        # 명시적 삭제 열
        drop_targets = ['취소여부', '매출구분']
        cols_to_drop = unnamed_cols + [c for c in drop_targets if c in df.columns]
        df = df.drop(columns=cols_to_drop)
        
        # 4. 이용일 간소화 (예: 2025-01-01 형식으로 변환)
        date_col = next((c for c in df.columns if '이용일' in str(c)), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # 5. 필수 컬럼 매칭
        card_num_col = next((c for c in df.columns if '카드번호' in str(c)), None)
        amt_col = next((c for c in df.columns if any(kw in str(c) for kw in ['매출금액', '금액', '합계', '이용금액'])), None)
        card_co_col = next((c for c in df.columns if any(kw in str(c) for kw in ['카드사', '기관', '카드명'])), None)
        
        if card_num_col and amt_col:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                grouped = df.groupby(card_num_col)
                
                for card_num, group in grouped:
                    if pd.isna(card_num) or str(card_num).strip() == "": continue
                    
                    upload_df = group.copy()
                    
                    # 공급가/부가세 계산
                    upload_df[amt_col] = pd.to_numeric(upload_df[amt_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    upload_df['공급가액'] = (upload_df[amt_col] / 1.1).round(0).astype(int)
                    upload_df['부가세'] = upload_df[amt_col] - upload_df['공급가액']
                    
                    # 파일명 결정
                    safe_num = str(card_num).replace('*', '').strip()
                    card_company = str(group[card_co_col].iloc[0]) if card_co_col else "카드"
                    new_file_name = f"{clean_name}_{card_company}_{safe_num}_(업로드용).xlsx"
                    
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        upload_df.to_excel(writer, index=False)
                    zf.writestr(new_file_name, excel_buffer.getvalue())
            
            st.success(f"✅ 필터링 완료! {len(grouped)}개의 정돈된 파일을 생성했습니다.")
            st.download_button(
                label=f"📥 {clean_name} 필터링 완료 파일 다운로드 (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"{clean_name}_가공분리.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.error("카드번호나 금액 컬럼을 찾을 수 없습니다.")
