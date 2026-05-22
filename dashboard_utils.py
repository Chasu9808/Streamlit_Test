# dashboard_utils.py
import io
import html

import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError


# =========================================================
# CSV 읽기 / 다운로드 공통 함수
# =========================================================

@st.cache_data
def read_csv_from_path(file_path):
    """
    로컬 CSV 파일을 읽는 함수.
    마케팅/이커머스처럼 기본으로 제공되는 CSV 파일을 읽을 때 사용한다.
    """

    try:
        return pd.read_csv(file_path)
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding="cp949")


@st.cache_data
def read_csv_from_upload(file_bytes):
    """
    사용자가 업로드한 CSV 파일을 읽는 함수.
    Streamlit uploaded_file 객체를 직접 읽지 않고 bytes로 읽는다.
    """

    if len(file_bytes) == 0:
        raise EmptyDataError("업로드한 CSV 파일이 비어 있습니다.")

    try:
        return pd.read_csv(io.BytesIO(file_bytes))
    except UnicodeDecodeError:
        return pd.read_csv(io.BytesIO(file_bytes), encoding="cp949")


@st.cache_data
def convert_df_to_csv_bytes(df):
    """
    DataFrame을 다운로드 가능한 CSV bytes로 변환한다.
    utf-8-sig를 사용하면 엑셀에서 한글 깨짐 가능성이 줄어든다.
    """

    return df.to_csv(index=False).encode("utf-8-sig")


# =========================================================
# page3 등에서 사용할 공통 분석 대시보드
# =========================================================

