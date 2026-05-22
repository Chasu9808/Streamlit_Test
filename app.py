# app.py
import io

import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError

st.set_page_config(
    page_title="CSV 분석 대시보드",
    page_icon="📊",
    layout="wide"
)

# 멀티 페이지 설정
market = st.Page("page1.py", title="마케팅", icon="📊")
icomous = st.Page("page2.py", title="이커머스", icon="🔍")

pg = st.navigation([market, icomous])

st.title("CSV 분석 대시보드")

uploaded = st.file_uploader("내 데이터 업로드 (CSV)", type=["csv"])

user_df = None
selected_df = None

if uploaded is not None:
    try:
        file_bytes = uploaded.getvalue()

        if len(file_bytes) == 0:
            st.error("업로드한 CSV 파일이 비어 있습니다.")
        else:
            # Streamlit 업로드 객체를 직접 읽지 않고 BytesIO로 안정적으로 읽기
            user_df = pd.read_csv(io.BytesIO(file_bytes))

            st.success(f"{uploaded.name} 파일 업로드 완료")
            st.write(f"전체 데이터 크기: {len(user_df):,}행 / {len(user_df.columns):,}개 컬럼")

            # =========================
            # 1. 분석할 컬럼 선택
            # =========================
            st.subheader("분석할 항목 선택")

            selected_columns = st.multiselect(
                "분석에 사용할 컬럼을 선택하세요",
                options=user_df.columns.tolist(),
                default=user_df.columns.tolist()[:5]
            )

            if len(selected_columns) == 0:
                st.warning("분석할 컬럼을 최소 1개 이상 선택해주세요.")
            else:
                selected_df = user_df[selected_columns]

                st.info(f"현재 선택된 분석 항목: {', '.join(selected_columns)}")

                # =========================
                # 2. 탭 생성
                # =========================
                tab1, tab2, tab3, tab4, tab5 = st.tabs(
                    [
                        "데이터 미리보기",
                        "기초 통계",
                        "결측치 분석",
                        "범주형 분석",
                        "키워드 검색"
                    ]
                )

                # =========================
                # TAB 1. 데이터 미리보기
                # =========================
                with tab1:
                    st.subheader("선택한 항목 데이터 미리보기")

                    st.write("선택한 컬럼만 표시합니다.")
                    st.dataframe(selected_df.head(20), use_container_width=True)

                    st.write("선택한 데이터 크기")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("행 개수", f"{len(selected_df):,}")

                    with col2:
                        st.metric("선택 컬럼 수", f"{len(selected_df.columns):,}")

                # =========================
                # TAB 2. 기초 통계
                # =========================
                with tab2:
                    st.subheader("선택한 항목의 기초 통계")

                    numeric_columns = selected_df.select_dtypes(include=["int64", "float64"]).columns.tolist()
                    object_columns = selected_df.select_dtypes(include=["object"]).columns.tolist()

                    st.write("숫자형 컬럼")
                    st.write(numeric_columns if numeric_columns else "선택한 항목 중 숫자형 컬럼이 없습니다.")

                    st.write("문자형 컬럼")
                    st.write(object_columns if object_columns else "선택한 항목 중 문자형 컬럼이 없습니다.")

                    if len(numeric_columns) > 0:
                        st.write("숫자형 통계")
                        st.dataframe(
                            selected_df[numeric_columns].describe(),
                            use_container_width=True
                        )

                    st.write("전체 컬럼 통계")
                    st.dataframe(
                        selected_df.describe(include="all"),
                        use_container_width=True
                    )

                # =========================
                # TAB 3. 결측치 분석
                # =========================
                with tab3:
                    st.subheader("선택한 항목의 결측치 분석")

                    missing_df = pd.DataFrame({
                        "컬럼명": selected_df.columns,
                        "결측치 개수": selected_df.isnull().sum().values,
                        "결측치 비율(%)": (selected_df.isnull().mean().values * 100).round(2)
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
                    st.subheader("선택한 항목의 범주형 분석")

                    categorical_columns = selected_df.select_dtypes(include=["object"]).columns.tolist()

                    if len(categorical_columns) == 0:
                        st.warning("선택한 항목 중 범주형 컬럼이 없습니다.")
                    else:
                        selected_category_col = st.selectbox(
                            "분석할 범주형 컬럼을 선택하세요",
                            options=categorical_columns
                        )

                        value_count_df = selected_df[selected_category_col].value_counts().reset_index()
                        value_count_df.columns = [selected_category_col, "개수"]

                        st.write(f"{selected_category_col} 값 분포")
                        st.dataframe(value_count_df, use_container_width=True)

                        st.bar_chart(
                            value_count_df.set_index(selected_category_col)["개수"]
                        )

                # =========================
                # TAB 5. 키워드 검색
                # =========================
                with tab5:
                    st.subheader("선택한 항목 기준 키워드 검색")

                    with st.form("search_form"):
                        keyword = st.text_input("검색할 키워드를 입력하세요")
                        submitted = st.form_submit_button("검색")

                    if submitted:
                        if keyword.strip() == "":
                            st.warning("검색어를 입력해주세요.")
                        else:
                            # 선택한 컬럼들 안에서만 검색
                            search_result = selected_df[
                                selected_df.astype(str).apply(
                                    lambda row: row.str.contains(keyword, case=False, na=False).any(),
                                    axis=1
                                )
                            ]

                            st.write(f"검색 결과: {len(search_result):,}건")
                            st.dataframe(search_result, use_container_width=True)

    except EmptyDataError:
        st.error("CSV 파일에서 컬럼을 읽지 못했습니다. 파일이 비어 있거나 CSV 형식이 아닐 수 있습니다.")

    except UnicodeDecodeError:
        try:
            file_bytes = uploaded.getvalue()
            user_df = pd.read_csv(io.BytesIO(file_bytes), encoding="cp949")
            st.success("cp949 인코딩으로 CSV 파일을 읽었습니다.")
            st.dataframe(user_df.head(), use_container_width=True)

        except Exception as e:
            st.error("CSV 인코딩 문제로 파일을 읽지 못했습니다.")
            st.exception(e)

    except Exception as e:
        st.error("CSV 파일을 읽는 중 오류가 발생했습니다.")
        st.exception(e)

else:
    st.info("CSV 파일을 업로드해주세요.")

pg.run()