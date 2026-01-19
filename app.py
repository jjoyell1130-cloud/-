elif current_menu == st.session_state.config["menu_3"]:
    # 카드매입 화면: 카드번호별 파일 분리 및 자동 명칭 부여 로직 통합
    st.markdown(f"<p style='color: #666; font-size: 15px;'>{st.session_state.config['sub_menu3']}</p>", unsafe_allow_html=True)
    
    card_up = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], key="card_up")
    
    if card_up:
        # 1. 파일 읽기 및 기본 파일명 추출
        df = pd.read_excel(card_up)
        base_filename = os.path.splitext(card_up.name)[0]
        
        # 필수 컬럼 존재 여부 확인 (카드사, 카드번호 컬럼명은 데이터에 맞게 조정 필요)
        # 예: '카드사', '카드번호' 혹은 '카드명', '계좌번호' 등
        card_co_col = next((c for c in ['카드사', '카드기관', '카드명'] if c in df.columns), None)
        card_num_col = next((c for c in ['카드번호', '카드번호별', '계좌번호'] if c in df.columns), None)
        
        if card_co_col and card_num_col:
            # ZIP 파일 생성을 위한 메모리 버퍼
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                # 2. 카드사 및 카드번호별로 그룹화
                grouped = df.groupby([card_co_col, card_num_col])
                
                for (card_co, card_num), group in grouped:
                    # 3. 위하고 양식 변환 로직 적용
                    upload_df = group.copy()
                    
                    # 이용금액 컬럼 찾기 (금액, 합계 등)
                    amt_col = next((c for c in ['이용금액', '합계금액', '금액', '승인금액'] if c in upload_df.columns), None)
                    
                    if amt_col:
                        # 공급가액/부가세 계산 (반올림 포함)
                        upload_df['공급가액'] = (upload_df[amt_col] / 1.1).round(0).astype(int)
                        upload_df['부가세'] = upload_df[amt_col] - upload_df['공급가액']
                    
                    # 4. 파일명 규칙 적용: 제목_카드사_카드번호_(업로드용).xlsx
                    # 파일명에 사용할 수 없는 문자 제거 (카드번호의 * 등)
                    safe_card_num = str(card_num).replace('*', '').strip()
                    new_file_name = f"{base_filename}_{card_co}_{safe_card_num}_(업로드용).xlsx"
                    
                    # 5. 메모리 내에서 엑셀 파일 생성
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        upload_df.to_excel(writer, index=False)
                    
                    # 6. ZIP 파일에 추가
                    zf.writestr(new_file_name, excel_buffer.getvalue())
            
            st.success(f"✅ 총 {len(grouped)}개의 카드번호가 식별되었습니다.")
            
            # 7. 최종 압축파일 다운로드 버튼
            st.download_button(
                label=f"📥 {base_filename} 카드별 분리 다운로드 (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"{base_filename}_카드별분리.zip",
                mime="application/zip",
                use_container_width=True,
                key="card_zip_dl"
            )
        else:
            st.error("엑셀 파일에서 '카드사'와 '카드번호' 컬럼을 찾을 수 없습니다. 컬럼명을 확인해 주세요.")
