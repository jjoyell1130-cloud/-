# --- [사이드바 구성] ---
with st.sidebar:
    st.markdown("### 📁 Menu")
    st.write("")
    
    menu_items = [st.session_state.config["menu_0"], st.session_state.config["menu_1"], st.session_state.config["menu_2"]]
    
    for m_name in menu_items:
        is_selected = (st.session_state.selected_menu == m_name)
        if st.button(m_name, key=f"m_btn_{m_name}", use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state.selected_menu = m_name
            st.rerun()

    # --- 에러 방지를 위한 안전한 하단 밀기 로직 ---
    # 빈 공간을 만들어 메모를 아래로 보냅니다.
    st.container() 
    for _ in range(10): 
        st.text("") 
    
    st.divider()
    
    st.markdown("#### 📝 Memo")
    # key값을 고유하게 부여하여 충돌 방지
    side_memo = st.text_area(
        "Memo Content", 
        value=st.session_state.daily_memo, 
        height=200, 
        placeholder="내용을 입력하세요...",
        label_visibility="collapsed",
        key="side_memo_input"
    )
    if st.button("💾 저장", key="memo_save_btn", use_container_width=True):
        st.session_state.daily_memo = side_memo
        st.success("저장되었습니다.")
    
