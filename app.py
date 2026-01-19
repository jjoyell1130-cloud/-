# --- [1. 세션 상태 및 설정 업데이트] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "sidebar_title": "🗂️ 업무 메뉴",
        "sidebar_label": "업무 선택",
        "menu_1": "⚖️ 마감작업", 
        # [수정] 메뉴 제목 변경
        "menu_2": "💳 카드매입 수기입력건 엑셀 변환", 
        "sub_home": "🏠 홈: 단축키 관리 및 주요 링크 바로가기",
        "sub_menu1": "국세청 PDF와 매출매입장 엑셀을 업로드하면 안내문이 자동 작성됩니다.",
        # [수정] 안내 문구를 더 정중하고 명확하게 다듬었습니다.
        "sub_menu2": "카드사별 엑셀 파일을 업로드하시면, 위하고(WEHAGO) 수기입력 양식에 맞춘 전용 파일로 즉시 변환됩니다.",
        "prompt_template": """...""" # 기존 템플릿 유지
    }

# --- [3. 메뉴별 기능 구현 구역] ---

elif selected_menu == st.session_state.config["menu_2"]:
    # 정정된 제목과 다듬어진 안내 문구가 표시됩니다.
    st.info(st.session_state.config["sub_menu2"]) # "카드사별 엑셀 파일을 업로드하시면..."
    st.file_uploader("💳 카드사 엑셀 파일 업로드", type=['xlsx'], accept_multiple_files=True)
