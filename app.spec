import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import unicodedata

# --- [PDF 클래스: 인코딩 및 한글 최적화] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
        # 맑은 고딕 폰트 적용 (malgun.ttf 파일이 루트 폴더에 있어야 함)
        try:
            self.add_font('Malgun', '', 'malgun.ttf', unicode=True)
            self.font_set = 'Malgun'
        except:
            self.font_set = 'Arial'

    def header(self):
        self.set_font(self.font_set, '', 20)
        # NFC 정규화로 한글 깨짐 방지
        title = unicodedata.normalize('NFC', self.title_text)
        self.cell(0, 15, title, ln=True, align='C')
        
        self.set_font(self.font_set, '', 11)
        biz = unicodedata.normalize('NFC', f"업체명: {self.biz_name}")
        self.cell(0, 8, biz, ln=False, align='L')
        self.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='R')
        self.line(10, 38, 287, 38)
        self.ln(5)

    def draw_table(self, df):
        self.set_font(self.font_set, '', 9)
        if len(df.columns) == 0: return
        col_width = 277 / len(df.columns)
        
        # 헤더 디자인
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        for col in df.columns:
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(col_width, 10, txt, border=1, align='C', fill=True)
        self.ln()
        
        # 데이터 디자인
        self.set_text_color(0, 0, 0)
        fill = False
        for _, row in df.iterrows():
            for val in row:
                align = 'R' if isinstance(val, (int, float)) else 'C'
                display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                txt = unicodedata.normalize('NFC', display_val)
                self.cell(col_width, 8, txt, border=1, align=align, fill=fill)
            self.ln()
            fill = not fill

# --- [1. 세션 상태 및 설정 초기화] ---
if 'config' not in st.session_state:
    st.session_state.config = {
        "menu_0": "🏠 Home", 
        "menu_1": "⚖️ 마감작업", 
        "menu_2": "📁 매출매입장 PDF 변환", # 메뉴 신설
        "menu_3": "💳 카드매입 수기입력건",
        "sub_menu1": "국세청 PDF를 업로드하고 안내문을 작성하는 공간입니다.",
        "sub_menu2": "엑셀을 업로드하면 매출장/매입장 PDF로 변환합니다.",
        "prompt_template": """*{업체명} 부가세 신고현황☆★{결과}
감기 조심하시고 건강이 최고인거 아시죠? ^.<

부가세 신고 마무리되어 전체 자료 전달드립니다.

=첨부파일=
-부가세 신고서
-매출장: {매출액}원
-매입장: {매입액}원
-접수증 > {결과}: {세액}원

☆★{결과}예정 8월 말 정도

혹 확인 중에 변동사항이 있거나 궁금증이 생기시면 꼭 연락주세요!
25일 까지는 수정이 가능합니다!"""
    }

if 'daily_memo' not in st.session_state: st.session_state.daily_memo = ""
if 'selected_menu' not in st.session_state: st.session_state.selected_menu = st.session_state.config["menu_0"]

# 원본 링크 데이터 유지
if 'link_group_2' not in st.session_state:
    st.session_state.link_group_2 = [
        {"name": "📊 신고리스트", "url": "https://docs.google.com/spreadsheets/d/1VwvR2dk7TwymlemzDIOZdp9O13UYzuQr/edit?rtpof=true&sd=true"},
        {"name": "📁 상반기 자료", "url": "https://drive.google.com/drive/folders/1cDv6p6h5z3_4KNF-TZ5c7QfGzVvh4JV3"},
        {"name": "📁 하반기 자료", "url": "https://drive.google.com/drive/folders/1OL84Uh64hAe-lnlK0ZV4b6r6hWa2Qz-r0"},
        {"name": "💳 카드매입자료", "url": "https://drive.google.com/drive/folders/1k5kbUeFPvbtfqPlM61GM5PHhOy7s0JHe"}
    ]

# 원본 단축키 데이터 25개 보존
if 'account_data' not in st.session_state:
    st.session_state.account_data = [{"단축키": "822", "거래처": "유류대", "계정명": "차량유지비", "분류": "공제유무확인후 분류"}, {"단축키": "812", "거래처": "편의점", "계정명": "여비교통비", "분류": "공제유무확인후 분류"}, {"단축키": "830", "거래처": "다이소", "계정명": "소모품비", "분류": "매입"}, {"단축키": "811", "거래처": "식당", "계정명": "복리후생비", "분류": "공제유무확인후 분류"}, {"단축키": "146", "거래처": "거래처", "계정명": "상품", "분류": "매입"}, {"단축키": "830", "거래처": "홈쇼핑, 인터넷구매", "계정명": "소모품비", "분류": "매입"}, {"단축키": "822", "거래처": "주차장, 적은금액세금", "계정명": "차량유지비", "분류": "일반"}, {"단축키": "-", "거래처": "휴게소", "계정명": "차량/여비교통비", "분류": "공제유무확인후 분류"}, {"단축키": "-", "거래처": "전기요금", "계정명": "전력비", "분류": "매입"}, {"단축키": "-", "거래처": "수도요금", "계정명": "수도광열비", "분류": "일반"}, {"단축키": "814", "거래처": "통신비", "계정명": "통신비", "분류": "매입"}, {"단축키": "-", "거래처": "금융결제원", "계정명": "세금과공과", "분류": "일반"}, {"단축키": "830", "거래처": "약국", "계정명": "소모품비", "분류": "일반"}, {"단축키": "-", "거래처": "모텔", "계정명": "출장비/여비교통비", "분류": "일반"}, {"단축키": "831", "거래처": "캡스, 보안, 홈페이지", "계정명": "지급수수료", "분류": "매입"}, {"단축키": "-", "거래처": "아울렛(작업복)", "계정명": "소모품비", "분류": "매입"}, {"단축키": "820", "거래처": "컴퓨터 AS", "계정명": "수선비", "분류": "매입"}, {"단축키": "830", "거래처": "결제대행업체", "계정명": "소모품비", "분류": "일반"}, {"단축키": "-", "거래처": "신용카드 알림", "계정명": "지급수수료", "분류": "일반
