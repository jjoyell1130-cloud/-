# --- 메뉴별 상세 로직 (이 부분을 찾아서 수정하세요) ---

if current_menu == st.session_state.config["menu_0"]:
    # 홈 화면 로직 (기존 코드 유지)
    st.subheader("🔗 바로가기")
    # ... (생략) ...

elif current_menu == st.session_state.config["menu_1"]:
    # 마감작업 로직 (기존 코드 유지)
    # ... (생략) ...

elif current_menu == st.session_state.config["menu_2"]:
    # PDF 변환 로직 (기존 코드 유지)
    # ... (생략) ...

# 여기부터 Menu 3입니다. 기존 내용을 지우고 아래를 붙여넣으세요.
elif current_menu == st.session_state.config["menu_3"]:
    st.markdown(f"<p style='color: #666; font-size: 15px;'>{st.session_state.config['sub_menu3']}</p>", unsafe_allow_html=True)
    
    card_up = st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], key="card_up")
    
    if card_up:
        df = pd.read_excel(card_up)
        base_filename = os.path.splitext(card_up.name)[0]
        
        # 1. 컬럼명 자동 매칭 (유연하게 검색)
        card_co_col = next((c for c in ['카드사', '카드기관', '카드명', '발급사'] if c in df.columns), None)
        card_num_col = next((c for c in ['카드번호', '카드번호별', '계좌번호'] if c in df.columns), None)
        amt_col = next((c for c in ['이용금액', '합계금액', '금액', '승인금액'] if c in df.columns), None)
        
        if card_co_col and card_num_col:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                # 2. 카드사/카드번호별 그룹화
                grouped = df.groupby([card_co_col, card_num_col])
                
                for (card_co, card_num), group in grouped:
                    upload_df = group.copy()
                    
                    # 3. 위하고용 금액 계산 (공급가/부가세)
                    if amt_col:
                        upload_df['공급가액'] = (upload_df[amt_col] / 1.1).round(0).astype(int)
                        upload_df['부가세'] = upload_df[amt_col] - upload_df['공급가액']
                    
                    # 4. 파일명 규칙: 제목_카드사_카드번호_(업로드용).xlsx
                    safe_card_num = str(card_num).replace('*', '').strip()
                    new_file_name = f"{base_filename}_{card_co}_{safe_card_num}_(업로드용).xlsx"
                    
                    # 5. 메모리 내 엑셀 생성 및 압축파일 추가
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        upload_df.to_excel(writer, index=False)
                    
                    zf.writestr(new_file_name, excel_buffer.getvalue())
            
            st.success(f"✅ 총 {len(grouped)}개의 카드 파일이 생성되었습니다.")
            
            # 6. ZIP 다운로드 버튼
            st.download_button(
                label=f"📥 {base_filename} 카드별 분리 다운로드 (ZIP)",
                data=zip_buffer.getvalue(),
                file_name=f"{base_filename}_카드별분리.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.error("엑셀 파일에서 '카드사'와 '카드번호' 컬럼을 찾을 수 없습니다.")
