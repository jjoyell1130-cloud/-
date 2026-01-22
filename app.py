# --- [기존 코드 동일 유지 ... ] ---

elif curr == st.session_state.config["menu_2"]:
    # 1. 여러 개 업로드 가능하도록 accept_multiple_files=True 추가
    f_pdfs = st.file_uploader("📊 엑셀 파일 업로드 (여러 파일 선택 가능)", type=['xlsx'], accept_multiple_files=True, key="m2_up")
    
    if f_pdfs:
        zip_buf = io.BytesIO()
        # 처리된 업체명을 ZIP 파일명으로 쓰기 위해 첫 번째 파일에서 추출
        first_biz = f_pdfs[0].name.split(" ")[0]
        
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zf:
            for f_pdf in f_pdfs:
                df_all = pd.read_excel(f_pdf)
                # 파일명에서 업체명 추출 (공백 기준 첫 단어)
                biz_name = f_pdf.name.split(" ")[0]
                
                try:
                    tmp_d = pd.to_datetime(df_all['전표일자'], errors='coerce').dropna()
                    d_range = f"{tmp_d.min().strftime('%Y-%m-%d')} ~ {tmp_d.max().strftime('%Y-%m-%d')}"
                except: 
                    d_range = "2025년"
                
                type_col = next((c for c in ['구분', '유형'] if c in df_all.columns), None)
                
                if type_col:
                    for g in ['매출', '매입']:
                        tgt = df_all[df_all[type_col].astype(str).str.contains(g, na=False)].reset_index(drop=True)
                        if not tgt.empty:
                            pdf = make_pdf_stream(tgt, f"{g} 장", biz_name, d_range)
                            # 요청하신 파일명 규칙 적용: 2025 업체명 매출장.pdf / 2025 업체명 매입장.pdf
                            new_filename = f"2025 {biz_name} {g}장.pdf"
                            zf.writestr(new_filename, pdf.getvalue())
        
        st.success(f"✅ 총 {len(f_pdfs)}개의 파일 가공 완료")
        st.download_button(
            "🎁 가공된 PDF들(ZIP) 다운로드", 
            data=zip_buf.getvalue(), 
            file_name=f"{first_biz}_외_매출매입장_모음.zip", 
            use_container_width=True
        )

# --- [이후 카드매입 수기입력건 등 기존 코드 동일 유지 ... ] ---