def render_analysis_dashboard(df, title="데이터 분석 대시보드"):
    """
    공통 분석 대시보드 함수.
    새 데이터 업로드 페이지 등에서 사용한다.

    흐름:
    1. 원본 데이터 미리보기
    2. 분석 컬럼 선택
    3. 조건 필터
    4. 분석 실행 버튼
    5. 탭별 분석
    """

    st.title(title)

    if df is None:
        st.warning("분석할 데이터가 없습니다.")
        return None

    if df.empty:
        st.warning("데이터가 비어 있습니다.")
        return None

    st.success("데이터 로드 완료")
    st.write(f"전체 데이터 크기: {len(df):,}행 / {len(df.columns):,}개 컬럼")

    if len(df) > 100000:
        st.warning("데이터 행 수가 많습니다. 분석할 컬럼을 적게 선택하는 것을 권장합니다.")

    # =========================
    # 원본 데이터 미리보기
    # =========================
    st.subheader("원본 데이터 미리보기")
    st.dataframe(df.head(20), use_container_width=True)

    # =========================
    # 분석 컬럼 선택
    # =========================
    st.subheader("분석할 항목 선택")

    selected_columns = st.multiselect(
        "분석에 사용할 컬럼을 선택하세요",
        options=df.columns.tolist(),
        default=df.columns.tolist()[:5],
        key=f"{title}_selected_columns"
    )

    if len(selected_columns) == 0:
        st.warning("분석할 컬럼을 최소 1개 이상 선택해주세요.")
        return None

    selected_df = df[selected_columns].copy()

    st.info(f"현재 선택된 분석 항목: {', '.join(selected_columns)}")

    # =========================
    # 조건 필터
    # =========================
    st.subheader("조건 필터")

    filtered_df = selected_df.copy()

    filter_columns = st.multiselect(
        "필터를 적용할 컬럼을 선택하세요",
        options=selected_df.columns.tolist(),
        key=f"{title}_filter_columns"
    )

    if len(filter_columns) > 0:
        for filter_col in filter_columns:
            unique_values = selected_df[filter_col].dropna().astype(str).unique().tolist()
            unique_values = unique_values[:50]

            selected_values = st.multiselect(
                f"{filter_col} 컬럼에서 포함할 값을 선택하세요. 최대 50개 값만 표시됩니다.",
                options=unique_values,
                key=f"{title}_{filter_col}_filter_values"
            )

            if len(selected_values) > 0:
                filtered_df = filtered_df[
                    filtered_df[filter_col].astype(str).isin(selected_values)
                ]

    st.write(f"필터 적용 후 데이터 크기: {len(filtered_df):,}행 / {len(filtered_df.columns):,}개 컬럼")
    st.dataframe(filtered_df.head(20), use_container_width=True)

    run_analysis = st.button("분석 실행", key=f"{title}_run_analysis")

    if not run_analysis:
        st.info("분석을 시작하려면 '분석 실행' 버튼을 눌러주세요.")
        return filtered_df

    if len(filtered_df) == 0:
        st.warning("필터 적용 후 남은 데이터가 없습니다.")
        return filtered_df

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "데이터 품질 요약",
            "기초 통계",
            "결측치 분석",
            "범주형 분석",
            "숫자형 차트",
            "상관관계 분석",
            "다운로드 / 검색"
        ]
    )

    # =========================
    # TAB 1. 데이터 품질 요약
    # =========================
    with tab1:
        st.subheader("데이터 품질 요약")

        total_rows = len(filtered_df)
        total_columns = len(filtered_df.columns)
        duplicate_rows = filtered_df.duplicated().sum()
        total_missing = filtered_df.isnull().sum().sum()

        numeric_columns = filtered_df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        object_columns = filtered_df.select_dtypes(include=["object"]).columns.tolist()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("행 개수", f"{total_rows:,}")

        with col2:
            st.metric("컬럼 개수", f"{total_columns:,}")

        with col3:
            st.metric("중복 행 개수", f"{duplicate_rows:,}")

        with col4:
            st.metric("전체 결측치 개수", f"{total_missing:,}")

        type_summary_df = pd.DataFrame({
            "컬럼명": filtered_df.columns,
            "데이터 타입": filtered_df.dtypes.astype(str).values,
            "고유값 개수": filtered_df.nunique(dropna=True).values,
            "결측치 개수": filtered_df.isnull().sum().values,
            "결측치 비율(%)": (filtered_df.isnull().mean().values * 100).round(2)
        })

        st.dataframe(type_summary_df, use_container_width=True)

        st.write("숫자형 컬럼")
        st.write(numeric_columns if numeric_columns else "숫자형 컬럼이 없습니다.")

        st.write("문자형 컬럼")
        st.write(object_columns if object_columns else "문자형 컬럼이 없습니다.")

    # =========================
    # TAB 2. 기초 통계
    # =========================
    with tab2:
        st.subheader("기초 통계")

        numeric_columns = filtered_df.select_dtypes(include=["int64", "float64"]).columns.tolist()

        if len(numeric_columns) > 0:
            st.write("숫자형 통계")
            st.dataframe(
                filtered_df[numeric_columns].describe(),
                use_container_width=True
            )
        else:
            st.warning("숫자형 컬럼이 없습니다.")

        st.write("전체 컬럼 통계")
        st.dataframe(
            filtered_df.describe(include="all"),
            use_container_width=True
        )

    # =========================
    # TAB 3. 결측치 분석
    # =========================
    with tab3:
        st.subheader("결측치 분석")

        missing_df = pd.DataFrame({
            "컬럼명": filtered_df.columns,
            "결측치 개수": filtered_df.isnull().sum().values,
            "결측치 비율(%)": (filtered_df.isnull().mean().values * 100).round(2)
        })

        st.dataframe(missing_df, use_container_width=True)

        st.write("결측치 비율 차트")
        st.bar_chart(
            missing_df.set_index("컬럼명")["결측치 비율(%)"]
        )

    # =========================
    # TAB 4. 범주형 분석
    # =========================
    with tab4:
        st.subheader("범주형 분석")

        categorical_columns = filtered_df.select_dtypes(include=["object"]).columns.tolist()

        if len(categorical_columns) == 0:
            st.warning("범주형 컬럼이 없습니다.")
        else:
            selected_category_col = st.selectbox(
                "분석할 범주형 컬럼을 선택하세요",
                options=categorical_columns,
                key=f"{title}_category_col"
            )

            top_n = st.slider(
                "상위 몇 개 값까지 볼까요?",
                5,
                50,
                20,
                key=f"{title}_top_n"
            )

            value_count_df = (
                filtered_df[selected_category_col]
                .value_counts()
                .head(top_n)
                .reset_index()
            )

            value_count_df.columns = [selected_category_col, "개수"]

            st.dataframe(value_count_df, use_container_width=True)

            st.bar_chart(
                value_count_df.set_index(selected_category_col)["개수"]
            )

    # =========================
    # TAB 5. 숫자형 차트
    # =========================
    with tab5:
        st.subheader("숫자형 컬럼 차트")

        numeric_columns = filtered_df.select_dtypes(include=["int64", "float64"]).columns.tolist()

        if len(numeric_columns) == 0:
            st.warning("숫자형 컬럼이 없습니다.")
        else:
            chart_col = st.selectbox(
                "차트로 확인할 숫자형 컬럼을 선택하세요",
                options=numeric_columns,
                key=f"{title}_chart_col"
            )

            chart_data = filtered_df[[chart_col]].dropna().reset_index(drop=True)
            chart_data = chart_data.head(1000)

            st.write(f"{chart_col} 값 추이. 최대 1,000개 행만 표시합니다.")
            st.line_chart(chart_data)

    # =========================
    # TAB 6. 상관관계 분석
    # =========================
    with tab6:
        st.subheader("상관관계 분석")

        numeric_df = filtered_df.select_dtypes(include=["int64", "float64"])

        if numeric_df.shape[1] < 2:
            st.warning("상관관계 분석을 위해서는 숫자형 컬럼이 최소 2개 이상 필요합니다.")
        else:
            max_corr_columns = 20
            numeric_df = numeric_df.iloc[:, :max_corr_columns]

            corr_df = numeric_df.corr()

            st.write("상관관계 표")
            st.dataframe(corr_df, use_container_width=True)

            st.write("상관관계 차트")
            st.bar_chart(corr_df)

    # =========================
    # TAB 7. 다운로드 / 검색
    # =========================
    with tab7:
        st.subheader("CSV 다운로드")

        csv_data = convert_df_to_csv_bytes(filtered_df)

        st.download_button(
            label="필터링 결과 CSV 다운로드",
            data=csv_data,
            file_name="filtered_result.csv",
            mime="text/csv",
            key=f"{title}_download_filtered"
        )

        st.divider()

        st.subheader("키워드 검색")

        with st.form(f"{title}_search_form"):
            keyword = st.text_input("검색할 키워드를 입력하세요")
            submitted = st.form_submit_button("검색")

        if submitted:
            if keyword.strip() == "":
                st.warning("검색어를 입력해주세요.")
            else:
                search_result = filtered_df[
                    filtered_df.astype(str).apply(
                        lambda row: row.str.contains(keyword, case=False, na=False).any(),
                        axis=1
                    )
                ]

                st.write(f"검색 결과: {len(search_result):,}건")
                st.dataframe(search_result.head(500), use_container_width=True)

                search_csv_data = convert_df_to_csv_bytes(search_result)

                st.download_button(
                    label="검색 결과 CSV 다운로드",
                    data=search_csv_data,
                    file_name="search_result.csv",
                    mime="text/csv",
                    key=f"{title}_download_search"
                )

    return filtered_df


