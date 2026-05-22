import streamlit as st
import pandas as pd

@st.cache_data
def load_marketing():
    df = pd.read_csv('data/marketing_campaign_dataset.csv')
    df['Acquisition_Cost'] = (
        df['Acquisition_Cost']
        .str.replace('[$,]', '', regex=True)
        .astype(float)
    )
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_marketing().copy()
st.title("📣 마케팅 캠페인 대시보드")
st.write(f"전체 데이터: {len(df):,}행")


with st.sidebar:
    st.header("필터")
    if st.button("필터 초기화"):
        st.session_state['campaign_types'] = df['Campaign_Type'].unique().tolist()
        st.session_state['location'] = "전체"

    campaign_types = st.multiselect(
        "캠페인 유형",
        df['Campaign_Type'].unique().tolist(),
        default=st.session_state.get('campaign_types', df['Campaign_Type'].unique().tolist()),
        key='campaign_types'
    )
    location = st.selectbox(
        "지역",
        ["전체"] + sorted(df['Location'].unique().tolist()),
        key='location'
    )

filtered = df[df['Campaign_Type'].isin(campaign_types)]
if location != "전체":
    filtered = filtered[filtered['Location'] == location]

col1, col2, col3 = st.columns(3)
col1.metric("총 캠페인 수", f"{len(filtered):,}")
col2.metric("평균 ROI", f"{filtered['ROI'].mean():.2f}")
col3.metric("평균 전환율", f"{filtered['Conversion_Rate'].mean():.1%}")

import plotly.express as px

fig = px.bar(
    filtered.groupby('Campaign_Type')['ROI'].mean().reset_index(),
    x='Campaign_Type', y='ROI',
    title='캠페인 유형별 평균 ROI'
)
st.plotly_chart(fig)