import streamlit as st
import pandas as pd
import io
import os
import zipfile
import re

# --- [1. 기초 가공 및 세션 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환",
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF 및 엑셀 가공 후 안내문을 작성합니다.",
        "sub_menu2": "매출매입장을 깔끔한 PDF 압축파일로 변환합니다.",
        "sub_menu3": "불필요 열 삭제 및 날짜 간소화 후 카드별로 파일을 분리합니다.",
        "prompt_template": "*(업체명) 부가세 신고현황..."
    }

if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = st.session_state.config["menu_0"]

if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제확인"}]

# --- [2. 사이드바 및 레이아웃] ---
st.set_page_config(page_title="세무 통합 관리 시스템", layout="wide")

with st.sidebar:
    st.markdown("### 📁 Menu")
    for k in ["menu_0", "menu_1", "menu_2", "menu_3"]:
        m_name = st.session_state.config[k]
        if st.button(m_name, key=f"btn_{k}", use_container_width=True, 
                     type="primary" if st.session_state.selected_menu == m_name else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

# --- [3. 메인 로직 영역] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)
st.divider()

# --- 메뉴 0: Home (바로가기 & 단축키 관리) ---
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 업무 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    
    st.divider()
    st.subheader("⌨️ 차변계정 단축키 관리")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True)
    if st.button("💾 단축키 리스트 저장"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("단축키 정보가 업데이트되었습니다.")

# --- 메뉴 1: 마감작업 (안내문 & 엑셀가공) ---
elif current_menu == st.session_state.config["menu_1"]:
    st.info(st.session_state.config["sub_menu1"])
    with st.expander("💬 안내문 양식 편집"):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=150)
        if st.button("💾 양식 저장"):
            st.session_state.config["prompt_template"] = u_template
            st.success("안내문 양식이 저장되었습니다.")
    
    excel_up = st.file_uploader("📊 매출매입장 엑셀 업로드", type=['xlsx'], key="m1_excel")
    if excel_up:
        df_tmp = pd.read_excel(excel_up)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_tmp.to_excel(writer, index=False)
        st.download_button("📥 가공된 엑셀 다운로드", data=output.getvalue(), file_name=f"가공_{excel_up.name}")

# --- 메뉴 2: 매출매입장 PDF 변환 ---
elif current_menu == st.session_state.config["menu_2"]:
    st.info(st.session_state.config["sub_menu2"])
    f_pdf = st.file_uploader("📊 엑셀 파일 업로드 (PDF 변환용)", type=['xlsx'], key="m2_pdf")
    if f_pdf:
        st.write("✅ 파일 분석 완료. (PDF 변환 엔진 가동 준비)")
        # 여기에 이전에 구현했던 PDF 변환 로직이 연결됩니다.

# --- 메뉴 3: 카드매입 수기입력건 (최종 가공 로직) ---
elif current_menu == st.session_state.config["menu_3"]:
    st.info(st.session_state.config["sub_menu3"])
    card_up = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], key="m3_card")
    
    if card_up:
        # 1. 파일명 정리 (접두어 및 기존 카드번호 목록 삭제)
        raw_fn = os.path.splitext(card_up.name)[0]
        clean_name = raw_fn.replace("위하고_수기입력_", "")
        clean_name = re.sub(r'\(.*?\)', '', clean_name).strip()
        
        # 2. 헤더 찾기 (데이터 시작점 자동 스캔)
        temp_df = pd.read_excel(card_up, header=None)
        target_row = 0
        for i, row in temp_df.iterrows():
            row_str = " ".join(row.astype(str))
            if any(kw in row_str for kw in ['카드번호', '매출금액', '이용일']):
                target_row = i
                break
        
        df = pd.read_excel(card_up, header=target_row)
        
        # 3. 불필요 열(Unnamed, 취소여부, 매출구분) 삭제
        unnamed_cols = [c for c in df.columns if 'Unnamed' in str(c)]
        drop_targets = ['취소여부', '매출구분']
        df = df.drop(columns=unnamed_cols + [c for c in drop_targets if c in df.columns])
        
        # 4. 이용일 간소화
        date_col = next((c for c in df.columns if '이용일' in str(c)), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # 5. 컬럼 매칭 및 파일 분리
        num_col = next((c for c in df.columns if '카드번호' in str(c)), None)
        amt_col = next((c for c in df.columns if any(kw in str(c) for kw in ['매출금액', '금액', '합계'])), None)
        co_col = next((c for c in df.columns if any(kw in str(c) for kw in ['카드사', '기관', '카드명'])), None)
        
        if num_col and amt_col:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                grouped = df.groupby(num_col)
                for card_num, group in grouped:
                    if pd.isna(card_num) or str(card_num).strip() == "": continue
                    
                    up_df = group.copy()
                    # 금액 가공
                    up_df[amt_col] = pd.to_numeric(up_df[amt_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    up_df['공급가액'] = (up_df[amt_col] / 1.1).round(0).astype(int)
                    up_df['부가세'] = up_df[amt_col] - up_df['공급가액']
                    
                    # 새 파일명 규칙 적용
                    safe_num = str(card_num).replace('*', '').strip()
                    card_co = str(group[co_col].iloc[0]) if co_col else "카드"
                    new_fn = f"{clean_name}_{card_co}_{safe_num}_(업로드용).xlsx"
                    
                    excel_buf = io.BytesIO()
                    with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                        up_df.to_excel(writer, index=False)
                    zf.writestr(new_fn, excel_buf.getvalue())
            
            st.success(f"✅ {len(grouped)}개의 카드 파일로 정리가 완료되었습니다.")
            st.download_button(
                label="📥 가공 및 분리 완료 파일(ZIP) 다운로드",
                data=zip_buffer.getvalue(),
                file_name=f"{clean_name}_최종가공.zip",
                mime="application/zip",
                use_container_width=True
            )
