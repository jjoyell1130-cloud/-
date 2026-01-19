# Menu 0: Home
if curr == st.session_state.config["menu_0"]:
    # 1. 바로가기 버튼 섹션
    st.subheader("🔗 신속 바로가기")
    c1, c2 = st.columns(2)
    with c1: 
        st.link_button("🌐 WEHAGO 접속", "https://www.wehago.com/#/main", use_container_width=True) [cite: 22]
    with c2: 
        st.link_button("🏠 국세청 홈택스", "https://hometax.go.kr/", use_container_width=True) [cite: 22]

    st.divider()

    # 2. 전표 입력 단축키 안내 섹션
    st.subheader("⌨️ 전표 입력 코드 단축키")
    
    # 가독성을 위해 2개의 컬럼으로 나누어 표기
    short_c1, short_c2 = st.columns(2)
    
    with short_c1:
        st.info("**[차변 구분 코드]**\n* **3** : 차변\n* **1** : 출금")
        
    with short_c2:
        st.success("**[대변 구분 코드]**\n* **4** : 대변\n* **2** : 입금")

    # 상세 안내 테이블
    code_data = {
        "구분": ["입금", "출금", "차변", "대변", "결산차변", "결산대변"],
        "코드": ["1", "2", "3", "4", "5", "6"],
        "설명": ["현금 들어옴", "현금 나감", "자산증가/비용발생", "부채증가/수익발생", "결산 시 사용", "결산 시 사용"]
    }
    st.table(pd.DataFrame(code_data))
