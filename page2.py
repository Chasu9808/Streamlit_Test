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

# =========================
# 추가 분석 영역
# =========================

st.divider()
st.subheader("📌 추가 분석 자료")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "데이터 미리보기",
        "도시별 분석",
        "월별 매출 분석",
        "고객/결제 분석",
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
# TAB 2. 도시별 분석
# =========================
with tab2:
    st.write("도시별 주문 수와 매출을 확인합니다.")

    city_summary = (
        filtered
        .groupby("City")
        .agg(
            주문수=("Sales", "count"),
            총매출=("Sales", "sum"),
            평균매출=("Sales", "mean")
        )
        .reset_index()
        .sort_values("총매출", ascending=False)
    )

    st.dataframe(city_summary, use_container_width=True)

    fig_city_sales = px.bar(
        city_summary,
        x="City",
        y="총매출",
        title="도시별 총 매출",
        text_auto=".2s"
    )

    st.plotly_chart(fig_city_sales, use_container_width=True)

    fig_city_orders = px.bar(
        city_summary,
        x="City",
        y="주문수",
        title="도시별 주문 수",
        text_auto=True
    )

    st.plotly_chart(fig_city_orders, use_container_width=True)


# =========================
# TAB 3. 월별 매출 분석
# =========================
with tab3:
    st.write("월별 주문 수와 매출 흐름을 확인합니다.")

    monthly_summary = (
        filtered
        .groupby("Month")
        .agg(
            주문수=("Sales", "count"),
            총매출=("Sales", "sum"),
            평균매출=("Sales", "mean")
        )
        .reset_index()
        .sort_values("Month")
    )

    st.dataframe(monthly_summary, use_container_width=True)

    fig_month_sales = px.line(
        monthly_summary,
        x="Month",
        y="총매출",
        markers=True,
        title="월별 총 매출 추이"
    )

    st.plotly_chart(fig_month_sales, use_container_width=True)

    fig_month_orders = px.bar(
        monthly_summary,
        x="Month",
        y="주문수",
        title="월별 주문 수",
        text_auto=True
    )

    st.plotly_chart(fig_month_orders, use_container_width=True)


# =========================
# TAB 4. 고객/결제 분석
# =========================
with tab4:
    st.write("성별, 결제 방식, 배송 방식 등 고객/주문 특성을 확인합니다.")

    # 성별 분석
    if "Gender" in filtered.columns:
        gender_summary = (
            filtered
            .groupby("Gender")
            .agg(
                주문수=("Sales", "count"),
                총매출=("Sales", "sum"),
                평균매출=("Sales", "mean")
            )
            .reset_index()
        )

        st.write("성별 매출 분석")
        st.dataframe(gender_summary, use_container_width=True)

        fig_gender = px.pie(
            gender_summary,
            names="Gender",
            values="총매출",
            title="성별 총 매출 비중"
        )

        st.plotly_chart(fig_gender, use_container_width=True)

    # 결제 방식 분석
    if "Payment Method" in filtered.columns:
        payment_summary = (
            filtered
            .groupby("Payment Method")
            .agg(
                주문수=("Sales", "count"),
                총매출=("Sales", "sum"),
                평균매출=("Sales", "mean")
            )
            .reset_index()
            .sort_values("총매출", ascending=False)
        )

        st.write("결제 방식별 매출 분석")
        st.dataframe(payment_summary, use_container_width=True)

        fig_payment = px.bar(
            payment_summary,
            x="Payment Method",
            y="총매출",
            title="결제 방식별 총 매출",
            text_auto=".2s"
        )

        st.plotly_chart(fig_payment, use_container_width=True)

    # 배송 방식 분석
    if "Shipping Type" in filtered.columns:
        shipping_summary = (
            filtered
            .groupby("Shipping Type")
            .agg(
                주문수=("Sales", "count"),
                총매출=("Sales", "sum"),
                평균매출=("Sales", "mean")
            )
            .reset_index()
            .sort_values("총매출", ascending=False)
        )

        st.write("배송 방식별 매출 분석")
        st.dataframe(shipping_summary, use_container_width=True)

        fig_shipping = px.bar(
            shipping_summary,
            x="Shipping Type",
            y="총매출",
            title="배송 방식별 총 매출",
            text_auto=".2s"
        )

        st.plotly_chart(fig_shipping, use_container_width=True)

    if (
        "Gender" not in filtered.columns
        and "Payment Method" not in filtered.columns
        and "Shipping Type" not in filtered.columns
    ):
        st.warning("고객/결제 분석에 사용할 수 있는 컬럼이 없습니다.")


# =========================
# TAB 5. 다운로드
# =========================
with tab5:
    st.write("현재 필터가 적용된 데이터를 CSV 파일로 다운로드할 수 있습니다.")

    csv_data = filtered.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="필터 적용 데이터 다운로드",
        data=csv_data,
        file_name="filtered_ecommerce_data.csv",
        mime="text/csv"
    )

    st.write("다운로드 대상 데이터 미리보기")
    st.dataframe(filtered.head(20), use_container_width=True)