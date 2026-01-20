# ... (상단 생략) ...

            # 2. 헤더 탐색 키워드 (신한카드 '거래일' 추가)
            card_keywords = ['카드번호', '카드 No', '이용카드', '카드명']
            amt_keywords = ['이용금액', '합계', '승인금액', '금액', '결제액']
            partner_keywords = ['가맹점명', '거래처', '상호', '내용', '이용처']
            item_keywords = ['업종', '품명', '상품명', '항목', '종목']
            date_keywords = ['거래일', '이용일', '일자', '승인일']

            header_idx = None
            for i, row in raw_df.iterrows():
                row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                if any(ck in row_str for ck in card_keywords) and any(ak in row_str for ak in amt_keywords):
                    header_idx = i
                    break
            
            if header_idx is not None:
                df = raw_df.iloc[header_idx+1:].copy()
                df.columns = raw_df.iloc[header_idx].values
                df = df.dropna(how='all', axis=0)

                # 컬럼 매칭 (가장 유사한 것 찾기)
                num_col = next((c for c in df.columns if any(ck in str(c) for ck in card_keywords)), None)
                amt_col = next((c for c in df.columns if any(ak in str(c) for ak in amt_keywords)), None)
                partner_col = next((c for c in df.columns if any(pk in str(c) for pk in partner_keywords)), None)
                item_col = next((c for c in df.columns if any(ik in str(c) for ik in item_keywords)), None)
                date_col = next((c for c in df.columns if any(dk in str(c) for dk in date_keywords)), None)
                
                if num_col and amt_col:
                    df[amt_col] = df[amt_col].apply(to_int)
                    df = df[df[amt_col] != 0].copy()
                    
                    # [핵심] 데이터가 없어도 공란 대신 기본값 채우기
                    df['거래처'] = df[partner_col] if partner_col else "상호미표기"
                    df['품명'] = df[item_col] if item_col else "-"  # 신한카드처럼 업종이 없으면 '-' 표시
                    df['일자'] = df[date_col] if date_col else ""
                    
                    df['공급가액'] = (df[amt_col] / 1.1).round(0).astype(int)
                    df['부가세'] = df[amt_col] - df['공급가액']
                    df['합계'] = df[amt_col]

                    # 출력 컬럼 확정
                    final_cols = ['일자', '거래처', '품명', '공급가액', '부가세', '합계']
                    
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        # 신한카드는 '본인8525'처럼 글자가 섞여있으므로 숫자만 추출
                        df['card_group'] = df[num_col].astype(str).str.replace(r'[^0-9]', '', regex=True).str[-4:]
                        
                        for c_num, group in df.groupby('card_group'):
                            if not c_num or c_num == 'nan' or c_num == '': continue
                            excel_buf = io.BytesIO()
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                group[final_cols].to_excel(writer, index=False)
                            zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", excel_buf.getvalue())
# ... (하단 동일) ...
