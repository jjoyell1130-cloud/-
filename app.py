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

    # --- 여백을 만들어 메모란을 하단으로 밀어냄 ---
    for _ in range(15): # 필요에 따라 범위를 조절하여 높이를 맞출 수 있습니다.
        st.sidebar.write("") 
    
    st.divider()
    
    st.markdown("#### 📝 Memo")
    side_memo = st.text_area(
        "Memo Content", 
        value=st.session_state.daily_memo, 
        height=200, 
        placeholder="Enter your notes here...",
        label_visibility="collapsed"
    )
    if st.button("💾 저장", use_container_width=True):
        st.session_state.daily_memo = side_memo
        st.success("저장되었습니다.")
