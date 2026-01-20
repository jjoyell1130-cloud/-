# ... (상단 import 및 Menu 1, 2 로직은 기존 그대로 유지) ...

if curr == "💳 카드매입 수기입력건":
    st.title("💳 카드매입 수기입력건")
    st.info("신한카드(거래일/가맹점명) 및 삼성카드(이용일/업종) 양식을 모두 자동으로 인식합니다.")
    
    card_up = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'], key="card_uroller")
    
    if card_up:
        raw_fn = os.path.splitext(card_up.name)[0]
        biz_name = raw_fn.split('-')[0].split('_')[0].strip()
        
        try:
            # 1. 파일 읽기
            if card_up.name.endswith('.csv'):
                try: raw_df = pd.read_csv(card_up, header=None, encoding='cp949')
                except: card_up.seek(0); raw_df = pd.read_csv(card_up, header=None, encoding='utf-8-sig')
            else:
                raw_df = pd.read_excel(card_up, header=None)

            # 2. 통합 키워드 설정 (신한/삼성 UI 대응)
            date_k = ['거래일', '이용일', '일자', '승인일']
            partner_k = ['가맹점명', '거래처', '상호', '이용처']
            amt_k = ['이용금액', '합계', '승인금액', '금액']
            item_k = ['업종', '품명', '상품명', '종목']
            card_k = ['카드번호', '카드 No', '이용카드']

            # 3. 데이터 시작점(헤더) 자동 탐색
            header_idx = None
            for i, row in raw_df.iterrows():
                row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                if any(pk in row_str for pk in partner_k) and any(ak in row_str for ak in amt_k):
                    header_idx = i; break
            
            if header_idx is not None:
                df = raw_df.iloc[header_idx+1:].copy()
                df.columns = raw_df.iloc[header_idx].values
                df = df.dropna(how='all', axis=0)

                # 컬럼 매칭
                d_col = next((c for c in df.columns if any(k in str(c) for k in date_k)), None)
                p_col = next((c for c in df.columns if any(k in str(c) for k in partner_k)), None)
                a_col = next((c for c in df.columns if any(k in str(c) for k in amt_k)), None)
                i_col = next((c for c in df.columns if any(k in str(c) for k in item_k)), None)
                n_col = next((c for c in df.columns if any(k in str(c) for k in card_k)), None)

                if p_col and a_col:
                    # 금액 숫자 변환
                    df[a_col] = df[a_col].apply(lambda x: to_int(x) if 'to_int' in globals() else int(re.sub(r'[^\d.-]', '', str(x)) if pd.notna(x) else 0))
                    df = df[df[a_col] != 0].copy()
                    
                    # 표준 컬럼으로 매핑 (공란 해결 핵심)
                    df['일자'] = df[d_col] if d_col else ""
                    df['거래처'] = df[p_col] if p_col else "상호미표기"
                    df['품명'] = df[i_col] if i_col is not None else "-" 
                    df['공급가액'] = (df[a_col] / 1.1).round(0).astype(int)
                    df['부가세'] = df[a_col] - df['공급가액']
                    df['합계'] = df[a_col]

                    # 4. 카드번호별 파일 분리
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        # 번호에서 숫자만 추출 (예: 본인8525 -> 8525)
                        df['card_id'] = df[n_col].astype(str).str.replace(r'[^0-9]', '', regex=True).str[-4:]
                        
                        final_cols = ['일자', '거래처', '품명', '공급가액', '부가세', '합계']
                        for c_num, group in df.groupby('card_id'):
                            if not c_num or c_num == 'nan' or c_num == '': continue
                            excel_buf = io.BytesIO()
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                group[final_cols].to_excel(writer, index=False)
                            zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", excel_buf.getvalue())
                    
                    st.success(f"✅ {biz_name} 처리 완료!")
                    st.download_button("📥 결과 다운로드", z_buf.getvalue(), f"{biz_name}_카드분리.zip")
            else:
                st.error("파일 양식을 인식할 수 없습니다. 가맹점명/금액 컬럼을 확인해주세요.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
