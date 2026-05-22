# app.py
import streamlit as st

st.set_page_config(
    page_title="CSV 분석 대시보드",
    page_icon="📊",
    layout="wide"
)

market = st.Page("page1.py", title="마케팅", icon="📊")
ecommerce = st.Page("page2.py", title="이커머스", icon="🛒")
custom = st.Page("page3.py", title="새 데이터 분석", icon="📁")

pg = st.navigation([market, ecommerce, custom])

pg.run()