# =========================================================
# 자동 인사이트 카드 출력 함수
# =========================================================

def render_insight_card(title, summary_text, insight_items):
    """
    HTML을 사용하지 않고 Streamlit 기본 컴포넌트만으로
    하나의 박스 안에 자동 인사이트를 정리해서 보여주는 함수.

    HTML 태그가 화면에 그대로 출력되는 문제를 피하기 위해
    st.markdown(unsafe_allow_html=True)를 사용하지 않는다.
    """

    badge_map = {
        "good": {
            "icon": "✅",
            "text": "양호"
        },
        "warning": {
            "icon": "⚠️",
            "text": "확인"
        },
        "danger": {
            "icon": "🚨",
            "text": "주의"
        },
        "normal": {
            "icon": "ℹ️",
            "text": "요약"
        }
    }

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(summary_text)

        st.divider()

        for index, item in enumerate(insight_items):
            label = item.get("label", "")
            message = item.get("message", "")
            level = item.get("level", "normal")

            badge_info = badge_map.get(level, badge_map["normal"])

            badge_col, content_col = st.columns([1.2, 8.8])

            with badge_col:
                st.markdown(
                    f"**{badge_info['icon']} {badge_info['text']}**"
                )

            with content_col:
                st.markdown(f"**{label}**")
                st.write(message)

            if index < len(insight_items) - 1:
                st.divider()


