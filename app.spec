import streamlit as st
import pandas as pd
import io
from datetime import datetime
from fpdf import FPDF
import unicodedata

# --- [PDF 클래스: 한글 최적화] ---
class SimplePDF(FPDF):
    def __init__(self, title, biz):
        super().__init__(orientation='L')
        self.title_text = title
        self.biz_name = biz
        try:
            # 루트 폴더의 malgun.ttf 사용
            self.add_font('Malgun', '', 'malgun.ttf', unicode=True)
            self.font_set = 'Malgun'
        except:
            self.font_set = 'Arial'

    def header(self):
        self.set_font(self.font_set, '', 20)
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
        self.set_fill_color(50, 50, 50); self.set_text_color(255, 255, 255)
        for col in df.columns:
            txt = unicodedata.normalize('NFC', str(col))
            self.cell(col_width, 10, txt, border=1, align='C', fill=True)
        self.ln()
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

# --- [1. 세션 상태 및 설정 강제 업데이트] ---
# 메뉴 구성을 4개로 확실히 정의합니다.
menu_defs = {
    "m0": "🏠 Home",
    "m1": "⚖️ 마감작업",
    "m2": "📁 매출매입장 PDF 변환",
    "m
