# --- [5. 메인 화면 구성] ---
current_menu = st.session_state.selected_menu
st.title(current_menu)

# 서브 헤더 텍스트 설정
if current_menu == st.session_state.config["menu_1"]:
    st.markdown(f"<p style='color: #666; font-size: 15px;'>{st.session_state.config['sub_menu1']}</p>", unsafe_allow_html=True)
elif current_menu == st.session_state.config["menu_2"]:
    st.markdown(f"<p style='color: #666; font-size: 15px;'>{st.session_state.config['sub_menu2']}</p>", unsafe_allow_html=True)
elif current_menu == st.session_state.config["menu_3"]:
    st.markdown(f"<p style='color: #666; font-size: 15px;'>{st.session_state.config['sub_menu3']}</p>", unsafe_allow_html=True)

st.divider()

# --- 메뉴별 상세 로직 ---
if current_menu == st.session_state.config["menu_0"]:
    st.subheader("🔗 바로가기")
    c1, c2 = st.columns(2)
    with c1: st.link_button("WEHAGO (위하고)", "https://www.wehago.com/#/main", use_container_width=True)
    with c2: st.link_button("🏠 홈택스", "https://hometax.go.kr/", use_container_width=True)
    st.write("")
    c3, c4, c5, c6 = st.columns(4)
    links = st.session_state.link_group_2
    with c3: st.link_button(links[0]["name"], links[0]["url"], use_container_width=True)
    with c4: st.link_button(links[1]["name"], links[1]["url"], use_container_width=True)
    with c5: st.link_button(links[2]["name"], links[2]["url"], use_container_width=True)
    with c6: st.link_button(links[3]["name"], links[3]["url"], use_container_width=True)
    st.divider()
    st.subheader("⌨️ 차변계정 단축키")
    df_acc = pd.DataFrame(st.session_state.account_data)
    edited_df = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_editor")
    if st.button("💾 리스트 저장", key="save_acc_list"):
        st.session_state.account_data = edited_df.to_dict('records')
        st.success("데이터가 저장되었습니다.")

elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=200, key="tmpl_area")
        if st.button("💾 안내문 양식 저장", key="save_tmpl"):
            st.session_state.config["prompt_template"] = u_template
            st.success("저장되었습니다.")
    st.divider()
    pdf_up = st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True, key="pdf_up")
    if pdf_up:
        st.download_button("📥 가공된 PDF 다운로드", data=pdf_up[0].getvalue(), file_name="가공_국세청자료.pdf", use_container_width=True)
    excel_up = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], key="excel_up")
    if excel_up:
        st.download_button("📥 가공된 매출매입장 다운로드", data=get_processed_excel(excel_up), file_name=f"가공_{excel_up.name}", use_container_width=True)

elif current_menu == st.session_state.config["menu_2"]:
    f = st.file_uploader("📊 엑셀 파일 업로드", type=['xlsx'], key="pdf_conv_uploader")
    if f:
        df = pd.read_excel(f)
        biz_name = f.name.split(" ")[0]
        try:
            tmp_d = pd.to_datetime(df['전표일자'], errors='coerce').dropna()
            d_range = f"{tmp_d.min().strftime('%Y-%m-%d')} ~ {tmp_d.max().strftime('%Y-%m-%d')}" if not tmp_d.empty else "기간정보없음"
        except: d_range = "기간 정보 확인 필요"
        
        type_col = next((c for c in ['구분', '유형'] if c in df.columns), None)
        if type_col:
            st.success(f"데이터 분석 완료: {biz_name} ({d_range})")
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                for g in ['매출', '매입']:
                    target = df[df[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                    if not target.empty:
                        pdf = make_pdf_stream(target, f"{g} 장", biz_name, d_range)
                        zf.writestr(f"{biz_name}_{g}장.pdf", pdf.getvalue())
            st.download_button(label="🎁 매출/매입장 PDF 일괄 다운로드 (ZIP)", data=zip_buf.getvalue(), file_name=f"{biz_name}_매출매입장_일괄.zip", mime="application/zip", use_container_width=True)
        else:
            st.error("'구분' 또는 '유형' 컬럼을 찾을 수 없습니다.")

elif current_menu == st.session_state.config["menu_3"]:
    card_up = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], key="card_up")
    if card_up:
        df = pd.read_excel(card_up)
        base_filename = os.path.splitext(card_up.name)[0]
        
        # 컬럼 자동 찾기
        card_co_col = next((c for c in ['카드사', '카드기관', '카드명', '발급사'] if c in df.columns), None)
        card_num_col = next((c for c in ['카드번호', '카드번호별', '계좌번호'] if c in df.columns), None)
        amt_col = next((c for c in ['이용금액', '합계금액', '금액', '승인금액'] if c in df.columns), None)
        
        if card_co_col and card_num_col:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                grouped = df.groupby([card_co_col, card_num_col])
                for (card_co, card_num), group in grouped:
                    upload_df = group.copy()
                    if amt_col:
                        upload_df['공급가액'] = (upload_df[amt_col] / 1.1).round(0).astype(int)
                        upload_df['부가세'] = upload_df[amt_col] - upload_df['공급가액']
                    
                    # 파일명: 제목_카드사_카드번호_(업로드용).xlsx
                    safe_card_num = str(card_num).replace('*', '').strip()
                    new_file_name = f"{base_filename}_{card_co}_{safe_card_num}_(업로드용).xlsx"
                    
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        upload_df.to_excel(writer, index=False)
                    zf.writestr(new_file_name, excel_buffer.getvalue())
            
            st.success(f"✅ 총 {len(grouped)}개의 카드 파일이 생성되었습니다.")
            st.download_button(label=f"📥 {base_filename} 카드별 분리 다운로드 (ZIP)", data=zip_buffer.getvalue(), file_name=f"{base_filename}_카드별분리.zip", mime="application/zip", use_container_width=True)
        else:
            st.error("엑셀 파일에서 '카드사'와 '카드번호' 컬럼을 찾을 수 없습니다.")
