# 사이드바: 매출매입장 PDF 생성 (여러 파일 지원)
st.sidebar.title("📑 매출매입장 PDF 생성")
# accept_multiple_files=True 옵션을 추가하여 여러 파일 선택 가능하게 함
uploaded_excels = st.sidebar.file_uploader("엑셀 파일들을 업로드하세요", type=['xlsx'], accept_multiple_files=True)

if uploaded_excels:
    if not font_status:
        st.sidebar.error("❌ malgun.ttf 폰트 파일이 없습니다.")
    else:
        # 업로드된 각 파일에 대해 반복 실행
        for uploaded_excel in uploaded_excels:
            try:
                # 파일명에서 업체명 추출 (예: '에덴인테리어_매입매출장.xlsx' -> '에덴인테리어')
                file_display_name = uploaded_excel.name.split('.')[0]
                
                df_excel = pd.read_excel(uploaded_excel)
                date_series = df_excel['전표일자'].dropna().astype(str)
                date_range = f"{date_series.min()} ~ {date_series.max()}" if not date_series.empty else "기간 없음"
                
                clean_df = df_excel[df_excel['구분'].isin(['매입', '매출'])].copy()
                
                st.sidebar.markdown(f"---")
                st.sidebar.write(f"📂 **{file_display_name}** 처리 중...")

                for g in ['매출', '매입']:
                    target = clean_df[clean_df['구분'] == g].reset_index(drop=True)
                    if not target.empty:
                        pdf_out = make_pdf_buffer(target, f"{g[0]} {g[1]} 장", date_range)
                        st.sidebar.download_button(
                            label=f"📥 {file_display_name}_{g}장 다운로드",
                            data=pdf_out,
                            file_name=f"{file_display_name}_{g}장.pdf",
                            mime="application/pdf",
                            key=f"{file_display_name}_{g}" # 버튼마다 고유 키 필요
                        )
            except Exception as e:
                st.sidebar.error(f"❌ {uploaded_excel.name} 처리 중 오류: {e}")
        
        st.sidebar.success("✅ 모든 파일 변환 완료!")
