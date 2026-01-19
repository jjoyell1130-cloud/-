# --- [1. 홈 화면] 내 계정과목 에디터 부분 ---

st.subheader("⌨️ 차변 계정 단축키 및 메모란")
st.info("💡 '분류' 칸을 클릭하면 [매입, 일반, 공제유무확인] 중 선택할 수 있습니다.")

# 세션 상태의 데이터를 데이터프레임으로 변환
df_accounts = pd.DataFrame(st.session_state.account_data)

# 데이터 에디터 생성 (분류 열을 선택형으로 설정)
edited_df = st.data_editor(
    df_accounts,
    num_rows="dynamic", 
    use_container_width=True,
    key="account_editor",
    column_config={
        "분류": st.column_config.SelectboxColumn(
            "분류",
            help="거래의 성격을 선택하세요",
            options=["매입", "일반", "공제유무확인"], # 선택 가능한 옵션 설정
            required=True,
        ),
        "코드": st.column_config.TextColumn(
            "코드",
            help="계정 코드를 입력하세요 (예: 811)"
        )
    }
)

# 변경사항 저장 버튼
if st.button("💾 계정 리스트 변경사항 저장"):
    st.session_state.account_data = edited_df.to_dict('records')
    st.success("단축키 리스트가 성공적으로 저장되었습니다!")