# =========================================================
# 자동 인사이트 공통 내용 생성 함수
# =========================================================

def build_basic_insight_items(df):
    """
    마케팅/이커머스에서 공통으로 사용할 수 있는
    데이터 규모, 결측치, 중복 데이터 인사이트를 만든다.

    이 함수는 화면에 직접 출력하지 않고,
    render_insight_card()에 전달할 리스트만 반환한다.
    """

    insight_items = []

    if df is None or df.empty:
        insight_items.append({
            "label": "데이터 상태",
            "message": "현재 필터 기준으로 해석할 데이터가 없습니다.",
            "level": "warning"
        })
        return insight_items

    row_count = len(df)
    col_count = len(df.columns)

    missing_count = df.isnull().sum().sum()
    duplicate_count = df.duplicated().sum()

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    object_cols = df.select_dtypes(include=["object"]).columns.tolist()

    insight_items.append({
        "label": "데이터 규모",
        "message": (
            f"현재 필터 기준 데이터는 총 {row_count:,}행, {col_count:,}개 컬럼으로 구성되어 있습니다. "
            f"숫자형 컬럼은 {len(numeric_cols):,}개, 문자형 컬럼은 {len(object_cols):,}개입니다."
        ),
        "level": "normal"
    })

    if missing_count > 0:
        insight_items.append({
            "label": "결측치 확인 필요",
            "message": (
                f"결측치가 총 {missing_count:,}개 발견되었습니다. "
                "결측치가 많은 컬럼은 평균, 합계, 비율 계산 결과에 영향을 줄 수 있습니다."
            ),
            "level": "warning"
        })
    else:
        insight_items.append({
            "label": "결측치 상태",
            "message": "현재 필터 기준 데이터에는 결측치가 없습니다.",
            "level": "good"
        })

    if duplicate_count > 0:
        insight_items.append({
            "label": "중복 데이터 확인 필요",
            "message": (
                f"중복 행이 {duplicate_count:,}개 발견되었습니다. "
                "동일한 거래 또는 캠페인이 반복 기록된 것인지 확인하는 것이 좋습니다."
            ),
            "level": "warning"
        })
    else:
        insight_items.append({
            "label": "중복 데이터 상태",
            "message": "현재 필터 기준 데이터에는 중복 행이 없습니다.",
            "level": "good"
        })

    return insight_items


# =========================================================
# 마케팅 자동 인사이트
# =========================================================

