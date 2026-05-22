import streamlit as st
import pandas as pd

@st.cache_data
def load_ecommerce():
    df = pd.read_csv('data/ecommerce_sales_data.csv', index_col=0)
    df['City'] = df['City'].str.strip()
    return df

df = load_ecommerce().copy()
st.title("🛒 이커머스 매출 대시보드")

with st.sidebar:
    st.header("필터")
    if st.button("필터 초기화"):
        st.session_state['categories'] = df['Product Category'].unique().tolist()
        st.session_state['month_range'] = (1, 12)

    categories = st.multiselect(
        "카테고리",
        df['Product Category'].unique().tolist(),
        default=st.session_state.get('categories', df['Product Category'].unique().tolist()),
        key='categories'
    )
    month_range = st.slider("월 범위", 1, 12, (1, 12), key='month_range')

filtered = df[
    df['Product Category'].isin(categories) &
    df['Month'].between(month_range[0], month_range[1])
]

col1, col2 = st.columns(2)
col1.metric("총 주문 수", f"{len(filtered):,}")
col2.metric("총 매출", f"${filtered['Sales'].sum():,.0f}")

import plotly.express as px
fig = px.bar(
    filtered.groupby('Product Category')['Sales'].sum().reset_index(),
    x='Product Category', y='Sales',
    title='카테고리별 총 매출'
)
st.plotly_chart(fig)