# page3.py
import streamlit as st

from dashboard_utils import read_csv_from_upload, render_analysis_dashboard, render_generic_insight

st.title("새 데이터 분석")

uploaded = st.file_uploader("분석할 CSV 파일을 업로드하세요", type=["csv"])

if uploaded is not None:
    try:
        file_bytes = uploaded.getvalue()

        uploaded_df = read_csv_from_upload(file_bytes)

        render_analysis_dashboard(
            uploaded_df,
            title="새 데이터 분석"
        )

        render_generic_insight(uploaded_df)

    except Exception as e:
        st.error("업로드한 CSV 파일을 읽는 중 오류가 발생했습니다.")
        st.exception(e)

else:
    st.info("CSV 파일을 업로드하면 분석 대시보드가 표시됩니다.")