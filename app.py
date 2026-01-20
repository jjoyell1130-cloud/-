# (이전 import 및 기초 엔진 부분은 동일하게 유지)

# ... (Menu 0, 1, 2 로직 유지) ...

# --- [Menu 3: 카드매입 수기입력건 - 오류 수정본] ---
elif curr == st.session_state.config["menu_3"]:
    st.info("신한카드/삼성카드 등 카드사 엑셀을 업로드하면 위하고 양식으로 자동 변환합니다.")
    
    card_up = st.file_uploader("카드사 엑셀/CSV 업로드", type=['xlsx', 'csv', 'xls'], key="card_m3_final")
    
    if card_up:
        raw_fn = os.path.splitext(card_up.name)[0]
        biz_name = raw_fn.split('-')[0].split('_')[0].strip()
        
        try:
            if card_up.name.endswith('.csv'):
                try: raw_df = pd.read_csv(card_up, header=None, encoding='cp949')
                except: card_up.seek(0); raw_df = pd.read_csv(card_up, header=None, encoding='utf-8-sig')
            else:
                raw_df = pd.read_excel(card_up, header=None)

            # 1. 헤더 찾기 (줄바꿈 대응)
            date_k = ['거래일', '이용일', '일자']
            partner_k = ['가맹점', '거래처', '상호', '이용처']
            amt_k = ['이용금액', '합계', '승인금액', '금액']
            sup_k = ['공급가액', '공급가']
            tax_k = ['부가세', '부가가치세']
            card_k = ['카드', '번호', 'No']

            header_idx = None
            for i, row in raw_df.iterrows():
                # 한 줄의 모든 텍스트를 합쳐서 키워드 검색 (줄바꿈/공백 제거)
                row_str = "".join([str(v) for v in row.values if pd.notna(v)]).replace("\n", "").replace(" ", "")
                if any(pk in row_str for pk in partner_k) and any(ak in row_str for ak in amt_k):
                    header_idx = i; break
            
            if header_idx is not None:
                # 헤더 정리 (\n 제거)
                cols = [str(c).replace("\n", "").replace(" ", "") for c in raw_df.iloc[header_idx].values]
                df = raw_df.iloc[header_idx+1:].copy()
                df.columns = cols
                df = df.dropna(how='all', axis=0)

                # 컬럼 자동 매칭
                d_col = next((c for c in df.columns if any(k in c for k in date_k)), None)
                p_col = next((c for c in df.columns if any(k in c for k in partner_k)), None)
                a_col = next((c for c in df.columns if any(k in c for k in amt_k)), None)
                s_col = next((c for c in df.columns if any(k in c for k in sup_k)), None)
                t_col = next((c for c in df.columns if any(k in c for k in tax_k)), None)
                n_col = next((c for c in df.columns if any(k in c for k in card_k)), None)
                item_col = next((c for c in df.columns if any(k in c for k in ['업종', '품명'])), None)

                if p_col and a_col:
                    df[a_col] = df[a_col].apply(to_int)
                    df = df[df[a_col] != 0].copy()
                    
                    # 표준 데이터 생성
                    df['일자'] = df[d_col] if d_col else ""
                    df['거래처'] = df[p_col] if p_col else "상호미표기"
                    df['품명'] = df[item_col] if item_col else "-"
                    
                    # 파일에 공급가액/부가세가 있으면 사용, 없으면 계산
                    if s_col and t_col:
                        df['공급가액'] = df[s_col].apply(to_int)
                        df['부가세'] = df[t_col].apply(to_int)
                    else:
                        df['공급가액'] = (df[a_col] / 1.1).round(0).astype(int)
                        df['부가세'] = df[a_col] - df['공급가액']
                    
                    df['합계'] = df[a_col]

                    # 카드번호별 파일 분리 (뒷 4자리 숫자만 추출)
                    z_buf = io.BytesIO()
                    with zipfile.ZipFile(z_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                        card_src = df[n_col].astype(str) if n_col else pd.Series(["0000"]*len(df))
                        df['card_id'] = card_src.str.replace(r'[^0-9]', '', regex=True).str[-4:]
                        
                        final_cols = ['일자', '거래처', '품명', '공급가액', '부가세', '합계']
                        for c_num, group in df.groupby('card_id'):
                            if not c_num or c_num == 'nan' or c_num == '': continue
                            excel_buf = io.BytesIO()
                            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                                group[final_cols].to_excel(writer, index=False)
                            zf.writestr(f"{biz_name}_카드_{c_num}.xlsx", excel_buf.getvalue())
                    
                    st.success(f"✅ {biz_name} 분석 완료!")
                    st.download_button("📥 결과(ZIP) 다운로드", z_buf.getvalue(), f"{biz_name}_카드분리.zip")
            else:
                st.error("데이터 시작점을 찾지 못했습니다. 파일의 컬럼명(가맹점명, 이용금액 등)을 확인해주세요.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