def render_marketing_insight(filtered):
    """
    마케팅 데이터 전용 자동 인사이트.

    필요한 주요 컬럼:
        Campaign_Type
        Channel_Used
        ROI
        Conversion_Rate
        Acquisition_Cost
    """

    if filtered is None or filtered.empty:
        render_insight_card(
            title="🤖 마케팅 자동 인사이트",
            summary_text="현재 필터 기준으로 해석할 마케팅 데이터가 없습니다.",
            insight_items=[
                {
                    "label": "데이터 없음",
                    "message": "필터 조건을 조정하거나 전체 데이터를 다시 확인해주세요.",
                    "level": "warning"
                }
            ]
        )
        return

    insight_items = build_basic_insight_items(filtered)

    required_cols = [
        "Campaign_Type",
        "Channel_Used",
        "ROI",
        "Conversion_Rate",
        "Acquisition_Cost"
    ]

    missing_cols = [
        col for col in required_cols
        if col not in filtered.columns
    ]

    if len(missing_cols) > 0:
        insight_items.append({
            "label": "필수 컬럼 부족",
            "message": f"마케팅 자동 해석에 필요한 컬럼이 부족합니다: {missing_cols}",
            "level": "danger"
        })

        render_insight_card(
            title="🤖 마케팅 자동 인사이트",
            summary_text="마케팅 데이터 구조를 기준으로 자동 해석을 시도했지만, 일부 필수 컬럼이 부족합니다.",
            insight_items=insight_items
        )
        return

    # =========================
    # 캠페인 유형별 ROI
    # =========================
    campaign_roi = (
        filtered
        .groupby("Campaign_Type")["ROI"]
        .mean()
        .sort_values(ascending=False)
    )

    if not campaign_roi.empty:
        best_campaign_type = campaign_roi.index[0]
        best_campaign_roi = campaign_roi.iloc[0]

        worst_campaign_type = campaign_roi.index[-1]
        worst_campaign_roi = campaign_roi.iloc[-1]

        insight_items.append({
            "label": "ROI 우수 캠페인 유형",
            "message": (
                f"평균 ROI가 가장 높은 캠페인 유형은 '{best_campaign_type}'이며, "
                f"평균 ROI는 {best_campaign_roi:.2f}입니다."
            ),
            "level": "good"
        })

        insight_items.append({
            "label": "ROI 낮은 캠페인 유형",
            "message": (
                f"평균 ROI가 가장 낮은 캠페인 유형은 '{worst_campaign_type}'이며, "
                f"평균 ROI는 {worst_campaign_roi:.2f}입니다."
            ),
            "level": "warning"
        })

    # =========================
    # 채널별 전환율
    # =========================
    channel_conversion = (
        filtered
        .groupby("Channel_Used")["Conversion_Rate"]
        .mean()
        .sort_values(ascending=False)
    )

    if not channel_conversion.empty:
        best_channel = channel_conversion.index[0]
        best_conversion = channel_conversion.iloc[0]

        insight_items.append({
            "label": "전환율 우수 채널",
            "message": (
                f"평균 전환율이 가장 높은 채널은 '{best_channel}'이며, "
                f"평균 전환율은 {best_conversion:.2%}입니다."
            ),
            "level": "normal"
        })

    # =========================
    # 채널별 획득 비용
    # =========================
    cost_by_channel = (
        filtered
        .groupby("Channel_Used")["Acquisition_Cost"]
        .mean()
        .sort_values(ascending=False)
    )

    if not cost_by_channel.empty:
        high_cost_channel = cost_by_channel.index[0]
        high_cost_value = cost_by_channel.iloc[0]

        low_cost_channel = cost_by_channel.index[-1]
        low_cost_value = cost_by_channel.iloc[-1]

        insight_items.append({
            "label": "획득 비용 비교",
            "message": (
                f"평균 획득 비용이 가장 높은 채널은 '{high_cost_channel}'이며 평균 비용은 ${high_cost_value:,.0f}입니다. "
                f"가장 낮은 채널은 '{low_cost_channel}'이며 평균 비용은 ${low_cost_value:,.0f}입니다."
            ),
            "level": "normal"
        })

    # =========================
    # ROI 이상치 후보
    # =========================
    q1 = filtered["ROI"].quantile(0.25)
    q3 = filtered["ROI"].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr

    outlier_df = filtered[filtered["ROI"] > upper_bound]

    if outlier_df.empty:
        insight_items.append({
            "label": "ROI 이상치",
            "message": "현재 필터 기준으로 ROI가 일반 범위보다 과도하게 높은 이상치 후보는 발견되지 않았습니다.",
            "level": "good"
        })
    else:
        insight_items.append({
            "label": "ROI 이상치 후보",
            "message": (
                f"ROI가 일반 범위보다 높은 캠페인이 {len(outlier_df):,}건 발견되었습니다. "
                "성과가 매우 좋은 캠페인인지, 데이터 입력 오류인지 확인해볼 수 있습니다."
            ),
            "level": "warning"
        })

    # =========================
    # 하나의 카드로 출력
    # =========================
    render_insight_card(
        title="🤖 마케팅 자동 인사이트",
        summary_text="현재 적용된 필터 조건을 기준으로 캠페인 성과, 전환율, 획득 비용, 데이터 품질을 요약했습니다.",
        insight_items=insight_items
    )

    # 상세 데이터는 기본 노출하지 않고 접어두기
    with st.expander("ROI 상위 캠페인 TOP 5 보기"):
        display_cols = [
            col for col in [
                "Campaign_ID",
                "Company",
                "Campaign_Type",
                "Channel_Used",
                "Location",
                "ROI",
                "Conversion_Rate",
                "Acquisition_Cost"
            ]
            if col in filtered.columns
        ]

        top_roi_df = (
            filtered
            .sort_values("ROI", ascending=False)
            .head(5)
        )

        st.dataframe(
            top_roi_df[display_cols],
            use_container_width=True
        )


