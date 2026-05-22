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

# =========================
# 추가 분석 영역
# =========================

st.divider()
st.subheader("📌 추가 분석 자료")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "데이터 미리보기",
        "채널별 분석",
        "지역별 분석",
        "비용 대비 성과",
        "다운로드"
    ]
)

# =========================
# TAB 1. 데이터 미리보기
# =========================
with tab1:
    st.write("현재 필터가 적용된 데이터입니다.")
    st.dataframe(filtered.head(30), use_container_width=True)

    st.write("필터 적용 후 데이터 크기")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("행 개수", f"{len(filtered):,}")

    with col2:
        st.metric("컬럼 개수", f"{len(filtered.columns):,}")

    with col3:
        st.metric("결측치 개수", f"{filtered.isnull().sum().sum():,}")

    st.write("기초 통계")
    st.dataframe(filtered.describe(include="all"), use_container_width=True)


# =========================
# TAB 2. 채널별 분석
# =========================
with tab2:
    st.write("마케팅 채널별 성과를 확인합니다.")

    channel_summary = (
        filtered
        .groupby("Channel_Used")
        .agg(
            캠페인수=("Campaign_ID", "count"),
            평균_ROI=("ROI", "mean"),
            평균_전환율=("Conversion_Rate", "mean"),
            평균_획득비용=("Acquisition_Cost", "mean"),
            총_클릭수=("Clicks", "sum"),
            총_노출수=("Impressions", "sum")
        )
        .reset_index()
    )

    st.dataframe(channel_summary, use_container_width=True)

    fig_channel_roi = px.bar(
        channel_summary,
        x="Channel_Used",
        y="평균_ROI",
        title="채널별 평균 ROI",
        text_auto=".2f"
    )

    st.plotly_chart(fig_channel_roi, use_container_width=True)

    fig_channel_conversion = px.bar(
        channel_summary,
        x="Channel_Used",
        y="평균_전환율",
        title="채널별 평균 전환율",
        text_auto=".2%"
    )

    st.plotly_chart(fig_channel_conversion, use_container_width=True)


# =========================
# TAB 3. 지역별 분석
# =========================
with tab3:
    st.write("지역별 캠페인 성과를 확인합니다.")

    location_summary = (
        filtered
        .groupby("Location")
        .agg(
            캠페인수=("Campaign_ID", "count"),
            평균_ROI=("ROI", "mean"),
            평균_전환율=("Conversion_Rate", "mean"),
            평균_획득비용=("Acquisition_Cost", "mean")
        )
        .reset_index()
        .sort_values("평균_ROI", ascending=False)
    )

    st.dataframe(location_summary, use_container_width=True)

    fig_location = px.bar(
        location_summary,
        x="Location",
        y="평균_ROI",
        title="지역별 평균 ROI",
        text_auto=".2f"
    )

    st.plotly_chart(fig_location, use_container_width=True)


# =========================
# TAB 4. 비용 대비 성과 분석
# =========================
with tab4:
    st.write("광고 획득 비용과 ROI의 관계를 확인합니다.")

    fig_scatter = px.scatter(
        filtered,
        x="Acquisition_Cost",
        y="ROI",
        color="Campaign_Type",
        size="Conversion_Rate",
        hover_data=["Company", "Channel_Used", "Location"],
        title="획득 비용 대비 ROI"
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

    st.write("월별 평균 ROI 추이")

    monthly_roi = (
        filtered
        .assign(YearMonth=filtered["Date"].dt.to_period("M").astype(str))
        .groupby("YearMonth")["ROI"]
        .mean()
        .reset_index()
    )

    fig_monthly = px.line(
        monthly_roi,
        x="YearMonth",
        y="ROI",
        markers=True,
        title="월별 평균 ROI 추이"
    )

    st.plotly_chart(fig_monthly, use_container_width=True)


# =========================
# TAB 5. 다운로드
# =========================
with tab5:
    st.write("현재 필터가 적용된 데이터를 CSV 파일로 다운로드할 수 있습니다.")

    csv_data = filtered.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="필터 적용 데이터 다운로드",
        data=csv_data,
        file_name="filtered_marketing_data.csv",
        mime="text/csv"
    )

    st.write("다운로드 대상 데이터 미리보기")
    st.dataframe(filtered.head(20), use_container_width=True)

