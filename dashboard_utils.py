# dashboard_utils.py
import io

import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError


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


def render_analysis_dashboard(df, title="데이터 분석 대시보드"):
    """
    공통 분석 대시보드 함수.
    마케팅, 이커머스, 새 데이터 분석 페이지에서 모두 사용한다.
    """

    st.title(title)

    if df is None:
        st.warning("분석할 데이터가 없습니다.")
        return

    if df.empty:
        st.warning("데이터가 비어 있습니다.")
        return

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
        default=df.columns.tolist()[:5]
    )

    if len(selected_columns) == 0:
        st.warning("분석할 컬럼을 최소 1개 이상 선택해주세요.")
        return

    selected_df = df[selected_columns].copy()

    st.info(f"현재 선택된 분석 항목: {', '.join(selected_columns)}")

    # =========================
    # 조건 필터
    # =========================
    st.subheader("조건 필터")

    filtered_df = selected_df.copy()

    filter_columns = st.multiselect(
        "필터를 적용할 컬럼을 선택하세요",
        options=selected_df.columns.tolist()
    )

    if len(filter_columns) > 0:
        for filter_col in filter_columns:
            unique_values = selected_df[filter_col].dropna().astype(str).unique().tolist()
            unique_values = unique_values[:50]

            selected_values = st.multiselect(
                f"{filter_col} 컬럼에서 포함할 값을 선택하세요. 최대 50개 값만 표시됩니다.",
                options=unique_values,
                key=f"{title}_{filter_col}"
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
        return

    if len(filtered_df) == 0:
        st.warning("필터 적용 후 남은 데이터가 없습니다.")
        return

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