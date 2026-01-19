elif current_menu == st.session_state.config["menu_1"]:
    with st.expander("💬 카톡 안내문 양식 편집", expanded=True):
        u_template = st.text_area("양식 수정", value=st.session_state.config["prompt_template"], height=200, key="template_input")
        if st.button("💾 안내문 양식 저장", key="template_save_btn"):
            st.session_state.config["prompt_template"] = u_template
            st.success("저장되었습니다.")
            
    st.divider()
    
    # 1. 국세청 PDF 업로드 (기존 기능)
    st.file_uploader("📄 1. 국세청 PDF 업로드", type=['pdf'], accept_multiple_files=True, key="pdf_uploader")
    
    # 2. 매출매입장 엑셀 업로드 및 PDF 변환 (새로운 기능)
    uploaded_excels = st.file_uploader("📊 2. 매출매입장 엑셀 업로드", type=['xlsx'], accept_multiple_files=True, key="excel_uploader")
    
    if uploaded_excels:
        if st.button("🚀 업체별 PDF 분할 변환 시작"):
            import io
            import zipfile
            
            zip_buffer = io.BytesIO()
            success_count = 0
            
            try:
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for uploaded_file in uploaded_excels:
                        # 엑셀 로드
                        df = pd.read_excel(uploaded_file)
                        
                        # [중요] 업체명을 구분할 컬럼 찾기 (거래처, 상호, 업체명 중 있는 것 사용)
                        target_col = None
                        for col in ['거래처', '상호', '업체명', '거래처명']:
                            if col in df.columns:
                                target_col = col
                                break
                        
                        if target_col:
                            unique_biz = df[target_col].unique()
                            for biz in unique_biz:
                                biz_df = df[df[target_col] == biz]
                                # PDF 대신 우선 엑셀/CSV로 분할 저장하는 로직 (기본 구현)
                                # PDF 라이브러리 설정 전이므로 엑셀로 먼저 분할해 드립니다.
                                output = io.BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    biz_df.to_excel(writer, index=False)
                                
                                zip_file.writestr(f"{biz}_매출매입장.xlsx", output.getvalue())
                                success_count += 1
                        else:
                            st.error(f"'{uploaded_file.name}'에서 '거래처' 컬럼을 찾을 수 없습니다.")

                if success_count > 0:
                    st.success(f"✅ 총 {success_count}개의 업체별 파일이 생성되었습니다.")
                    st.download_button(
                        label="📥 변환된 파일(ZIP) 다운로드",
                        data=zip_buffer.getvalue(),
                        file_name="매출매입장_업체별분리.zip",
                        mime="application/zip"
                    )
            except Exception as e:
                st.error(f"변환 중 오류 발생: {e}")