# =========================================================
# 이커머스 자동 인사이트
# =========================================================

def render_ecommerce_insight(filtered):
    """
    이커머스 데이터 전용 자동 인사이트.

    필요한 주요 컬럼:
        Product Category
        City
        Month
        Sales
    """

    if filtered is None or filtered.empty:
        render_insight_card(
            title="🤖 이커머스 자동 인사이트",
            summary_text="현재 필터 기준으로 해석할 이커머스 데이터가 없습니다.",
            insight_items=[
                {
                    "label": "데이터 없음",
                    "message": "필터 조건을 조정하거나 전체 데이터를 다시 확인해주세요.",
                    "level": "warning"
                }
            ]
        )
        return

    insight_items = build_basic_insight_items(filtered)

    required_cols = [
        "Product Category",
        "City",
        "Month",
        "Sales"
    ]

    missing_cols = [
        col for col in required_cols
        if col not in filtered.columns
    ]

    if len(missing_cols) > 0:
        insight_items.append({
            "label": "필수 컬럼 부족",
            "message": f"이커머스 자동 해석에 필요한 컬럼이 부족합니다: {missing_cols}",
            "level": "danger"
        })

        render_insight_card(
            title="🤖 이커머스 자동 인사이트",
            summary_text="이커머스 데이터 구조를 기준으로 자동 해석을 시도했지만, 일부 필수 컬럼이 부족합니다.",
            insight_items=insight_items
        )
        return

    # =========================
    # 카테고리별 매출
    # =========================
    category_sales = (
        filtered
        .groupby("Product Category")["Sales"]
        .sum()
        .sort_values(ascending=False)
    )

    if not category_sales.empty:
        top_category = category_sales.index[0]
        top_category_sales = category_sales.iloc[0]

        bottom_category = category_sales.index[-1]
        bottom_category_sales = category_sales.iloc[-1]

        total_sales = filtered["Sales"].sum()
        top_category_ratio = top_category_sales / total_sales if total_sales != 0 else 0

        insight_items.append({
            "label": "매출 상위 카테고리",
            "message": (
                f"현재 필터 기준 매출이 가장 높은 카테고리는 '{top_category}'이며, "
                f"총 매출은 ${top_category_sales:,.0f}입니다. "
                f"전체 매출의 {top_category_ratio:.1%}를 차지합니다."
            ),
            "level": "good"
        })

        insight_items.append({
            "label": "매출 하위 카테고리",
            "message": (
                f"매출이 가장 낮은 카테고리는 '{bottom_category}'이며, "
                f"총 매출은 ${bottom_category_sales:,.0f}입니다."
            ),
            "level": "warning"
        })

    # =========================
    # 도시별 매출
    # =========================
    city_sales = (
        filtered
        .groupby("City")["Sales"]
        .sum()
        .sort_values(ascending=False)
    )

    if not city_sales.empty:
        top_city = city_sales.index[0]
        top_city_sales = city_sales.iloc[0]

        insight_items.append({
            "label": "매출 상위 도시",
            "message": (
                f"도시 기준으로는 '{top_city}'의 매출이 가장 높으며, "
                f"총 매출은 ${top_city_sales:,.0f}입니다."
            ),
            "level": "normal"
        })

    # =========================
    # 월별 매출
    # =========================
    monthly_sales = (
        filtered
        .groupby("Month")["Sales"]
        .sum()
        .sort_index()
    )

    if not monthly_sales.empty:
        best_month = monthly_sales.idxmax()
        best_month_sales = monthly_sales.max()

        insight_items.append({
            "label": "월별 최고 매출",
            "message": (
                f"월별 기준으로는 {best_month}월의 매출이 가장 높으며, "
                f"총 매출은 ${best_month_sales:,.0f}입니다."
            ),
            "level": "normal"
        })

        if len(monthly_sales) >= 2:
            first_month_sales = monthly_sales.iloc[0]
            last_month_sales = monthly_sales.iloc[-1]

            if first_month_sales != 0:
                growth_rate = (last_month_sales - first_month_sales) / first_month_sales

                if growth_rate > 0:
                    insight_items.append({
                        "label": "월 범위 매출 변화",
                        "message": (
                            f"선택된 월 범위에서 마지막 월 매출은 첫 월 대비 {growth_rate:.1%} 증가했습니다."
                        ),
                        "level": "good"
                    })
                elif growth_rate < 0:
                    insight_items.append({
                        "label": "월 범위 매출 변화",
                        "message": (
                            f"선택된 월 범위에서 마지막 월 매출은 첫 월 대비 {abs(growth_rate):.1%} 감소했습니다."
                        ),
                        "level": "warning"
                    })
                else:
                    insight_items.append({
                        "label": "월 범위 매출 변화",
                        "message": "선택된 월 범위에서 첫 월과 마지막 월의 매출은 동일합니다.",
                        "level": "normal"
                    })

    # =========================
    # 매출 이상치 후보
    # =========================
    q1 = filtered["Sales"].quantile(0.25)
    q3 = filtered["Sales"].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr

    outlier_df = filtered[filtered["Sales"] > upper_bound]

    if outlier_df.empty:
        insight_items.append({
            "label": "매출 이상치",
            "message": "현재 필터 기준으로 매출이 일반 범위보다 과도하게 높은 이상치 후보는 발견되지 않았습니다.",
            "level": "good"
        })
    else:
        insight_items.append({
            "label": "매출 이상치 후보",
            "message": (
                f"일반 범위보다 매출이 높은 주문이 {len(outlier_df):,}건 발견되었습니다. "
                "대량 구매, 특수 주문, 데이터 입력 오류 여부를 확인해볼 수 있습니다."
            ),
            "level": "warning"
        })

    # =========================
    # 하나의 카드로 출력
    # =========================
    render_insight_card(
        title="🤖 이커머스 자동 인사이트",
        summary_text="현재 적용된 필터 조건을 기준으로 매출, 카테고리, 도시, 월별 흐름, 데이터 품질을 요약했습니다.",
        insight_items=insight_items
    )

    # 상세 데이터는 기본 노출하지 않고 접어두기
    with st.expander("매출 상위 주문 TOP 5 보기"):
        display_cols = [
            col for col in [
                "Product Category",
                "City",
                "Month",
                "Sales",
                "Gender",
                "Payment Method",
                "Shipping Type"
            ]
            if col in filtered.columns
        ]

        top_sales_df = (
            filtered
            .sort_values("Sales", ascending=False)
            .head(5)
        )

        st.dataframe(
            top_sales_df[display_cols],
            use_container_width=True
        )